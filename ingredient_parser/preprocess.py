#!/usr/bin/env python3

import re
from fractions import Fraction
from html import unescape
from typing import Any, Dict, List

from nltk.tag import pos_tag
from nltk.tokenize import RegexpTokenizer

# Regex pattern for fraction parts.
# Matches 0+ numbers followed by 0+ white space characters followed by a number then a forward slash then another number
FRACTION_PARTS_PATTERN = re.compile(r"(\d*\s*\d/\d+)")

# Regex pattern for checking if token starts with a capital letter
CAPITALISED_PATTERN = re.compile(r"^[A-Z]")

# Regex pattern for finding quantity and units without space between them.
# Assumes the quantity is always a number and the units always a letter
QUANTITY_UNITS_PATTERN = re.compile(r"(\d)([a-zA-Z])")

# Regex pattern for matching a numeric range e.g. 1-2, 2-3
RANGE_PATTERN = re.compile(r"\d+\s*\-\d+")

# Regex pattern for matching a range in string format e.g. 1 to 2, 8.5 to 12, 4 or 5
# Assumes fake fractions and unicode fraction have already been replaced
# Allows the range to include a hyphen after each number, which are captured in separate groups
# Captures the two number in the range in separate capture groups
STRING_RANGE_PATTERN = re.compile(r"([\d\.]+)(-)?\s+(to|or)\s+([\d\.]+)(-)?")

# Predefine tokenizer
# The regex pattern matches the tokens: any word character (including '.' and '-' and ' ) or ( or ) or , or "
REGEXP_TOKENIZER = RegexpTokenizer(r"[\w\.\-\']+|\(|\)|,|\"", gaps=False)

# Plural and singular units
UNITS = {
    "tablespoons": "tablespoon",
    "tbsps": "tbsp",
    "teaspoons": "teaspoon",
    "tsps": "tsp",
    "grams": "gram",
    "g": "g",
    "kilograms": "kilogram",
    "kg": "kg",
    "litres": "litre",
    "liters": "liter",
    "milliliters": "milliliter",
    "ml": "ml",
    "pounds": "pound",
    "lbs": "lb",
    "ounces": "ounce",
    "cups": "cup",
    "cloves": "clove",
    "sprigs": "sprig",
    "pinches": "pinch",
    "bunches": "bunch",
    "handfuls": "handful",
    "slices": "slice",
    "grams": "gram",
    "heads": "head",
    "quarts": "quart",
    "stalks": "stalk",
    "pints": "pint",
    "pieces": "piece",
    "sticks": "stick",
    "dashes": "dash",
    "fillets": "fillet",
    "cans": "can",
    "ears": "ear",
    "packages": "package",
    "strips": "strip",
    "bulbs": "bulb",
    "bottles": "bottle",
    "boxes": "box",
    "sheet": "sheets",
    "scoops": "scoop",
    "chops": "chop",
    "leaves": "leaf",
    "glasses": "glass",
}

# The spaces around the text are required to ensure we only replace the word when it represents a number
# and not when the word appear inside a large word.
# We don't want boneless to become b1less
STRING_NUMBERS = {
    " half ": " 0.5 ",
    " one ": " 1 ",
    " two ": " 2 ",
    " three ": " 3 ",
    " four ": " 4 ",
    " five ": " 5 ",
    " six ": " 6 ",
    " seven ": " 7 ",
    " eight ": " 8 ",
    " nine ": " 9 ",
}


class PreProcessor:

    """Recipe ingredient sentence PreProcessor class.

    Performs the necessary preprocessing on a sentence to generate the features required for the ingredient parser model.

    Each input sentence goes through a cleaning process to tidy up the input into a standardised form.
    The cleaning steps are as follows:

    1. | Replace numbers given as words with the numeric equivalent.
       | e.g. one >> 1
    2. | Replace fractions given in html mark up with the unicide representation.
       | e.g. &frac12; >> ½
    3. | Replace unicode fractions with the equivalent decimal form. Decimals are rounded to 3 a maximum of decimal places.
       | e.g. ½ >> 0.5
    4. | Replace "fake" fractions represented by 1/2, 2/3 etc. with the equivalent decimal form
       | e.g. 1/2 >> 0.5
    5. | A space is enforced between quantities and units
    6. | Numeric ranges indicated in words using "to" or "or" are replaced with a standard numeric form
       | e.g. 1 or 2 >> 1-2; 10 to 12 >> 10-12
    7. | Units are made singular. This step uses a predefined list of plural units and their singular form.

    Following the cleaning of the input sentence, it is tokenized into a list of tokens.
    Each token is one of the following:

    * A word, including . - and ' characters
    * Opening or closing parentheses
    * Comma
    * Speech marks, "

    The features for each token are computed on demand using the ``sentence_features`` method, which returns a list of dictionaries.
    Each dictionary is the feature set for each token.
    The following features are generated:

    word
        The current token.

    pos
        The part of speech tag for the current token.

    prev_pos+pos
        The combined part of speech tag for the previous token and the current token.

    pos+next_pos
        The combined part of speech tag for the current token and the next token.

    prev_word
        The previous token.

    prev_word2
        The token before the previous token.

    next_word
        The next token.

    next_word2
        The token following the next token.

    is_capitalised
        True if the token starts with a capital letter.

    is_numeric
        True if the token is numeric, including ranges.

    is_unit
        True if the token is a unit.

    The sentence features can then be passed to the CRF model which will generate the parsed output.

    Parameters
    ----------
    sentence : str
        Input ingredient sentence.
    defer_pos_tagging : bool
        Defer part of speech tagging until feature generation.
        Part of speech tagging is an expensive operation and it's not always needed when using this class.

    Attributes
    ----------
    input: str
        Input ingredient sentence.
    sentence: str
        Input ingredient sentence, cleaned to standardised form.
    tokenized_sentence : List[str]
        Tokenised ingredient sentence.
    pos_tags : List[str]
        Part of speech tag for each token in the tokenized sentence.
    """

    def __init__(self, sentence: str, defer_pos_tagging=False):
        """Initialisation

        Parameters
        ----------
        sentence : str
            Ingredient sentence
        defer_pos_tagging : bool, optional
            Defer part of speech tagging until feature generation
        """
        self.input = sentence
        self.sentence = self._clean(sentence)
        self.tokenized_sentence = REGEXP_TOKENIZER.tokenize(self.sentence)
        self.defer_pos_tagging = defer_pos_tagging
        if not defer_pos_tagging:
            self.pos_tags = self._tag_partofspeech(self.tokenized_sentence)
        else:
            self.pos_tags = []

    def __repr__(self) -> str:
        """__repr__ method

        Returns
        -------
        str
            String representation of initialised object
        """
        return f'PreProcessor("{self.input}")'

    def __str__(self) -> str:
        """__str__ method

        Returns
        -------
        str
            Human readble string representation of object
        """
        _str = [
            "Pre-processed recipe ingedient sentence",
            f"\t    Input: {self.input}",
            f"\t  Cleaned: {self.sentence}",
            f"\tTokenized: {self.tokenized_sentence}",
        ]
        return "\n".join(_str)

    def _clean(self, sentence: str) -> str:
        """Clean sentence prior to feature extraction

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Clean ingredient sentence
        """
        # List of funtions to apply to sentence
        # Note that the order matters
        funcs = [
            self._replace_string_numbers,
            self._replace_html_fractions,
            self._replace_unicode_fractions,
            self._replace_fake_fractions,
            self._split_quantity_and_units,
            self._replace_string_range,
            self._singlarise_unit,
        ]

        for func in funcs:
            sentence = func(sentence)

        return sentence

    def _replace_string_numbers(self, sentence: str) -> str:
        """Replace string numbers (e.g. one, two) with numeric values (e.g. 1, 2)

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with string numbers replace with numeric values
        """
        for s, n in STRING_NUMBERS.items():
            # This is case insensitive so it replace e.g. "one" and "One"
            sentence = re.sub(s, n, sentence, flags=re.IGNORECASE)

        return sentence

    def _replace_html_fractions(self, sentence: str) -> str:
        """Replace html fractions e.g. &frac12; with unicode equivalents

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with html fractions replaced
        """
        return unescape(sentence)

    def _replace_fake_fractions(self, sentence: str) -> str:
        """Attempt to parse fractions from sentence and convert to decimal
        This looks for fractions with the format of 1/2, 1/4, 1 1/2 etc.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with fractions replaced with decimals
        """
        matches = FRACTION_PARTS_PATTERN.findall(sentence)
        # This is a bit of a hack.
        # If a fraction appears multiple times but in different forms e.g. 1/2 and 1 1/2, then
        # we need to replace the longest one first, otherwise both instance of 1/2 would be replaced
        # at the same time which would mean that the instance of 1 1/2 would end up as 1 0.5 instead of 1.5
        matches.sort(key=len, reverse=True)

        if matches is None:
            return sentence

        for match in matches:
            # The regex pattern will capture the space before a fraction if the fraction doesn't have a whole number in front of it.
            # Therefore, if the match starts with a space, remove it.
            if match.startswith(" "):
                match = match[1:]

            split = match.split()
            summed = float(sum(Fraction(s) for s in split))
            rounded = round(summed, 3)
            sentence = sentence.replace(match, f"{rounded:g}")

        return sentence

    def _replace_unicode_fractions(self, sentence: str) -> str:
        """Replace unicode fractions with a 'fake' ascii equivalent.
        The ascii equivalent is used because the replace_fake_fractions function can deal with spaces between an integer and the fraction.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with unicode fractions replaced
        """
        fractions = {
            "\x215b": "1/8",
            "\x215c": "3/8",
            "\x215d": "5/8",
            "\x215e": "7/8",
            "\x2159": "1/6",
            "\x215a": "5/6",
            "\x2155": "1/5",
            "\x2156": "2/5",
            "\x2157": "3/5",
            "\x2158": "4/5",
            "\xbc": "1/4",
            "\xbe": "3/4",
            "\x2153": "1/3",
            "\x2154": "2/3",
            "\xbd": "1/2",
        }
        for f_unicode, f_ascii in fractions.items():
            # Insert space before ascii fraction to avoid merging into a single token
            sentence = sentence.replace(f_unicode, f" {f_ascii}")

        return sentence

    def _split_quantity_and_units(self, sentence: str) -> str:
        """Insert space between quantity and unit
        This currently finds any instances of a number followed directly by a letter with no space inbetween.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with spaces inserted between quantity and units
        """
        return QUANTITY_UNITS_PATTERN.sub(r"\1 \2", sentence)

    def _replace_string_range(self, sentence: str) -> str:
        """Replace range in the form "<num> to <num" with standardised range "<num>-<num>"
        For example:
        1 to 2 -> 1-2
        8.5 to 12.5 -> 8.5-12.5
        16- to 9-

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with string ranges replaced with standardised range
        """
        return STRING_RANGE_PATTERN.sub(r"\1-\4 ", sentence)

    def _singlarise_unit(self, sentence: str) -> str:
        """Singularise units
        e.g. cups -> cup, tablespoons -> tablespoon

        Parameters
        ----------
        sentence : str
            Ingredient sentnece

        Returns
        -------
        str
            Ingredient sentence with units singularised
        """
        for plural, singular in UNITS.items():
            sentence = sentence.replace(plural, singular)

        return sentence

    def _tag_partofspeech(self, tokens: List[str]) -> List[str]:
        """Tag tokens with part of speech using universal tagset
        This function manually fixes tags that are incorrect in the context of:
        1. Change tags of numeric ranges to CD
        2. Change tag of "ground" from NN to VBD e.g. ground almonds


        Parameters
        ----------
        tokens : List[str]
            Tokenized ingredient sentence

        Returns
        -------
        List[str]
            List of part of speech tags
        """
        tags = []
        for token, tag in pos_tag(tokens):
            if RANGE_PATTERN.match(token):
                tag = "CD"
            if token in ["ground"]:
                tag = "VBD"
            tags.append(tag)
        return tags

    def _get_length(self, tokens: List[str]) -> int:
        """Get the smallest bucket the length of the tokens list fits into.

        Parameters
        ----------
        tokens : List[str]
            List of tokens in sentence

        Returns
        -------
        int
            Smallest bucket true length fits in

        """
        length = len(tokens)
        for n in [4, 8, 12, 16, 20, 26, 32, 38, 44, 50, 70]:
            if length < n:
                return n

        return 0

    def _is_unit(self, token: str) -> bool:
        """Return True if token is a unit

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True if token is a unit, else False
        """
        return token in UNITS.values()

    def _is_numeric(self, token: str) -> bool:
        """Return True if token is numeric

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True if token is numeric, else False
        """
        if "-" in token:
            parts = token.split("-")
            return all([self._is_numeric(part) for part in parts])

        try:
            float(token)
            return True
        except ValueError:
            return False

    def _follows_comma(self, token: str) -> bool:
        """Return True if token follows a comma (by any amount) in sentence

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True if token follows comma, else False
        """
        try:
            comma_index = self.tokenized_sentence.index(",")
            token_index = self.tokenized_sentence.index(token)
            if comma_index < token_index:
                return True
            else:
                return False
        except ValueError:
            return False

    def _is_capitalised(self, token: str) -> bool:
        """Return True is token starts with a capital letter

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True is token starts with a capital letter
        """
        return CAPITALISED_PATTERN.match(token) is not None

    def _is_inside_parentheses(self, token: str) -> bool:
        """Return True is token is inside parentheses within the sentence or is a parenthesis

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True is token is inside parantheses or is parenthesis
        """
        # If token not sentence return False
        # This protects the final return from returning True is there are brackets but no token in the sentence
        if token not in self.tokenized_sentence:
            return False

        # If it's "(" or ")", return True
        if token in ["(", ")"]:
            return True

        token_index = self.tokenized_sentence.index(token)
        return (
            "(" in self.tokenized_sentence[:token_index]
            and ")" in self.tokenized_sentence[token_index + 1 :]
        )

    def _token_features(self, index: int) -> Dict[str, Any]:
        """Return the features for each token in the sentence

        Parameters
        ----------
        index : int
            Index of token to get features for.

        Returns
        -------
        Dict[str, Any]
            Dictionary of features for token at index
        """
        token = self.tokenized_sentence[index]
        return {
            "word": token.lower(),
            "pos": self.pos_tags[index],
            "prev_pos+pos": self.pos_tags[index]
            if index == 0
            else self.pos_tags[index - 1] + self.pos_tags[index],
            "pos+next_pos": self.pos_tags[index]
            if index == len(self.tokenized_sentence) - 1
            else self.pos_tags[index] + self.pos_tags[index + 1],
            "prev_word": "" if index == 0 else self.tokenized_sentence[index - 1],
            "prev_word2": "" if index < 2 else self.tokenized_sentence[index - 2],
            "next_word": ""
            if index == len(self.tokenized_sentence) - 1
            else self.tokenized_sentence[index + 1],
            "next_word2": ""
            if index >= len(self.tokenized_sentence) - 2
            else self.tokenized_sentence[index + 2],
            "is_capitalised": self._is_capitalised(token),
            "is_numeric": self._is_numeric(token),
            "is_unit": self._is_unit(token),
        }

    def sentence_features(self) -> List[Dict[str, Any]]:
        """Return features for all tokens in sentence

        Parameters
        ----------
        sentence : str
            Description

        Returns
        -------
        List[Dict[str, Any]]
            Description
        """
        if self.defer_pos_tagging:
            # If part of speech tagging was deferred, do it now
            self.pos_tags = self._tag_partofspeech(self.tokenized_sentence)

        features = []
        for idx, _ in enumerate(self.tokenized_sentence):
            features.append(self._token_features(idx))

        return features

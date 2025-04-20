#!/usr/bin/env python3

import re
import string
import unicodedata
from dataclasses import dataclass
from html import unescape

from nltk import pos_tag

from ._constants import (
    AMBIGUOUS_UNITS,
    FLATTENED_UNITS_LIST,
    STRING_NUMBERS,
    UNICODE_FRACTIONS,
    UNITS,
)
from ._regex import (
    CAPITALISED_PATTERN,
    DIGIT_PATTERN,
    DUPE_UNIT_RANGES_PATTERN,
    EXPANDED_RANGE,
    FRACTION_PARTS_PATTERN,
    FRACTION_TOKEN_PATTERN,
    LOWERCASE_PATTERN,
    QUANTITY_UNITS_PATTERN,
    QUANTITY_X_PATTERN,
    STRING_QUANTITY_HYPHEN_PATTERN,
    UNITS_HYPHEN_QUANTITY_PATTERN,
    UNITS_QUANTITY_PATTERN,
    UPPERCASE_PATTERN,
)
from ._utils import (
    combine_quantities_split_by_and,
    is_unit_synonym,
    replace_string_range,
    stem,
    tokenize,
)

CONSECUTIVE_SPACES = re.compile(r"\s+")


@dataclass
class TokenFeatures:
    stem: str
    shape: str
    is_capitalised: bool
    is_unit: bool
    is_punc: bool
    is_ambiguous_unit: bool


@dataclass
class Token:
    index: int
    text: str
    feat_text: str
    pos_tag: str
    features: TokenFeatures


class PreProcessor:
    """Recipe ingredient sentence PreProcessor class.

    Performs the necessary preprocessing on a sentence to generate the features
    required for the ingredient parser model.

    Each input sentence goes through a cleaning process to tidy up the input into a
    standardised form.

    Notes
    -----
    The cleaning steps are as follows

    1. | Replace all en-dashes and em-dashes with hyphens.
    2. | Replace numbers given as words with the numeric equivalent.
       | e.g. one >> 1
    3. | Replace fractions given in html markup with the unicode representation.
       | e.g. &frac12; >> ½
    4. | Replace unicode fractions with the equivalent decimal form. Decimals are
       | rounded to a maximum of 3 decimal places.
       | e.g. ½ >> 0.5
    5. | Identify fractions represented by 1/2, 2/3 etc. by replaceing the slash with $
       | and the prepending # in front of the fraction e.g. #1$2
       | e.g. 1/2 >> 0.5
    6. | A space is enforced between quantities and units
    7. | Remove trailing periods from units
       | e.g. tsp. >> tsp
    8. | Numeric ranges indicated in words using "to" or "or" are replaced with a
       | standard numeric form
       | e.g. 1 or 2 >> 1-2; 10 to 12 >> 10-12
    9. | Units are made singular. This step uses a predefined list of plural units and
       | their singular form.

    Following the cleaning of the input sentence, it is tokenized into a list of tokens.

    Each token is one of the following

    * A word, including most punctuation marks
    * Opening or closing parentheses, braces, brackets; comma; speech marks

    The features for each token are computed on demand using the ``sentence_features``
    method, which returns a list of dictionaries.
    Each dictionary is the feature set for each token.

    The sentence features can then be passed to the CRF model which will generate the
    parsed output.

    Parameters
    ----------
    input_sentence : str
        Input ingredient sentence.
    show_debug_output : bool, optional
        If True, print out each stage of the sentence normalisation

    Attributes
    ----------
    show_debug_output : bool
        If True, print out each stage of the sentence normalisation
    input : str
        Input ingredient sentence.
    sentence : str
        Input ingredient sentence, cleaned to standardised form.
    singularised_indices : list[int]
        Indices of tokens in tokenized sentence that have been converted from plural
        to singular
    tokenized_sentence : list[Token]
        Tokenised ingredient sentence.
    """

    def __init__(
        self,
        input_sentence: str,
        show_debug_output: bool = False,
    ):
        """Initialise.

        Parameters
        ----------
        input_sentence : str
            Input ingredient sentence
        show_debug_output : bool, optional
            If True, print out each stage of the sentence normalisation

        """
        self.show_debug_output = show_debug_output
        self.input: str = input_sentence
        self.sentence: str = self._normalise(input_sentence)

        self.singularised_indices = []
        self.tokenized_sentence = self._calculate_tokens(self.sentence)

    def __repr__(self) -> str:
        """__repr__ method.

        Returns
        -------
        str
            String representation of initialised object
        """
        return f'PreProcessor("{self.input}")'

    def __str__(self) -> str:
        """__str__ method.

        Returns
        -------
        str
            Human readable string representation of object
        """
        _str = [
            "Pre-processed recipe ingredient sentence",
            f"\t  Input: {self.input}",
            f"\tCleaned: {self.sentence}",
            f"\t Tokens: {[t.text for t in self.tokenized_sentence]}",
        ]
        return "\n".join(_str)

    def _normalise(self, sentence: str) -> str:
        """Normalise sentence prior to feature extraction.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Normalised ingredient sentence
        """
        # List of functions to apply to sentence
        # Note that the order matters
        funcs = [
            self._replace_en_em_dash,
            self._replace_html_fractions,
            self._replace_unicode_fractions,
            combine_quantities_split_by_and,
            self._identify_fractions,
            self._split_quantity_and_units,
            self._remove_unit_trailing_period,
            replace_string_range,
            self._replace_dupe_units_ranges,
            self._merge_quantity_x,
            self._collapse_ranges,
        ]

        for func in funcs:
            sentence = func(sentence)

            if self.show_debug_output:
                print(f"{func.__name__}: {sentence}")

        return sentence.strip()

    def _replace_en_em_dash(self, sentence: str) -> str:
        """Replace en-dashes and em-dashes with hyphens.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with en and em dashes replaced with hyphens

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_en_em_dash("2 cups flour – white or self-raising")
        "2 cups flour - white or self-raising"

        >>> p = PreProcessor("")
        >>> p._replace_en_em_dash("3–4 sirloin steaks")
        "3-4 sirloin steaks"
        """
        return sentence.replace("–", "-").replace("—", " - ")

    def _replace_html_fractions(self, sentence: str) -> str:
        """Replace html fractions e.g. &frac12; with unicode equivalents.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with html fractions replaced

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_html_fractions("1&frac34; cups tomato ketchup")
        "1¾ cups tomato ketchup"
        """
        return unescape(sentence)

    def _identify_fractions(self, sentence: str) -> str:
        """Identify fractions and modify them so that they are do not get split by
        the tokenizer.

        This looks for fractions with the format of 1/2, 1/4, 1 1/2 etc. and replaces
        the forward slash with $ and inserts a # before the fractional part.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with fractions replaced with decimals

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._identify_fractions("1/2 cup icing sugar")
        "#1$2 cup icing sugar"

        >>> p = PreProcessor("")
        >>> p._identify_fractions("2 3/4 pound chickpeas")
        "2#3$4 pound chickpeas"

        >>> p = PreProcessor("")
        >>> p._identify_fractions("1 1⁄2 cups fresh corn")
        "1#1$2 cups fresh corn"
        """
        # Replace unicode FRACTION SLASH (U+2044) with forward slash
        sentence = sentence.replace("\u2044", "/")

        matches = FRACTION_PARTS_PATTERN.findall(sentence)

        if not matches:
            return sentence

        # This is a bit of a hack.
        # If a fraction appears multiple times but in different forms e.g. 1/2 and
        # 1 1/2, then
        # we need to replace the longest one first, otherwise both instance of 1/2
        # would be replaced at the same time which would mean that the instance of
        # 1 1/2 would end up as 1 0.5 instead of 1.5
        # Before we sort, we need to strip any space from the start and end.
        matches = [match.strip() for match in matches]
        matches.sort(key=len, reverse=True)

        for match in matches:
            # Replace / with $
            replacement = match.replace("/", "$")
            # If there's a space in the match, replace with #, otherwise prepend #
            if " " in replacement:
                replacement = CONSECUTIVE_SPACES.sub("#", replacement)
            else:
                replacement = "#" + replacement
            sentence = sentence.replace(match, replacement)

        return sentence

    def _replace_unicode_fractions(self, sentence: str) -> str:
        """Replace unicode fractions with a 'fake' ascii equivalent.

        The ascii equivalent is used because the replace_fake_fractions function can
        deal with spaces between an integer and the fraction.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with unicode fractions replaced

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_unicode_fractions("½ cup icing sugar")
        " 1/2 cup icing sugar"

        >>> p = PreProcessor("")
        >>> p._replace_unicode_fractions("3⅓ cups warm water")
        "3 1/3 cups warm water"

        >>> p = PreProcessor("")
        >>> p._replace_unicode_fractions("¼-½ teaspoon")
        "1/4-1/2 teaspoon"
        """
        for f_unicode, f_ascii in UNICODE_FRACTIONS.items():
            sentence = sentence.replace(f_unicode, f_ascii)

        return sentence

    def _split_quantity_and_units(self, sentence: str) -> str:
        """Insert space between quantity and unit.

        This currently finds any instances of a number followed directly by a letter
        with no space or a hyphen in between. It also finds any letters followed
        directly by a number with no space in between.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with spaces inserted between quantity and units

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._split_quantity_and_units("100g green beans")
        "100 g green beans"

        >>> p = PreProcessor("")
        >>> p._split_quantity_and_units("2-pound red peppers, sliced")
        "2 pound red peppers, sliced"

        >>> p = PreProcessor("")
        >>> p._split_quantity_and_units("2lb1oz cherry tomatoes")
        "2 lb 1 oz cherry tomatoes"

        >>> p = PreProcessor("")
        >>> p._split_quantity_and_units("2lb-1oz cherry tomatoes")
        "2 lb - 1 oz cherry tomatoes"
        """
        sentence = QUANTITY_UNITS_PATTERN.sub(r"\1 \2", sentence)
        sentence = UNITS_QUANTITY_PATTERN.sub(r"\1 \2", sentence)
        sentence = UNITS_HYPHEN_QUANTITY_PATTERN.sub(r"\1 - \2", sentence)
        return STRING_QUANTITY_HYPHEN_PATTERN.sub(r"\1 \2", sentence)

    def _remove_unit_trailing_period(self, sentence: str) -> str:
        """Remove trailing periods from units e.g. tsp. -> tsp.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with trailing periods from units removed

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._remove_unit_trailing_period("1 tsp. garlic powder")
        "1 tsp garlic powder"

        >>> p = PreProcessor("")
        >>> p._remove_unit_trailing_period("5 oz. chopped tomatoes")
        "5 oz chopped tomatoes"
        """
        units = [
            "tsp.",
            "tsps.",
            "tbsp.",
            "tbsps.",
            "tbs.",
            "tb.",
            "lb.",
            "lbs.",
            "oz.",
        ]
        units.extend([u.capitalize() for u in units])
        for unit in units:
            unit_no_period = unit.replace(".", "")
            sentence = sentence.replace(unit, unit_no_period)

        return sentence

    def _replace_dupe_units_ranges(self, sentence: str) -> str:
        """Replace ranges where the unit appears twice with standard range then unit.

        This assumes that the _split_quantity_and_units has already been run on
        the sentence.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with ranges containing unit twice replaced with
            standardised range

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_dupe_units_ranges("227 g - 283.5 g/8-10 oz duck breast")
        "227-283.5 g/8-10 oz duck breast"

        >>> p = PreProcessor("")
        >>> p._replace_dupe_units_ranges("400-500 g/14 oz - 17 oz rhubarb")
        "400-500 g/14-17 oz rhubarb"

        >>> p = PreProcessor("")
        >>> p._replace_dupe_units_ranges("0.5 c to 1 cup shelled raw pistachios")
        "0.5-1 c shell raw pistachios"
        """
        matches = DUPE_UNIT_RANGES_PATTERN.findall(sentence)

        if not matches:
            return sentence

        for full_match, quantity1, unit1, quantity2, unit2 in matches:
            # We are only interested if the both captured units are the same
            if unit1 != unit2 and not is_unit_synonym(unit1, unit2):
                continue

            # If capture unit not in units list, abort
            if unit1 not in FLATTENED_UNITS_LIST:
                continue

            sentence = sentence.replace(full_match, f"{quantity1}-{quantity2} {unit1}")

        return sentence

    def _merge_quantity_x(self, sentence: str) -> str:
        """Merge any quantity followed by "x" into a single token.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with single "x" merged into preceding number

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_dupe_units_ranges("8 x 450 g/1 lb live lobsters")
        "8x 450g/1lb live lobsters"

        >>> p = PreProcessor("")
        >>> p._replace_dupe_units_ranges("4 x 100 g wild salmon fillet")
        "4x 100 g wild salmon fillet"
        """
        return QUANTITY_X_PATTERN.sub(r"\1x ", sentence)

    def _collapse_ranges(self, sentence: str) -> str:
        """Collapse any whites pace found in a range so the range has the standard form.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with white space removed from ranges

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._collapse_ranges("8 - 10 g ground pepper")
        "8-10 g ground pepper"

        >>> p = PreProcessor("")
        >>> p._collapse_ranges("0.25  -0.5 tsp salt")
        "0.25-0.5 tsp salt"
        """
        return EXPANDED_RANGE.sub(r"\1-\2", sentence)

    def _calculate_tokens(self, sentence: str) -> list[Token]:
        """Tokenize sentence and calculate attributes for each token.

        The attributes calculated for each token are attributes that properties of the
        individual token, such as things like is_numeric, is_unit.
        It does not include attributes that depend on the token context.

        Parameters
        ----------
        sentence : str
            Sentence to tokenize.

        Returns
        -------
        list[Token]
            List of Tokens for sentence.
        """

        # Singularise units
        text_tokens = []
        for i, text in enumerate(tokenize(sentence)):
            singular = UNITS.get(text, None)
            if singular is not None:
                text_tokens.append(singular)
                self.singularised_indices.append(i)
            else:
                text_tokens.append(text)

        tokens = []
        for i, (text, pos) in enumerate(pos_tag(text_tokens)):
            # Convert tokens:
            # * Singularise units, keeping track of indices of singularised tokens
            # * Replace numeric token with "!num"
            if self._is_numeric(text):
                feat_text = "!num"
            else:
                feat_text = text

            # Get part of speech tag, with overrides for certain tokens
            if self._is_numeric(text):
                pos = "CD"
            elif text in ["c", "g"]:
                # Special cases for c (cup) and g (gram)
                pos = "NN"

            features = TokenFeatures(
                stem=stem(feat_text),
                shape=self._word_shape(feat_text),
                is_capitalised=self._is_capitalised(feat_text),
                is_unit=self._is_unit(feat_text),
                is_punc=self._is_punc(feat_text),
                is_ambiguous_unit=self._is_ambiguous_unit(feat_text),
            )

            tokens.append(
                Token(
                    index=i,
                    text=text,
                    feat_text=feat_text,
                    pos_tag=pos,
                    features=features,
                )
            )

        return tokens

    def _is_unit(self, token: str) -> bool:
        """Return True if token is a unit.

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True if token is a unit, else False

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._is_unit("cup")
        True

        >>> p = PreProcessor("")
        >>> p._is_unit("beef")
        False
        """
        return token.lower() in UNITS.values()

    def _is_punc(self, token: str) -> bool:
        """Return True if token is a punctuation mark.

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True if token is a punctuation mark, else False

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._is_unit("/")
        True

        >>> p = PreProcessor("")
        >>> p._is_unit("--")
        True

        >>> p = PreProcessor("")
        >>> p._is_unit("beef")
        False
        """
        return token in string.punctuation or token in {"--"}

    def _is_numeric(self, token: str) -> bool:
        """Return True if token is numeric.

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True if token is numeric, else False

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._is_numeric("1")
        True

        >>> p = PreProcessor("")
        >>> p._is_numeric("1-2")
        True

        >>> p = PreProcessor("")
        >>> p._is_numeric("dozen")
        True

        >>> p = PreProcessor("")
        >>> p._is_numeric("1x")
        True

        >>> p = PreProcessor("")
        >>> p._is_numeric("three")
        True

        >>> p = PreProcessor("")
        >>> p._is_numeric("beef")
        False
        """
        if token in ["00"]:
            # Special cases of digits that don't represent numbers
            return False

        if FRACTION_TOKEN_PATTERN.match(token):
            # Fraction tokens e.g. #1$4 or 1#2$3
            return True

        if token.lower() in STRING_NUMBERS.keys():
            return True

        if "-" in token:
            parts = token.split("-")
            return all([self._is_numeric(part) for part in parts])

        if token == "dozen":
            return True

        if token.endswith("x"):
            try:
                float(token[:-1])
                return True
            except ValueError:
                return False

        try:
            float(token)
            return True
        except ValueError:
            return False

    def _follows_comma(self, index: int) -> bool:
        """Return True if token at index follows a comma (by any amount) in sentence.

        If the token at index is a comma, treat it the same as any other token

        Parameters
        ----------
        index : int
            Index of token to check

        Returns
        -------
        bool
            True if token follows comma, else False
        """
        return "," in [t.feat_text for t in self.tokenized_sentence[:index]]

    def _follows_plus(self, index: int) -> bool:
        """Return True if token at index follow "plus" by any amount in sentence.

        If the token at the index is "plus", it doesn't count as following.

        Parameters
        ----------
        index : int
            Index of token to check

        Returns
        -------
        bool
            True if token follows "plus", else False
        """
        return "plus" in [t.feat_text for t in self.tokenized_sentence[:index]]

    def _is_capitalised(self, token: str) -> bool:
        """Return True if token starts with a capital letter.

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True if token starts with a capital letter, else False

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._is_capitalised("Chicken")
        True

        >>> p = PreProcessor("")
        >>> p._is_capitalised("chicken")
        False
        """
        return CAPITALISED_PATTERN.match(token) is not None

    def _is_inside_parentheses(self, index: int) -> bool:
        """Return True if token is inside parentheses or is a parenthesis.

        Parameters
        ----------
        index : int
            Index of token to check

        Returns
        -------
        bool
            True if index is inside parentheses or is parenthesis, else False
        """
        # If it's "(" or ")", return True
        if self.tokenized_sentence[index].feat_text in ["(", ")", "[", "]"]:
            return True

        open_parens, closed_parens = [], []
        for i, token in enumerate(self.tokenized_sentence):
            if token.feat_text == "(" or token.feat_text == "[":
                open_parens.append(i)
            elif token.feat_text == ")" or token.feat_text == "]":
                closed_parens.append(i)

        for start, end in zip(open_parens, closed_parens):
            if start < index < end:
                return True

        return False

    def _is_ambiguous_unit(self, token: str) -> bool:
        """Return True if token is in AMBIGUOUS_UNITS list.

        Parameters
        ----------
        token : str
            Token to check

        Returns
        -------
        bool
            True if token is in AMBIGUOUS_UNITS, else False

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._is_ambiguous_unit("cloves")
        True

        >>> p = PreProcessor("")
        >>> p._is_ambiguous_unit("wedge")
        True

        >>> p = PreProcessor("")
        >>> p._is_ambiguous_unit("leaf")
        True
        """
        return token in AMBIGUOUS_UNITS

    def _sentence_length_bucket(self) -> int:
        """Return the length of sentence, rounding down to the nearest bucket.

        The buckets are 2, 4, 8, 12, 16, 20, 32, 64

        Returns
        -------
        int
            Length bucket of sentence
        """
        length = len(self.tokenized_sentence)
        bucket = 1
        for length_bucket in [2, 4, 8, 12, 16, 20, 32, 64]:
            if length >= length_bucket:
                bucket = length_bucket

        return bucket

    def _word_shape(self, token: str) -> str:
        """Calculate the word shape for token.

        The word shape is a representation of the word where all letter characters are
        replaced with placeholders:
        - All lowercase characters are replaced with "x"
        - All uppercase characters are replaced with "X"
        - All digits are replaced with "d"
        - Punctuation is left unchanged

        Parameters
        ----------
        token : str
            Token to calculate word shape of.

        Returns
        -------
        str
            Word shape of token.
        """
        normalised = self._remove_accents(token)
        shape = LOWERCASE_PATTERN.sub("x", normalised)
        shape = UPPERCASE_PATTERN.sub("X", shape)
        shape = DIGIT_PATTERN.sub("d", shape)
        return shape

    def _remove_accents(self, token: str) -> str:
        """Remove accents from characters in token.

        Parameters
        ----------
        token : str
           Token to remove accents from.

        Returns
        -------
        str
           Token with accents removed.
        """
        return "".join(
            c
            for c in unicodedata.normalize("NFD", token)
            if unicodedata.category(c) != "Mn"
        )

    def _common_features(self, index: int, prefix: str) -> dict[str, str | bool]:
        """Return common features for token at given index.

        Parameters
        ----------
        index : int
            Index of token to return features for.
        prefix : str
            Feature label prefix.

        Returns
        -------
        dict[str, str | bool]
            Dict of features for token at given index.
        """
        token = self.tokenized_sentence[index]
        return {
            prefix + "is_capitalised": token.features.is_capitalised,
            prefix + "is_unit": token.features.is_unit,
            prefix + "is_punc": token.features.is_punc,
            prefix + "is_ambiguous": token.features.is_ambiguous_unit,
            prefix + "is_in_parens": self._is_inside_parentheses(index),
            prefix + "is_after_comma": self._follows_comma(index),
            prefix + "is_after_plus": self._follows_plus(index),
            prefix + "word_shape": token.features.shape,
        }

    def _ngram_features(self, token: str, prefix: str) -> dict[str, str]:
        """Return n-gram features for token in a dict.

        N = 3, 4, 5 are returned if possible, for prefixes and suffixes.
        An n-gram feature is only return if length of the token greater than N for that
        n-gram.

        If the token is "!num", don't return any n-gram features.

        Parameters
        ----------
        token : str
            Token to calculate n-gram features for.
        prefix : str
            Feature label prefix.

        Returns
        -------
        dict[str, str]
            Dict of n-gram features for token.
        """
        ngram_features = {}
        if token != "!num" and len(token) >= 4:
            ngram_features[prefix + "prefix_3"] = token[:3]
            ngram_features[prefix + "suffix_3"] = token[-3:]

        if token != "!num" and len(token) >= 5:
            ngram_features[prefix + "prefix_4"] = token[:4]
            ngram_features[prefix + "suffix_4"] = token[-4:]

        if token != "!num" and len(token) >= 6:
            ngram_features[prefix + "prefix_5"] = token[:5]
            ngram_features[prefix + "suffix_5"] = token[-5:]

        return ngram_features

    def _token_features(self, token: Token) -> dict[str, str | bool | int | float]:
        """Return the features for the token at the given index in the sentence.

        If the token at the given index appears in the corpus parameter, the token is
        used as a feature. Otherwise (i.e. for tokens that only appear once), the token
        stem is used as a feature.

        Parameters
        ----------
        token : Token
            Token to generate features for

        Returns
        -------
        dict[str, str | bool| int | float]
            Dictionary of features for token at index.
        """

        index = token.index
        features: dict[str, str | bool | int | float] = {}

        features["bias"] = ""
        features["sentence_length"] = self._sentence_length_bucket()

        # Features for current token
        features["pos"] = token.pos_tag
        features["stem"] = token.features.stem
        if token.feat_text != token.features.stem:
            features["token"] = token.feat_text

        features |= self._common_features(index, "")
        features |= self._ngram_features(token.feat_text, "")

        # Features for previous token
        if index > 0:
            prev_token = self.tokenized_sentence[index - 1]
            features["prev_stem"] = prev_token.features.stem
            features["prev_pos"] = "+".join(
                (
                    self.tokenized_sentence[index - 1].pos_tag,
                    self.tokenized_sentence[index].pos_tag,
                )
            )
            features |= self._common_features(index - 1, "prev_")

        # Features for previous previous token
        if index > 1:
            prev2_token = self.tokenized_sentence[index - 2]
            features["prev2_stem"] = prev2_token.features.stem
            features["prev2_pos"] = "+".join(
                (
                    self.tokenized_sentence[index - 2].pos_tag,
                    self.tokenized_sentence[index - 1].pos_tag,
                    self.tokenized_sentence[index].pos_tag,
                )
            )
            features |= self._common_features(index - 2, "prev2_")

        # Features for previous previous previous token
        if index > 2:
            prev3_token = self.tokenized_sentence[index - 3]
            features["prev3_stem"] = prev3_token.features.stem
            features["prev3_pos"] = "+".join(
                (
                    self.tokenized_sentence[index - 3].pos_tag,
                    self.tokenized_sentence[index - 2].pos_tag,
                    self.tokenized_sentence[index - 1].pos_tag,
                    self.tokenized_sentence[index].pos_tag,
                )
            )
            features |= self._common_features(index - 3, "prev3_")

        # Features for next token
        if index < len(self.tokenized_sentence) - 1:
            next_token = self.tokenized_sentence[index + 1]
            features["next_stem"] = next_token.features.stem
            features["next_pos"] = "+".join(
                (
                    self.tokenized_sentence[index].pos_tag,
                    self.tokenized_sentence[index + 1].pos_tag,
                )
            )
            features |= self._common_features(index + 1, "next_")

        # Features for next next token
        if index < len(self.tokenized_sentence) - 2:
            next2_token = self.tokenized_sentence[index + 2]
            features["next2_stem"] = next2_token.features.stem
            features["next2_pos"] = "+".join(
                (
                    self.tokenized_sentence[index].pos_tag,
                    self.tokenized_sentence[index + 1].pos_tag,
                    self.tokenized_sentence[index + 2].pos_tag,
                )
            )
            features |= self._common_features(index + 2, "next2_")

        # Features for next next next token
        if index < len(self.tokenized_sentence) - 3:
            next3_token = self.tokenized_sentence[index + 3]
            features["next3_stem"] = next3_token.features.stem
            features["next3_pos"] = "+".join(
                (
                    self.tokenized_sentence[index].pos_tag,
                    self.tokenized_sentence[index + 1].pos_tag,
                    self.tokenized_sentence[index + 2].pos_tag,
                    self.tokenized_sentence[index + 3].pos_tag,
                )
            )
            features |= self._common_features(index + 3, "next3_")

        return features

    def sentence_features(self) -> list[dict[str, str | bool | int | float]]:
        """Return features for all tokens in sentence.

        Returns
        -------
        list[dict[str, str | bool | int]]
            List of features for each token in sentence
        """
        return [self._token_features(token) for token in self.tokenized_sentence]

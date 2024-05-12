#!/usr/bin/env python3

import re
import string
from fractions import Fraction
from html import unescape

from nltk.tag import pos_tag

from ._constants import (
    AMBIGUOUS_UNITS,
    FLATTENED_UNITS_LIST,
    STRING_NUMBERS,
    STRING_NUMBERS_REGEXES,
    UNICODE_FRACTIONS,
    UNITS,
)
from ._regex import (
    CAPITALISED_PATTERN,
    DUPE_UNIT_RANGES_PATTERN,
    EXPANDED_RANGE,
    FRACTION_PARTS_PATTERN,
    FRACTION_SPLIT_AND_PATTERN,
    QUANTITY_UNITS_PATTERN,
    QUANTITY_X_PATTERN,
    STRING_RANGE_PATTERN,
    UNITS_HYPHEN_QUANTITY_PATTERN,
    UNITS_QUANTITY_PATTERN,
)
from ._utils import stem, tokenize


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
    5. | Replace "fake" fractions represented by 1/2, 2/3 etc. with the equivalent
       | decimal form
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
    defer_pos_tagging : bool
        Defer part of speech tagging until feature generation.
        Part of speech tagging is an expensive operation and it's not always needed when
        using this class.
    show_debug_output : bool, optional
        If True, print out each stage of the sentence normalisation

    Attributes
    ----------
    defer_pos_tagging : bool
        Defer part of speech tagging until feature generation
    show_debug_output : bool
        If True, print out each stage of the sentence normalisation
    input : str
        Input ingredient sentence.
    pos_tags : list[str]
        Part of speech tag for each token in the tokenized sentence.
    sentence : str
        Input ingredient sentence, cleaned to standardised form.
    singularised_indices : list[int]
        Indices of tokens in tokenised sentence that have been converted from plural
        to singular
    tokenized_sentence : list[str]
        Tokenised ingredient sentence.
    """

    def __init__(
        self,
        input_sentence: str,
        defer_pos_tagging: bool = False,
        show_debug_output: bool = False,
    ):
        """Initialise.

        Parameters
        ----------
        input_sentence : str
            Input ingredient sentence
        defer_pos_tagging : bool, optional
            Defer part of speech tagging until feature generation
        show_debug_output : bool, optional
            If True, print out each stage of the sentence normalisation

        """
        self.show_debug_output = show_debug_output
        self.input: str = input_sentence
        self.sentence: str = self._normalise(input_sentence)

        _tokenised_sentence = tokenize(self.sentence)
        (
            self.tokenized_sentence,
            self.singularised_indices,
        ) = self._singlarise_units(_tokenised_sentence)

        self.defer_pos_tagging: bool = defer_pos_tagging
        if not defer_pos_tagging:
            self.pos_tags: list[str] = self._tag_partofspeech(self.tokenized_sentence)
        else:
            self.pos_tags = []

        # Replace all numeric tokens with "!num" for calculating features
        self._feature_tokens = self._replace_numeric_tokens(self.tokenized_sentence)

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
            f"\t    Input: {self.input}",
            f"\t  Cleaned: {self.sentence}",
            f"\tTokenized: {self.tokenized_sentence}",
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
            self._replace_string_numbers,
            self._replace_html_fractions,
            self._replace_unicode_fractions,
            self._combine_quantities_split_by_and,
            self._replace_fake_fractions,
            self._split_quantity_and_units,
            self._remove_unit_trailing_period,
            self._replace_string_range,
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

    def _replace_string_numbers(self, sentence: str) -> str:
        """Replace string numbers (e.g. one, two) with numeric values (e.g. 1, 2).

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with string numbers replace with numeric values

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_string_numbers("three large onions")
        "3 large onions"

        >>> p = PreProcessor("")
        >>> p._replace_string_numbers("twelve bonbons")
        "12 bonbons"
        """
        # STRING_NUMBER_REGEXES is a dict where the values are a tuple of the compiled
        # regular expression for matching a string number e.g. 'one', 'two' and the
        # substitution numerical value for that string number.
        for regex, substitution in STRING_NUMBERS_REGEXES.values():
            # Find matches for current string number
            for match in regex.finditer(sentence):
                if self._valid_string_number_replacement(match, sentence):
                    sentence = regex.sub(rf"{substitution}", sentence)

        return sentence

    def _valid_string_number_replacement(self, match: re.Match, sentence: str) -> bool:
        """Check if string number replacement is valid for the given Match in sentence.

        Parameters
        ----------
        match : re.Match
            Match object for matching string number in sentence
        sentence : str
            Sentence

        Returns
        -------
        bool
        """
        # Check the character following the match, If it's not a hyphen, or we're at
        # the end of the sentence, the replacement is valid.
        next_char_idx = match.span()[-1]
        if next_char_idx >= len(sentence) or sentence[next_char_idx] != "-":
            return True

        # If the next character is a hyphen, if the hyphen is followed by
        # a unit or another string number, then also do the substitution.
        sub_sentence = sentence[next_char_idx + 1 :]
        units_and_numbers = FLATTENED_UNITS_LIST + list(STRING_NUMBERS.keys())
        for unit_or_num in units_and_numbers:
            # Add a space to end of unit_or_num to make sure we don't incorrectly
            # get a substring match e.g. matching "g" when unit_or_num is grain.
            if sub_sentence.startswith(unit_or_num + " "):
                return True

        return False

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

    def _replace_fake_fractions(self, sentence: str) -> str:
        """Attempt to parse fractions from sentence and convert to decimal.

        This looks for fractions with the format of 1/2, 1/4, 1 1/2 etc.

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
        >>> p._replace_fake_fractions("1/2 cup icing sugar")
        "0.5 cup icing sugar"

        >>> p = PreProcessor("")
        >>> p._replace_fake_fractions("2 3/4 pound chickpeas")
        "2.75 pound chickpeas"

        >>> p = PreProcessor("")
        >>> p._replace_fake_fractions("1 1⁄2 cups fresh corn")
        "1.5 cups fresh corn"
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
            split = match.split()
            summed = float(sum(Fraction(s) for s in split))
            rounded = round(summed, 3)
            sentence = sentence.replace(match, f"{rounded:g}")

        return sentence

    def _combine_quantities_split_by_and(self, sentence: str) -> str:
        """Combine fractional quantities split by 'and' into single value.

        Parameters
        ----------
        sentence : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with split fractions replaced with
            single decimal value.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._combine_quantities_split_by_and("1 and 1/2 tsp fine grain sea salt")
        "1.5 tsp fine grain sea salt"

        >>> p = PreProcessor("")
        >>> p._combine_quantities_split_by_and("1 and 1/4 cups dark chocolate morsels")
        "1.25 cups dark chocolate morsels"
        """
        matches = FRACTION_SPLIT_AND_PATTERN.findall(sentence)

        for match in matches:
            combined_quantity = float(Fraction(match[1]) + Fraction(match[2]))
            rounded = round(combined_quantity, 3)
            sentence = sentence.replace(match[0], f"{rounded:g}")

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
        return UNITS_HYPHEN_QUANTITY_PATTERN.sub(r"\1 - \2", sentence)

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

    def _replace_string_range(self, sentence: str) -> str:
        """Replace range in the form "<num> to <num" with range "<num>-<num>".

        For example
        -----------
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

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_string_range("1 to 2 mashed bananas")
        "1-2 mashed bananas"

        >>> p = PreProcessor("")
        >>> p._replace_string_range("5- or 6- large apples")
        "5-6- large apples"
        """
        return STRING_RANGE_PATTERN.sub(r"\1-\5", sentence)

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
        """
        matches = DUPE_UNIT_RANGES_PATTERN.findall(sentence)

        if not matches:
            return sentence

        for full_match, quantity1, unit1, quantity2, unit2 in matches:
            # We are only interested if the both captured units are the same
            if unit1 != unit2:
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
        """Collapse any whitespace found in a range so the range has the standard form.

        Parameters
        ----------
        sentence : str
            Ingedient sentence

        Returns
        -------
        str
            Ingredient sentence with whitespace removed from ranges

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

    def _singlarise_units(
        self, tokenised_sentence: list[str]
    ) -> tuple[list[str], list[int]]:
        """Singularise units in tokenised sentence.

        Returns the tokenized sentence with plural units made singular, and a list of
        indices of tokens in the tokenised sentence that have been singularised.

        Parameters
        ----------
        tokenised_sentence : list[str]
            Tokenised sentence

        Returns
        -------
        list[str]
            Tokenised sentence with units singularised
        list[int]
            List of indices of tokenised sentence that have been singularised
        """
        singularised_indices = []
        for idx, token in enumerate(tokenised_sentence):
            singular = UNITS.get(token, None)
            if singular is not None:
                tokenised_sentence[idx] = singular
                singularised_indices.append(idx)

        return (tokenised_sentence, singularised_indices)

    def _replace_numeric_tokens(self, tokens: list[str]) -> list[str]:
        """Replace numeric tokens with single representation "!num".

        This is so the model doesn't need to learn multiple different numeric tokens,
        just the one.

        Parameters
        ----------
        tokens : list[str]
            List of tokens

        Returns
        -------
        list[str]
            List of tokens with numeric tokens replaced with "!num"
        """
        replaced_tokens = []
        for token in tokens:
            if self._is_numeric(token):
                replaced_tokens.append("!num")
            else:
                replaced_tokens.append(token)

        return replaced_tokens

    def _tag_partofspeech(self, tokens: list[str]) -> list[str]:
        """Tag tokens with part of speech using universal tagset.

        Parameters
        ----------
        tokens : list[str]
            Tokenized ingredient sentence

        Returns
        -------
        list[str]
            List of part of speech tags
        """
        tags = []
        # If we don't make each token lower case, that POS tag maybe different in
        # ways that are unhelpful. For example, if a sentence starts with a unit.
        for token, tag in pos_tag([t.lower() for t in tokens]):
            if self._is_numeric(token):
                tag = "CD"
            tags.append(tag)
        return tags

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
        >>> p._is_unit("beef")
        False
        """
        return token in string.punctuation

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
        >>> p._is_numeric("beef")
        False
        """
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
        return "," in self.tokenized_sentence[:index]

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
        return "plus" in self.tokenized_sentence[:index]

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
        if self.tokenized_sentence[index] in ["(", ")", "[", "]"]:
            return True

        open_parens, closed_parens = [], []
        for i, token in enumerate(self.tokenized_sentence):
            if token == "(" or token == "[":
                open_parens.append(i)
            elif token == ")" or token == "]":
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

    def _token_features(self, index: int) -> dict[str, str | bool]:
        """Return the features for each token in the sentence.

        Parameters
        ----------
        index : int
            Index of token to get features for.

        Returns
        -------
        dict[str, str | bool]
            Dictionary of features for token at index
        """
        token = self._feature_tokens[index]
        features = {
            "bias": "",
            "stem": stem(token),
            "pos": self.pos_tags[index],
            "is_capitalised": self._is_capitalised(token),
            "is_unit": self._is_unit(token),
            "is_punc": self._is_punc(token),
            "is_ambiguous": self._is_ambiguous_unit(token),
            "is_in_parens": self._is_inside_parentheses(index),
            "is_after_comma": self._follows_comma(index),
            "is_after_plus": self._follows_plus(index),
            "is_short_phrase": len(self.tokenized_sentence) < 3,
        }

        if token != stem(token):
            features["token"] = token

        if index > 0:
            prev_token = self._feature_tokens[index - 1]
            features["prev_pos"] = "+".join(
                (self.pos_tags[index - 1], self.pos_tags[index])
            )
            features["prev_stem"] = stem(prev_token)
            features["prev_is_capitalised"] = self._is_capitalised(prev_token)
            features["prev_is_unit"] = self._is_unit(prev_token)
            features["prev_is_punc"] = self._is_punc(prev_token)
            features["prev_is_ambiguous"] = self._is_ambiguous_unit(prev_token)
            features["prev_is_in_parens"] = self._is_inside_parentheses(index - 1)
            features["prev_is_after_comma"] = self._follows_comma(index - 1)
            features["prev_is_after_plus"] = self._follows_plus(index - 1)

        if index > 1:
            prev_token2 = self._feature_tokens[index - 2]
            features["prev_pos2"] = "+".join(
                (
                    self.pos_tags[index - 2],
                    self.pos_tags[index - 1],
                    self.pos_tags[index],
                )
            )
            features["prev_stem2"] = stem(prev_token2)
            features["prev_is_capitalised2"] = self._is_capitalised(prev_token2)
            features["prev_is_unit2"] = self._is_unit(prev_token2)
            features["prev_is_punc2"] = self._is_punc(prev_token2)
            features["prev_is_ambiguous2"] = self._is_ambiguous_unit(prev_token2)
            features["prev_is_in_parens2"] = self._is_inside_parentheses(index - 2)
            features["prev_is_after_comma2"] = self._follows_comma(index - 2)
            features["prev_is_after_plus2"] = self._follows_plus(index - 2)

        if index < len(self._feature_tokens) - 1:
            next_token = self._feature_tokens[index + 1]
            features["next_pos"] = "+".join(
                (self.pos_tags[index], self.pos_tags[index + 1])
            )
            features["next_stem"] = stem(next_token)
            features["next_is_capitalised"] = self._is_capitalised(next_token)
            features["next_is_unit"] = self._is_unit(next_token)
            features["next_is_punc"] = self._is_punc(next_token)
            features["next_is_ambiguous"] = self._is_ambiguous_unit(next_token)
            features["next_is_in_parens"] = self._is_inside_parentheses(index + 1)
            features["next_is_after_comma"] = self._follows_comma(index + 1)
            features["next_is_after_plus"] = self._follows_plus(index + 1)

        if index < len(self._feature_tokens) - 2:
            next_token2 = self._feature_tokens[index + 2]
            features["next_pos2"] = "+".join(
                (
                    self.pos_tags[index + 2],
                    self.pos_tags[index + 1],
                    self.pos_tags[index],
                )
            )
            features["next_stem2"] = stem(next_token2)
            features["next_is_capitalised2"] = self._is_capitalised(next_token2)
            features["next_is_unit2"] = self._is_unit(next_token2)
            features["next_is_punc2"] = self._is_punc(next_token2)
            features["next_is_ambiguous2"] = self._is_ambiguous_unit(next_token2)
            features["next_is_in_parens2"] = self._is_inside_parentheses(index + 2)
            features["next_is_after_comma2"] = self._follows_comma(index + 2)
            features["next_is_after_plus2"] = self._follows_plus(index + 2)

        return features

    def sentence_features(self) -> list[dict[str, str | bool]]:
        """Return features for all tokens in sentence.

        Returns
        -------
        list[dict[str, str | bool]]
            List of features for each token in sentence
        """
        if self.defer_pos_tagging:
            # If part of speech tagging was deferred, do it now
            self.pos_tags = self._tag_partofspeech(self.tokenized_sentence)

        features = []
        for idx, _ in enumerate(self.tokenized_sentence):
            features.append(self._token_features(idx))

        return features

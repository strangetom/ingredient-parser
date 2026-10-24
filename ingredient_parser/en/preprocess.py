#!/usr/bin/env python3

import logging
import re
import string
import unicodedata
from html import unescape
from itertools import chain

from ..dataclasses import Token, TokenFeatures
from ._ambiguity import Disambiguator
from ._constants import (
    ASCII_SHAPE_TABLE,
    BREAKS,
    CLOSE_BRACKET,
    DIMENSIONS,
    FLATTENED_UNITS_LIST,
    LENGTH_UNITS,
    OPEN_BRACKET,
    SIZES,
    STRING_NUMBERS,
    UNICODE_FRACTIONS_TO_TEXT,
    UNITS,
)
from ._regex import (
    CAPITALISED_PATTERN,
    CURRENCY_PATTERN,
    DUPE_UNIT_RANGES_PATTERN,
    EXPANDED_RANGE,
    FRACTION_PARTS_PATTERN,
    HYPHEN_SPLIT_NAME_PATTERN,
    INCH_SIZE_PATTERN,
    QUANTITY_UNITS_PATTERN,
    QUANTITY_X_PATTERN,
    STRING_QUANTITY_HYPHEN_PATTERN,
    UNITS_HYPHEN_QUANTITY_PATTERN,
    UNITS_QUANTITY_PATTERN,
    UNITS_WITH_TRAILING_PERIOD,
)
from ._structure_features import SentenceStructureFeatures
from ._tokenize import tokenize
from ._utils import (
    combine_quantities_split_by_and,
    is_numeric,
    is_unit_synonym,
    pos_tag,
    replace_string_range,
    stem,
)

logger = logging.getLogger("ingredient-parser.preprocess")

CONSECUTIVE_SPACES = re.compile(r"\s+")
PUNCTUATION = frozenset(string.punctuation) | {"--"}

# Type alias for dict of token features.
FeatureDict = dict[str, str | bool]


# Define features to include for current token from context tokens.
# These are only included if the token has the feature.
CONTEXT_FEATURES = frozenset(
    [
        "stem",
        "pos",
        "is_capitalised",
        "is_punc",
        "is_dimension",
        "word_shape",
        "ends_with_inch_symbol",
        "is_unit",
        "is_size",
        "is_in_parens",
        "is_after_plus",
        "is_length_unit",
        "mip_start",
        "mip_end",
        "within_mip",
        "within_mip_clause_0",
        "within_mip_clause_-1",
        "within_mip_clause_-2",
        "after_sentence_split",
        "example_phrase",
        "dimensional_phrase",
        "number_type",
    ]
)
# Define the size of the context window and the prefixes to apply to the features from
# the context tokens.
CONTEXT_TOKEN_PREFIXES = {
    -3: "prev3_",
    -2: "prev2_",
    -1: "prev_",
    1: "next_",
    2: "next2_",
    3: "next3_",
}


class PreProcessor:
    """Recipe ingredient sentence PreProcessor class.

    Performs the necessary preprocessing on a sentence to generate the features
    required for the ingredient parser model.

    Each input sentence goes through a cleaning process to tidy up the input into a
    standardised form.

    Notes
    -----
    The cleaning steps are as follows:
        1.  Unescape HTML
        2.  Remove price annotations
        3.  Replace en and em dashes with hyphens
        4.  Replace unicode fractions with ASCII versions
        5.  Combine quantities split by 'and' (e.g. 1 and 1/2)
        6.  Identify fractions and convert to intermediate format
        7.  Split joined quantity and units
        8.  Remove trailing period from units
        9.  Replace string ranges
        10. Replace ranges involved duplicated units
        11. Merge quantity with following 'x'
        12. Collapse ranges into single token
        13. Expand hyphen split names into full names

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
    custom_units : dict[str, str] | None, optional
        Dict of plural-singular pairs of custom units.

    Attributes
    ----------
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

    def __init__(self, input_sentence: str, custom_units: dict[str, str] | None = None):
        """Initialise.

        Parameters
        ----------
        input_sentence : str
            Input ingredient sentence.
        custom_units : dict[str, str] | None, optional
            Dict of plural-singular pairs of custom units.
        """
        self.input: str = input_sentence
        if custom_units is not None:
            self._units = UNITS | custom_units
            self._flattened_units = FLATTENED_UNITS_LIST | set(
                chain.from_iterable(custom_units.items())
            )
        else:
            self._units = UNITS
            self._flattened_units = FLATTENED_UNITS_LIST

        self.sentence: str = self._normalise(input_sentence)
        logger.debug("Normalised sentence: '%s'.", self.sentence)

        self.singularised_indices = []
        self.tokenized_sentence = self._calculate_tokens(self.sentence)
        self.n_tokens = len(self.tokenized_sentence)
        self.sentence_structure = SentenceStructureFeatures(self.tokenized_sentence)

    def __repr__(self) -> str:
        """__repr__ method.

        Returns
        -------
        str
            String representation of initialised object.
        """
        return f'PreProcessor("{self.input}")'

    def __str__(self) -> str:
        """__str__ method.

        Returns
        -------
        str
            Human readable string representation of object.
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
            Ingredient sentence.

        Returns
        -------
        str
            Normalised ingredient sentence.
        """
        # List of functions to apply to sentence
        # Note that the order matters
        funcs = [
            self._unescape_html,
            self._remove_price_annotations,
            self._replace_en_em_dash,
            self._noramlize_quote_marks,
            self._replace_unicode_fractions,
            combine_quantities_split_by_and,
            self._identify_fractions,
            self._split_quantity_and_units,
            self._remove_unit_trailing_period,
            replace_string_range,
            self._replace_dupe_units_ranges,
            self._merge_quantity_x,
            self._collapse_ranges,
            self._expand_hyphen_split_names,
        ]

        for func in funcs:
            sentence = func(sentence)
            logger.debug("%s: %s", func.__name__, sentence)

        return sentence.strip()

    def _remove_price_annotations(self, sentence: str) -> str:
        """Remove price annotations like ($0.20), (£1.50), etc. from the sentence.

        Allows whitespace to occur after openining parenthesis, after currency symbol
        and before closing parenthesis.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with price annotations removed.
        """
        return CURRENCY_PATTERN.sub("", sentence)

    def _replace_en_em_dash(self, sentence: str) -> str:
        """Replace en-dashes and em-dashes with hyphens.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with en and em dashes replaced with hyphens.

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

    def _noramlize_quote_marks(self, sentence: str) -> str:
        """Replace ” “ ″ with " and ’ ′ with '.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with quote marks normalised.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._noramlize_quote_marks("1 2” piece ginger")
        '1 2" piece ginger'

        >>> p = PreProcessor("")
        >>> p._noramlize_quote_marks("3’ length sausage casing")
        "3' length sausage casing"
        """
        for mark in {"”", "“", "″"}:
            if mark in sentence:
                sentence = sentence.replace(mark, '"')

        for mark in {"’", "′"}:
            if mark in sentence:
                sentence = sentence.replace(mark, "'")

        return sentence

    def _unescape_html(self, sentence: str) -> str:
        """Replace escaped HTML entities e.g. &frac12; with unicode equivalents.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with html entities replaced.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_html_fractions("1&frac34; cups tomato ketchup")
        "1¾ cups tomato ketchup"

        >>> p = PreProcessor("")
        >>> p._replace_html_fractions("1 &ndash; 2 tbsp oil")
        "1 – 2 tbsp oil"
        """
        return unescape(sentence)

    def _identify_fractions(self, sentence: str) -> str:
        """Identify and modify fractions so that they do not get split by the tokenizer.

        This looks for fractions with the format of 1/2, 1/4, 1 1/2 etc. and replaces
        the forward slash with $ and inserts a # before the fractional part.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with fractions replaced with decimals.

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
            # Skip percentage-breakdown ratios like 80/20 (lean-to-fat grades on
            # ground meat). These look like fractions to the regex but aren't:
            # treating them as such collapses the ratio into a single token where
            # it semantically belongs as part of the ingredient name. The
            # discriminator only fires on bare X/Y where X+Y==100; compound forms
            # like "3 1/2" are always kept as fractions.
            if " " not in match:
                try:
                    n_str, d_str = match.split("/")
                    if int(n_str) + int(d_str) == 100:
                        continue
                except (ValueError, IndexError):
                    pass

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
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with unicode fractions replaced.

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
        " 1/4-1/2 teaspoon"
        """
        for f_unicode, f_ascii in UNICODE_FRACTIONS_TO_TEXT.items():
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
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with spaces inserted between quantity and units.

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
        if "-" in sentence:
            # These regular expressions only need to run if the sentence contains a
            # hyphen.
            sentence = UNITS_HYPHEN_QUANTITY_PATTERN.sub(r"\1 - \2", sentence)
            sentence = STRING_QUANTITY_HYPHEN_PATTERN.sub(r"\1 \2", sentence)
        return sentence

    def _remove_unit_trailing_period(self, sentence: str) -> str:
        """Remove trailing periods from units e.g. tsp. -> tsp.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with trailing periods from units removed.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._remove_unit_trailing_period("1 tsp. garlic powder")
        "1 tsp garlic powder"

        >>> p = PreProcessor("")
        >>> p._remove_unit_trailing_period("5 oz. chopped tomatoes")
        "5 oz chopped tomatoes"
        """

        def strip_trailing_period(match: re.Match) -> str:
            """Strip trailing period from matching unit.

            Parameters
            ----------
            m : re.Match
                Regular expression match capturing unit followed by period.

            Returns
            -------
            str
                Captured unit with trailing period removed.
            """
            return match.group(0).removesuffix(".")

        return UNITS_WITH_TRAILING_PERIOD.sub(strip_trailing_period, sentence)

    def _replace_dupe_units_ranges(self, sentence: str) -> str:
        """Replace ranges where the unit appears twice with standard range then unit.

        This assumes that the _split_quantity_and_units has already been run on
        the sentence.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with ranges containing unit twice replaced with
            standardised range.

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
        "0.5-1 c shelled raw pistachios"
        """
        matches = DUPE_UNIT_RANGES_PATTERN.findall(sentence)

        if not matches:
            return sentence

        for full_match, quantity1, unit1, quantity2, unit2 in matches:
            # We are only interested if the both captured units are the same
            if unit1 != unit2 and not is_unit_synonym(unit1, unit2):
                continue

            # If capture unit not in units list, abort
            if unit1 not in self._flattened_units and unit1 not in LENGTH_UNITS:
                continue

            sentence = sentence.replace(full_match, f"{quantity1}-{quantity2} {unit1}")

        return sentence

    def _merge_quantity_x(self, sentence: str) -> str:
        """Merge any quantity followed by "x" into a single token.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with single "x" merged into preceding number.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._merge_quantity_x("8 x 450 g/1 lb live lobsters")
        "8x 450g/1lb live lobsters"

        >>> p = PreProcessor("")
        >>> p._merge_quantity_x("4 x 100 g wild salmon fillet")
        "4x 100 g wild salmon fillet"
        """
        return QUANTITY_X_PATTERN.sub(r"\1x ", sentence)

    def _collapse_ranges(self, sentence: str) -> str:
        """Collapse any whites pace found in a range so the range has the standard form.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with white space removed from ranges.

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

    def _expand_hyphen_split_names(self, sentence: str) -> str:
        """Expand names split with a hyphen that have a common suffix, for example
        "medium- or -short-grain", "red- or yellow-fleshed".

        In these cases, this function will fully expand the first name so that it
        includes the common suffix.

        Parameters
        ----------
        sentence : str
            Ingredient sentence.

        Returns
        -------
        str
            Ingredient sentence with hyphen split names fully expanded.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._expand_hyphen_split_names("1 tablespoon red- or white-wine vinegar")
        "1 tablespoon red-wine or white-wine vinegar"

        >>> p = PreProcessor("")
        >>> p._expand_hyphen_split_names("2 cups unsalted stove- or air-popped popcorn")
        "2 cups unsalted stove-popped or air-popped popcorn"
        """
        for match in HYPHEN_SPLIT_NAME_PATTERN.finditer(sentence):
            split_word = match.group(1)
            common_suffix = match.group(2)
            replacement = split_word + common_suffix + " "
            sentence = re.sub(rf"\b{split_word}\s", replacement, sentence)

        return sentence

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
        tokens = []
        paren_depth = segment = 0
        for i, (text, pos) in enumerate(pos_tag(tokenize(sentence))):
            # Pre-compute this once because we need it in multiple places.
            token_is_numeric = is_numeric(text)

            # Convert tokens:
            # * Singularise units, keeping track of indices of singularised tokens
            # * Replace numeric token with "!num"
            if (singular := self._units.get(text)) and singular != text:
                self.singularised_indices.append(i)
                feat_text = singular
                text = singular
            elif token_is_numeric:
                feat_text = "!num"
            else:
                feat_text = text

            # Get part of speech tag, with overrides for certain tokens.
            if token_is_numeric:
                pos = "CD"
            elif text.lower() in ["c", "g"]:
                # Special cases for c (cup) and g (gram).
                pos = "NN"
            elif text.lower() in ["and/or", "or", "and"]:
                # Force 'and/or' tag to conjunction.
                # Force OR tag to conjunction.
                pos = "CC"
            elif text.lower() == "e.g.":
                # Force "e.g." tag to preposition/subordinating conjunction .
                pos = "IN"
            elif text.lower() == "/":
                # Force "/" to have SYM tag.
                pos = "SYM"
            elif text.lower() == "in" and i > 0 and tokens[i - 1].feat_text == "!num":
                # If the text is "in" and the previous token is a number then this is
                # mostly likely to be the abbreviation of inches rather than the
                # preposition.
                pos = "NN"

            features = TokenFeatures(
                stem=stem(feat_text),
                shape=self._word_shape(text),
                is_capitalised=self._is_capitalised(feat_text),
                is_punc=self._is_punc(feat_text),
                is_dimension=self._is_dimension(feat_text),
                ends_with_inch_symbol=self._ends_with_inch_symbol(feat_text),
            )

            if feat_text in OPEN_BRACKET:
                paren_depth += 1

            tokens.append(
                Token(
                    index=i,
                    text=text,
                    feat_text=feat_text,
                    pos_tag=pos,
                    segment=segment,
                    paren_depth=paren_depth,
                    features=features,
                )
            )

            if feat_text in CLOSE_BRACKET:
                paren_depth = max(paren_depth - 1, 0)
            elif feat_text in BREAKS and paren_depth == 0:
                # We don't increment the segment counter if the BREAK is within
                # parentheses or brackets.
                segment += 1

        logger.debug("Tokenized sentence: %s.", [t.text for t in tokens])
        logger.debug("Singularised tokens at indices: %s.", self.singularised_indices)

        return tokens

    def _is_unit(self, index: int) -> bool:
        """Return True if token is a unit.

        Parameters
        ----------
        index : int
            Index of token to check.

        Returns
        -------
        bool
            True if token  at index is a unit, else False.
        """
        token = self.tokenized_sentence[index]

        if Disambiguator.is_ambiguous(
            token, index in self.singularised_indices, "is_unit"
        ):
            disambiguator = Disambiguator(
                self.tokenized_sentence, self.singularised_indices
            )
            return disambiguator.does_feature_apply(index, "is_unit")

        text = token.feat_text
        return text in self._units.values() and text.lower() not in LENGTH_UNITS

    def _is_size(self, index: int) -> bool:
        """Return True if token is a size.

        Parameters
        ----------
        index : int
            Index of token to check.

        Returns
        -------
        bool
            True if token  at index is a size, else False.
        """
        token = self.tokenized_sentence[index]

        if Disambiguator.is_ambiguous(
            token, index in self.singularised_indices, "is_size"
        ):
            disambiguator = Disambiguator(
                self.tokenized_sentence, self.singularised_indices
            )
            return disambiguator.does_feature_apply(index, "is_size")

        return token.feat_text.lower() in SIZES

    def _is_dimension(self, token: str) -> bool:
        """Return True if token is a dimension.

        Parameters
        ----------
        token : str
            Token to check.

        Returns
        -------
        bool
            True if token is a dimension, else False.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._is_dimension("thick")
        True

        >>> p = PreProcessor("")
        >>> p._is_dimension("long")
        True

        >>> p = PreProcessor("")
        >>> p._is_dimension("cm")
        False
        """
        if token.lower() in DIMENSIONS:
            return True

        # Try splitting token on hyphens and checking the last part
        if "-" in token:
            end_part = token.lower().split("-")[-1]
            if end_part in DIMENSIONS:
                return True

        return False

    def _ends_with_inch_symbol(self, token: str) -> bool:
        """Return True is token ends with an inch size e.g. 1", 2".

        Parameters
        ----------
        token : str
            Token to check.

        Returns
        -------
        bool
            True if token ends with inch size, else False.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._ends_with_inch_symbol('1"')
        True

        >>> p = PreProcessor("")
        >>> p._ends_with_inch_symbol('2-3"')
        True

        >>> p = PreProcessor("")
        >>> p._ends_with_inch_symbol("1 inch")
        False
        """
        return INCH_SIZE_PATTERN.search(token) is not None

    def _is_length_unit(self, index: int) -> bool:
        """Return True if token at index is a length unit.

        For the token "in", this function also checks previous token to ensure it return
        False when "in" does not mean "inch".

        Parameters
        ----------
        index : int
            Index of token to check.

        Returns
        -------
        bool
            True if token is a length unit, else False.
        """
        token = self.tokenized_sentence[index].feat_text
        if token == "in":
            if index > 0 and self.tokenized_sentence[index - 1].feat_text == "!num":
                return True

            return False

        return token.lower() in LENGTH_UNITS

    def _is_punc(self, token: str) -> bool:
        """Return True if token is a punctuation mark.

        Parameters
        ----------
        token : str
            Token to check.

        Returns
        -------
        bool
            True if token is a punctuation mark, else False.

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._is_punc("/")
        True

        >>> p = PreProcessor("")
        >>> p._is_punc("--")
        True

        >>> p = PreProcessor("")
        >>> p._is_punc("beef")
        False
        """
        return token in PUNCTUATION

    def _follows_plus(self, index: int) -> bool:
        """Return True if token at index follow "plus" by any amount in sentence.

        If the token at the index is "plus", it doesn't count as following.

        Parameters
        ----------
        index : int
            Index of token to check.

        Returns
        -------
        bool
            True if token follows "plus", else False.
        """
        return "plus" in [t.feat_text for t in self.tokenized_sentence[:index]]

    def _follows_colon(self, index: int) -> bool:
        """Return True if token at index follow ":" by any amount in sentence.

        If the token at the index is ":", it doesn't count as following.

        Parameters
        ----------
        index : int
            Index of token to check.

        Returns
        -------
        bool
            True if token follows ":", else False.
        """
        return ":" in [t.feat_text for t in self.tokenized_sentence[:index]]

    def _is_capitalised(self, token: str) -> bool:
        """Return True if token starts with a capital letter.

        Parameters
        ----------
        token : str
            Token to check.

        Returns
        -------
        bool
            True if token starts with a capital letter, else False.

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
            Index of token to check.

        Returns
        -------
        bool
            True if index is inside parentheses or is parenthesis, else False.
        """
        return self.tokenized_sentence[index].paren_depth > 0

    def _sentence_length_bucket(self) -> int:
        """Return the length of sentence, rounding down to the nearest bucket.

        The buckets are 2, 4, 8, 12, 16, 20, 32, 64

        Returns
        -------
        int
            Length bucket of sentence.
        """
        bucket = 1
        for length_bucket in [2, 4, 8, 12, 16, 20, 32, 64]:
            if self.n_tokens >= length_bucket:
                bucket = length_bucket

        return bucket

    def _number_type(self, token: str) -> str:
        """Return string indicating the type of number for numeric tokens.

        To avoid duplicate calls to is_numeric(), this function assumes the token being
        passed would return True from is_numeric()

        The types of number are:
        * word
        * multiplier
        * range
        * decimal
        * fraction
        * integer

        Parameters
        ----------
        token : str
            Token to return number type of.

        Returns
        -------
        str
            Number type.
        """

        token = token.lower()
        if token in STRING_NUMBERS or token == "dozen":
            return "word"

        elif token.endswith("x"):
            return "multiplier"

        elif "-" in token[1:]:
            # We don't want this to match if the token starts with "-"
            return "range"

        elif "#" in token:
            return "fraction"

        elif "." in token:
            return "decimal"

        else:
            return "integer"

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
        return normalised.translate(ASCII_SHAPE_TABLE)

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
        if token.isascii():
            # If token is ASCII, then it contains no accents so we can avoid doing any
            # work.
            return token

        return "".join(
            c
            for c in unicodedata.normalize("NFD", token)
            if unicodedata.category(c) != "Mn"
        )

    def _common_features(self, token: Token) -> FeatureDict:
        """Return common features for token at given index.

        Parameters
        ----------
        token : Token
            Token to return features for.

        Returns
        -------
        FeatureDict
            Dict of features for token at given index.
        """
        token = self.tokenized_sentence[token.index]
        features = {
            "bias": "",
            "sentence_length": str(self._sentence_length_bucket()),
            "pos": token.pos_tag,
            "stem": token.features.stem,
            "is_capitalised": token.features.is_capitalised,
            "is_punc": token.features.is_punc,
            "is_dimension": token.features.is_dimension,
            "word_shape": token.features.shape,
            "ends_with_inch_symbol": token.features.ends_with_inch_symbol,
            "is_unit": self._is_unit(token.index),
            "is_size": self._is_size(token.index),
            "is_in_parens": self._is_inside_parentheses(token.index),
            "is_after_plus": self._follows_plus(token.index),
            "is_after_colon": self._follows_colon(token.index),
            "is_length_unit": self._is_length_unit(token.index),
        }

        if token.feat_text != token.features.stem:
            features["token"] = token.feat_text

        if token.feat_text == "!num":
            features["number_type"] = self._number_type(token.text)

        features |= self._ngram_features(token.feat_text, "")
        features |= self.sentence_structure.token_features(token.index, "")

        return features

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

    def _pos_ngram(
        self, sentence_tags: list[str], index: int, offset: int
    ) -> list[str]:
        """Generate part of speech tag ngram for token at given index for given offset.

        The part of speech ngram is a list of contiguous part of speech tags between the
        token at the given index and the token at the offset from the given index.

        The tags are ordered so that the tag for the left most token in the sentence is
        first e.g.:
        For index=3, offset=2: [tag_3, tag_4, tag_5]
        For index=1, offset=-2: [<BOS> tag_0, tag_1]

        Parameters
        ----------
        sentence_tags : list[str]
            List of part of speech tags for full sentence, padding at start and end to
            cover maximum context window.
        index : int
            Index of token.
        offset : int
            Offset from index to generate ngram for.

        Returns
        -------
        list[str]
            List POS tags that make up ngram.
        """
        # Calculate the minimum index, can't be less than 0.
        # Note the index in increased by +3 to account for the padding tags at the start
        # of the sentence.
        min_ngram_index = max(0, min(index + 3, index + offset + 3))

        # Calculate the maximum index, can't be greater than sentence length (including
        # the padding).
        max_ngram_index = min(
            len(sentence_tags), max(index + 3, index + offset + 3) + 1
        )

        return sentence_tags[min_ngram_index:max_ngram_index]

    def _whole_sentence_features(self) -> FeatureDict:
        """Generate features based on the complete sentence.

        These features are applied to every token and are the same for each token.

        Returns
        -------
        FeatureDict
            Dict of whole sentence features.
        """
        return {
            "starts_with_qty": self.tokenized_sentence[0].feat_text == "!num",
            "starts_with_unit": self._is_unit(0),
            "n_numeric": str(
                sum(1 for t in self.tokenized_sentence if t.feat_text == "!num")
            ),
            "has_parens": any(t.paren_depth > 0 for t in self.tokenized_sentence),
            "has_or": any(t.feat_text.lower() == "or" for t in self.tokenized_sentence),
            "n_segments": str(self.tokenized_sentence[-1].segment),
        }

    def sentence_features(self) -> list[FeatureDict]:
        """Return dict of features for each token in sentence.

        This is done in two stages:
        1. Calculate the common features that every token has.
        2. Calculate the features for the context of each token by looking up the
           features from the common features for the context tokens.

        This two stage approach avoids calculating each feature for every token and
        every time each token is a context token, which improves performance.

        Returns
        -------
        list[FeatureDict]
            List of feature dicts for each token in sentence.
        """
        logger.debug("Generating features for tokens.")

        # Extract sentence pos tags and pad to cover the maximum context window size.
        sentence_pos_tags = (
            ["<BOS>"] * 3 + [t.pos_tag for t in self.tokenized_sentence] + ["<EOS>"] * 3
        )
        sentence_features = [
            self._common_features(token) for token in self.tokenized_sentence
        ]

        # Add conjunction and whole sentence features for the each token.
        whole_sentence_features = self._whole_sentence_features()
        for i, features in enumerate(sentence_features):
            prev = sentence_features[i - 1] if i > 0 else None
            next = sentence_features[i + 1] if i < self.n_tokens - 1 else None

            prev_stem = prev["stem"] if prev else "<BOS>"
            next_stem = next["stem"] if next else "<EOS>"

            features["prev_stem+stem"] = f"{prev_stem}+{features['stem']}"
            features["stem+next_stem"] = f"{features['stem']}+{next_stem}"
            features["is_unit+prev_num"] = (
                f"{features['is_unit']}+{bool(prev) and prev['stem'] == '!num'}"
            )
            features["pos+is_parens"] = f"{features['pos']}+{features['is_in_parens']}"
            features["pos+segment"] = f"{features['pos']}+{features['segment']}"

            if next and features["stem"] == "!num":
                # number_type feature is only defined if the stem is "!num"
                features["num_type+next_is_unit"] = (
                    f"{features['number_type']}+{next['is_unit']}"
                )

            features |= whole_sentence_features

        # Calculate the features used for each token when the token is in the context
        # window of another token.
        # This is a list of (feature name, feature value) tuples for each each element
        # in the sentence.
        # This approach means we only calculate the features for a context token once
        # and we can just look up the features of each context token to include in the
        # features for each token.
        context_features = [
            [(feat, val) for feat, val in features.items() if feat in CONTEXT_FEATURES]
            for features in sentence_features
        ]

        # Iterate over sentence features and add features for context tokens to features
        # for each token.
        for i, features in enumerate(sentence_features):
            # Iterate over all context window offsets for each element of
            # sentence_features.
            for offset, prefix in CONTEXT_TOKEN_PREFIXES.items():
                # If the index for the given context feature is within the sentence
                # (i.e. not < 0 or > sentence length), then obtain the context features
                # for that token from the already calculated sentence_features.
                if 0 <= i + offset < self.n_tokens:
                    for feature, value in context_features[i + offset]:
                        features[prefix + feature] = value

                pos_ngram = self._pos_ngram(sentence_pos_tags, i, offset)
                features[prefix + "pos_ngram"] = "+".join(pos_ngram)

        return sentence_features

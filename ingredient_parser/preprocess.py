#!/usr/bin/env python3

import re
from fractions import Fraction
from typing import Any, Dict, List

from nltk.tokenize import RegexpTokenizer
from nltk.tag import pos_tag


# Regex pattern for fraction parts.
# Matches 0+ numbers followed by 0+ whitespace charaters followed by a number then a forward slash then another number
FRACTION_PARTS_PATTERN = re.compile(r"(\d*\s*\d/\d)")

# Regex pattern for checking if token starts with a capital letter
CAPITALISED_PATTERN = re.compile(r"^[A-Z]")

# Regex pattern for finding quantity and units without space between them.
# Assumes the quantity is always a number and the units always a letter
QUANTITY_UNITS = re.compile(r"(\d)([a-zA-Z])")

# Regex pattern for matching a numeric range e.g. 1-2, 2-3
RANGE_PATTERN = re.compile(r"\d+\-\d+")

# Predefine tokenizer
# The regex pattern matches the tokens: any word character, including '.' and '-', or ( or ) or , or "
REGEXP_TOKENIZER = RegexpTokenizer('[\w\.-]+|\(|\)|,|"', gaps=False)

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
}


class PreProcessor:
    def __init__(self, sentence: str):
        """Summary

        Parameters
        ----------
        ingredient : str
            Ingredient sentence
        """
        self.sentence = self.clean(sentence)
        self.tokenized_sentence = REGEXP_TOKENIZER.tokenize(self.sentence)
        self.pos_tags = self.tag_partofspeech(self.tokenized_sentence)

    def clean(self, sentence: str) -> str:
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
        # List of funtions to apply to sentence, in order
        funcs = [
            self.replace_unicode_fractions,
            self.replace_fake_fractions,
            self.split_quantity_and_units,
            self.singlarise_unit,
        ]

        for func in funcs:
            sentence = func(sentence)

        return sentence

    def replace_fake_fractions(self, sentence: str) -> str:
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
        if matches is None:
            return sentence

        for match in matches:
            split = match.split()
            summed = float(sum(Fraction(s) for s in split))
            rounded = round(summed, 2)
            sentence = sentence.replace(match, f" {rounded:g}")

        return sentence

    def replace_unicode_fractions(self, sentence: str) -> str:
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

    def split_quantity_and_units(self, sentence: str) -> str:
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
        return QUANTITY_UNITS.sub(r"\1 \2", sentence)

    def singlarise_unit(self, sentence: str) -> str:
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

    def tag_partofspeech(self, tokens: List[str]) -> List[str]:
        """Tag tokens with part of speech using universal tagset
        This function ensures that numeric ranges are tagged as NUM

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
        for token, tag in pos_tag(tokens, tagset="universal"):
            if RANGE_PATTERN.match(token):
                tag = "NUM"
            tags.append(tag)
        return tags

    def get_length(self, tokens: List[str]) -> int:
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
        l = len(tokens)
        for n in [4, 8, 12, 16, 20, 26, 32, 38, 44, 50, 70]:
            if l < n:
                return n

        return 0

    def is_unit(self, token: str) -> bool:
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

    def is_numeric(self, token: str) -> bool:
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
            return all([self.is_numeric(part) for part in parts])

        try:
            float(token)
            return True
        except ValueError:
            return False

    def follows_comma(self, token: str) -> bool:
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

    def is_capitalised(self, token: str) -> bool:
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

    def is_inside_parentheses(self, token: str) -> bool:
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

    def token_features(self, index: int) -> Dict[str, Any]:
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
            "word": token,
            "pos": self.pos_tags[index],
            "prev_word": "" if index == 0 else self.tokenized_sentence[index - 1],
            "prev_word2": "" if index < 2 else self.tokenized_sentence[index - 2],
            "next_word": ""
            if index == len(self.tokenized_sentence) - 1
            else self.tokenized_sentence[index + 1],
            "next_word2": ""
            if index >= len(self.tokenized_sentence) - 2
            else self.tokenized_sentence[index + 2],
            "is_capitalised": self.is_capitalised(token),
            "is_numeric": self.is_numeric(token),
            "is_unit": self.is_unit(token),
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
        features = []
        for idx, _ in enumerate(self.tokenized_sentence):
            features.append(self.token_features(idx))

        return features

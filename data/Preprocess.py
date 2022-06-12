#!/usr/bin/env python3

import re

from fractions import Fraction
from itertools import chain
from typing import Dict, List, Optional

from nltk import pos_tag
from nltk.tokenize import RegexpTokenizer

# List of common units
UNITS = {
    "tablespoon": ["tbsp", "tbsps", "tablespoon", "tablespoons", "Tbsp"],
    "teaspoon": ["tsp", "tsps", "teaspoon", "teaspoons"],
    "gram": ["g", "gram", "grams", "g can", "g cans", "g tin", "g tins"],
    "kilogram": ["kg", "kilogram", "kilograms"],
    "liter": ["l", "liter", "liters", "litre", "litres"],
    "milliliter": ["ml", "milliliter", "milliliters"],
    "pinch": ["pinch", "pinches"],
    "handful": ["handful", "handfuls"],
    "clove": ["cloves", "clove"],
    "sprig": ["sprig", "sprigs"],
    "stick": ["stick", "sticks"],
    "size": ["small", "medium", "large"],
    "dimension": ["cm", "inch", "'"],
    "cup": ["cup", "cups", "mug", "mugs"],
    "bunch": ["bunches", "bunch"],
    "rasher": ["rasher", "rashers"],
    "ounce": ["ounce", "ounces", "oz", "oz."],
    "pound": ["pound", "pounds", "lb", "lbs", "lb.", "lbs."],
}
UNITS_LIST = list(chain.from_iterable(UNITS.values()))

# Regex pattern for fraction parts.
# Matches 1+ numbers followed by 1+ whitespace charaters followed by a number then a forward slash then another number
FRACTION_PARTS_PATTERN = re.compile(r"(\d*\s*\d/\d)")

# Regex pattern for units no preceeding by space
UNITS_NOT_PRECEEDED_BY_SPACE_PATTERN = re.compile(
    r"\S(%s)\s" % ("|".join(UNITS_LIST)), re.IGNORECASE
)

# Regex pattern for checking if token starts with a capital letter
CAPITALISED_PATTERN = re.compile(r"^[A-Z]")

# Predefine tokenizer
# The regex pattern matches the tokens: any word character, including '.', or ( or ) or ,
RegExpTokenizer = RegexpTokenizer("[\w\.]+|\(|\)|,", gaps=False)


class PreProcessor:
    def __init__(self, ingredient: str, labels: Dict[str, str]):
        """Summary

        Parameters
        ----------
        ingredient : str
            Ingredient sentence
        labels : Dict[str, str]
            Labels for ingredient sentence
        """
        self.sentence = ingredient
        self.labels = labels

    def split_units_from_quantity(self, string: str) -> str:
        """Ensure there is always a space before the units

        Parameters
        ----------
        string : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with a space inserted before units if there wasn't already one

        Examples
        -------
        >>> split_units_from_quantity("100g flour")
        '100 g flour'

        >>> split_units_from_quanity("2 cups wine")
        '2 cups wine'
        """
        return UNITS_NOT_PRECEEDED_BY_SPACE_PATTERN.sub(r" \1", string)

    def replace_fractions(self, string: str) -> str:
        """Attempt to parse fractions from sentence and convert to decimal

        Parameters
        ----------
        string : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with fractions replaced with decimals
        """
        matches = FRACTION_PARTS_PATTERN.match(string)
        if matches is None:
            return string

        for match in matches.groups():
            split = match.split()
            summed = float(sum(Fraction(s) for s in split))
            rounded = round(summed, 2)
            string = string.replace(match, f"{rounded:g}")

        return string

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
        for n in [4, 8, 12, 16, 20]:
            if l < n:
                return n

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
        if token not in self.sentence:
            return False

        # If it's "(" or ")", return True
        if token in ["(", ")"]:
            return True

        return (
            "(" in self.sentence.split(token)[0]
            and ")" in self.sentence.split(token)[-1]
        )

    def singlarise_unit(self, token: str) -> str:
        """Singularise units
        e.g. cups -> cup, tablespoons -> tablespoon

        Parameters
        ----------
        token : str
            Token to singularise

        Returns
        -------
        str
            Singularised token or original token
        """
        units = {
            "cups": "cup",
            "tablespoons": "tablespoon",
            "teaspoons": "teaspoon",
            "pounds": "pound",
            "ounces": "ounce",
            "cloves": "clove",
            "sprigs": "sprig",
            "pinches": "pinch",
            "bunches": "bunch",
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
        if token in units.keys():
            return units[token]
        else:
            return token

    def match_label(self, token: str) -> str:
        """Match a token to it's label
        This is naive in that it assumes a token can only have one label with the sentence

        Parameters
        ----------
        token : str
            Token to match

        Returns
        -------
        str
            Label for token, or None
        """

        # TODO:
        # 1. Handle ingredients that have both US and metric units (or remove them from training data...)
        # 2. Singularise all units so they match the label

        # Make lower case first, beccause all labels are lower case
        token = token.lower()
        token = self.singlarise_unit(token)

        if token in self.labels["quantity"]:
            return "QTY"
        elif token in self.labels["unit"]:
            return "UNIT"
        elif token in self.labels["name"]:
            return "NAME"
        elif token in self.labels["comment"]:
            return "COMMENT"
        else:
            return "OTHER"

    def generate_token_features(self) -> List[Dict[str, str]]:
        """Generate a list of tokens and their features for the sentence

        Returns
        -------
        List[Dict[str, str]]
            List of dictionaries containing the token and features
        """
        sentence_features = []

        # Clean sentence
        cleaned_sentence = self.replace_fractions(self.sentence)

        # Split into tokens and determine features for each token
        tokens = RegExpTokenizer.tokenize(cleaned_sentence)
        length = self.get_length(tokens)
        tagged_tokens = pos_tag(tokens)

        prev_bio_tags = set()
        for idx, (token, pos) in enumerate(tagged_tokens):
            features = {
                "token": token,
                "index": f"I{idx+1}",
                "POS": pos,
                "length": f"L{length}",
                "IsCap": self.is_capitalised(token),
                "IsParen": self.is_inside_parentheses(token),
            }

            # Now lets work out the BIO tag
            label = self.match_label(token)
            if label == "OTHER":
                features["BIO"] = label
            else:
                # Work out if it's B or I
                if label not in prev_bio_tags:
                    bio_tag = f"B-{label}"
                    prev_bio_tags.add(label)
                else:
                    bio_tag = f"I-{label}"
                features["BIO"] = bio_tag

            sentence_features.append(features)

        return sentence_features

#!/usr/bin/env python3

import re
import string
from itertools import chain

# Plural and singular units. Length units are excluded.
UNITS = {
    "balls": "ball",
    "bags": "bag",
    "bars": "bar",
    "baskets": "basket",
    "batches": "batch",
    "blocks": "block",
    "bottles": "bottle",
    "boxes": "box",
    "branches": "branch",
    "buckets": "bucket",
    "bulbs": "bulb",
    "bunches": "bunch",
    "bundles": "bundle",
    "c": "c",
    "cans": "can",
    "canisters": "canister",
    "chunks": "chunk",
    "cloves": "clove",
    "clusters": "cluster",
    "counts": "count",
    "cl": "cl",
    "cL": "cL",
    "cubes": "cube",
    "cups": "cup",
    "cutlets": "cutlet",
    "dashes": "dash",
    "dessertspoons": "dessertspoon",
    "dollops": "dollop",
    "drops": "drop",
    "ears": "ear",
    "envelopes": "envelope",
    "feet": "foot",
    "fl": "fl",
    "floz": "floz",
    "g": "g",
    "gm": "gm",
    "gal": "gal",
    "gallons": "gallon",
    "glasses": "glass",
    "grams": "gram",
    "grinds": "grind",
    "handfuls": "handful",
    "heads": "head",
    "jars": "jar",
    "jiggers": "jigger",
    "kg": "kg",
    "kilos": "kilo",
    "kilograms": "kilogram",
    "knobs": "knob",
    "ladles": "ladle",
    "lbs": "lb",
    "leaves": "leaf",
    "lengths": "length",
    "links": "link",
    "l": "l",
    "liters": "liter",
    "litres": "litre",
    "loaves": "loaf",
    "milliliters": "milliliter",
    "millilitres": "millilitre",
    "ml": "ml",
    "mL": "mL",
    "mugs": "mug",
    "ounces": "ounce",
    "oz": "oz",
    "packs": "pack",
    "packages": "package",
    "packets": "packet",
    "pairs": "pair",
    "pieces": "piece",
    "pinches": "pinch",
    "pints": "pint",
    "pods": "pod",
    "pots": "pot",
    "pounds": "pound",
    "pts": "pt",
    "punnets": "punnet",
    "rashers": "rasher",
    "recipes": "recipe",
    "rectangles": "rectangle",
    "ribs": "rib",
    "quarts": "quart",
    "qt": "qt",
    "sachets": "sachet",
    "scoops": "scoop",
    "sections": "section",
    "segments": "segment",
    "shakes": "shake",
    "sheets": "sheet",
    "shots": "shot",
    "shoots": "shoot",
    "slabs": "slab",
    "slices": "slice",
    "sprigs": "sprig",
    "squares": "square",
    "stalks": "stalk",
    "stems": "stem",
    "sticks": "stick",
    "strips": "strip",
    "ts": "t",
    "tablespoons": "tablespoon",
    "tbsps": "tbsp",
    "tbs": "tb",
    "teaspoons": "teaspoon",
    "tins": "tin",
    "tsps": "tsp",
    "tubs": "tub",
    "tubes": "tube",
    "twists": "twist",
    "units": "unit",
    "wedges": "wedge",
    "vials": "vial",
    "wheels": "wheel",
}


def _generate_upper_case_units(units: dict[str, str]) -> dict[str, str]:
    """Generate capitalized and uppercase version of each entry in the units dict.

    Parameters
    ----------
    units : dict[str, str]
        UNITS dict
    """
    _capitalized_units = {}
    for plural, singular in units.items():
        _capitalized_units[plural.capitalize()] = singular.capitalize()
        _capitalized_units[plural.upper()] = singular.upper()
    return UNITS | _capitalized_units


UNITS = _generate_upper_case_units(UNITS)

# Create a flattened set of all keys and values in UNITS dict
# since we need this in a few places
FLATTENED_UNITS_LIST = frozenset(chain.from_iterable(UNITS.items()))

# Invert UNITS dict so we can look up plural form from singular form.
UNITS_RINDEX: dict[str, str] = {v: k for k, v in UNITS.items()}

# Words that indicate ingredient size
SIZES = [
    "#2",
    "#2.5",
    "#10",
    "#300",
    "#303",
    "big",
    "bite-size",
    "bite-sized",
    "extra-large",
    "jumbo",
    "large",
    "lg",
    "little",
    "md",
    "medium",
    "medium-large",
    "medium-size",
    "medium-sized",
    "medium-small",
    "medium-to-large",
    "miniature",
    "regular",
    "slim",
    "sm",
    "small",
    "small-to-medium",
    "smaller",
    "smallest",
    "thick",
    "thin",
    "tiny",
]


# Strings and their numeric representation
STRING_NUMBERS = {
    "one-quarter": "1/4",
    "one-half": "1/2",
    "three-quarter": "3/4",
    "three-quarters": "3/4",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
}


def _generate_string_number_regexes(
    string_numbers: dict[str, str],
) -> dict[str, tuple[re.Pattern, str]]:
    """Generate pre-compiled regular expressions for converting number expressed as
    words to digits.

    The return dict values are a tuple of the pre-compiled regular expression and the
    replacement string.

    Parameters
    ----------
    string_numbers : dict[str, str]
        Dict of number as words and their digit equivalent.

    Returns
    -------
    dict[str, tuple[re.Pattern, str]]
        Dict mapping word number to a tuple of (regex, replacement).
    """
    string_numbers_regexes = {}
    for s, n in string_numbers.items():
        # This is case insensitive so it replace e.g. "one" and "One"
        # Only match if the string is preceded by a non-word character or is at
        # the start of the sentence
        string_numbers_regexes[s] = (re.compile(rf"\b({s})\b", flags=re.IGNORECASE), n)
    return string_numbers_regexes


STRING_NUMBERS_REGEXES = _generate_string_number_regexes(STRING_NUMBERS)

# Unicode fractions and their replacements as string fractions
# Most of the time we need to insert a space in front of the replacement so we don't
# merge the replacement with the previous token i.e. 1½ != 11/2
# However, if the prior chaacter is a hyphen, we don't want to insert a space as this
# will mess up any ranges
UNICODE_FRACTIONS_TO_TEXT = {
    "-\u215b": "-1/8",
    "-\u215c": "-3/8",
    "-\u215d": "-5/8",
    "-\u215e": "-7/8",
    "-\u2159": "-1/6",
    "-\u215a": "-5/6",
    "-\u2155": "-1/5",
    "-\u2156": "-2/5",
    "-\u2157": "-3/5",
    "-\u2158": "-4/5",
    "-\xbc": "-1/4",
    "-\xbe": "-3/4",
    "-\u2153": "-1/3",
    "-\u2154": "-2/3",
    "-\xbd": "-1/2",
    "\u215b": " 1/8",
    "\u215c": " 3/8",
    "\u215d": " 5/8",
    "\u215e": " 7/8",
    "\u2159": " 1/6",
    "\u215a": " 5/6",
    "\u2155": " 1/5",
    "\u2156": " 2/5",
    "\u2157": " 3/5",
    "\u2158": " 4/5",
    "\xbc": " 1/4",
    "\xbe": " 3/4",
    "\u2153": " 1/3",
    "\u2154": " 2/3",
    "\xbd": " 1/2",
}

# Stop words - high frequency grammatical words derived from nltk.corpus.stopwords
# The original list from NLTK has been edited to remove words that the tokenizer cannot
# output.
# See also https://dx.doi.org/10.18653/v1/W18-2502
STOP_WORDS = {
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "you're",
    "you've",
    "you'll",
    "you'd",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "she's",
    "her",
    "hers",
    "herself",
    "it",
    "it's",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "that'll",
    "these",
    "those",
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "a",
    "an",
    "the",
    "and",
    "but",
    "if",
    "or",
    "because",
    "as",
    "until",
    "while",
    "of",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "can",
    "will",
    "just",
    "don't",
    "should",
    "should've",
    "now",
    "aren't",
    "couldn't",
    "didn't",
    "doesn't",
    "hadn't",
    "hasn't",
    "haven't",
    "isn't",
    "mightn't",
    "mustn't",
    "needn't",
    "shan't",
    "shouldn't",
    "wasn't",
    "weren't",
    "won't",
    "wouldn't",
}

# Tokens that indicate a quantity is approximate
APPROXIMATE_PREFIXES = [
    "about",
    "approx",
    "approximately",
    "nearly",
    "roughly",
    "~",
    "generous",
]
APPROXIMATE_SUFFIXES = [["or", "so"]]
# Tokens that indicate an amount is singular
SINGULAR_TOKENS = ["each"]
# Tokens that indicate an amount refers to the prepared ingredient
PREPARED_INGREDIENT_TOKENS = [
    ["to", "yield"],
    ["to", "make"],
]

# List of sets, where each set contains the synonyms that represent the same unit.
UNIT_SYNONYMS = [
    {"cup", "c"},
    {"gram", "g", "gm"},
    {"kilogram", "kg"},
    {"litre", "liter", "l"},
    {"ounce", "oz"},
    {"pound", "lb"},
    {"quart", "qt"},
    {"tablespoon", "tbsp", "tbs", "tb"},
    {"teaspoon", "tsp"},
    {"pint", "pt"},
]

# Set of units that refer to lengths.
LENGTH_UNITS = frozenset(
    {
        "centimeter",
        "centimeters",
        "centimetre",
        "centimetres",
        "cm",
        "in",
        "inch",
        "inches",
        "millimeter",
        "millimeters",
        "millimetre",
        "millimetres",
        "mm",
    }
)

# Set of tokens that refer to the physical dimensions of an ingredient.
DIMENSIONS = frozenset(
    {
        "diameter",
        "inch-long",
        "inch-thick",
        "length",
        "long",
        "thick",
        "thickness",
        "wide",
        "width",
    }
)

INDEFINITE_QUANTIFIERS = frozenset(
    {
        "couple",
        "few",
        "many",
        "plenty",
        "more",
        "several",
        "some",
    }
)

# Define table mapping ascii characters to characters used in word shape.
ASCII_SHAPE_TABLE = str.maketrans(
    {
        **{c: "x" for c in string.ascii_lowercase},
        **{c: "X" for c in string.ascii_uppercase},
        **{c: "d" for c in string.digits},
    }
)

# Define characters to mark sentence segment boundaries.
OPEN_BRACKET = frozenset({"(", "["})
CLOSE_BRACKET = frozenset({")", "]"})
BREAKS = frozenset({",", ";"})

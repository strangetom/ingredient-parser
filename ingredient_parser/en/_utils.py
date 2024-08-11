#!/usr/bin/env python3

import re
from fractions import Fraction
from functools import lru_cache
from itertools import chain

import pint
from nltk.stem.porter import PorterStemmer
from nltk.tag.perceptron import PerceptronTagger

from .._common import download_nltk_resources, is_float, is_range
from ..dataclasses import IngredientAmount
from ._constants import UNITS
from ._regex import FRACTION_SPLIT_AND_PATTERN, STRING_RANGE_PATTERN

UREG = pint.UnitRegistry()

# Dict mapping certain units to their imperial version in pint
IMPERIAL_UNITS = {
    "cup": "imperial_cup",
    "floz": "imperial_floz",
    "fluid_ounce": "imperial_fluid_ounce",
    "quart": "imperial_quart",
    "pint": "imperial_pint",
    "gallon": "imperial_gallon",
}

# List of units that pint interprets as incorrect unit
# The comment indicates what pint interprets the unit as
MISINTERPRETED_UNITS = [
    "pinch",  # pico-inch
    "pinches",
    "bar",  # bar (pressure)
    "bars",
    "link",  # link (distance)
    "links",
    "shake",  # shake (time)
    "shakes",
    "tin",  # tera-inch
    "tins",
    "fat",  # femto-technical-atmosphere
]

# List of unit replacements so that these units get converted to the correct pint
# units. Each entry is a tuple of a pre-compliled regex, and the replacement value.
UNIT_REPLACEMENTS = [
    (re.compile(r"\b(fl oz)\b"), "floz"),
    (re.compile(r"\b(fluid oz)\b"), "fluid_ounce"),
    (re.compile(r"\b(fl ounce)\b"), "fluid_ounce"),
    (re.compile(r"\b(fluid ounce)\b"), "fluid_ounce"),
    (re.compile(r"\b(C)\b"), "cup"),
    (re.compile(r"\b(c)\b"), "cup"),
    (re.compile(r"\b(Cl)\b"), "centiliter"),
    (re.compile(r"\b(G)\b"), "gram"),
    (re.compile(r"\b(Ml)\b"), "milliliter"),
    (re.compile(r"\b(Mm)\b"), "millimeter"),
    (re.compile(r"\b(Pt)\b"), "pint"),
    (re.compile(r"\b(Tb)\b"), "tablespoon"),
]

download_nltk_resources()
STEMMER = PorterStemmer()
TAGGER = PerceptronTagger()

# Define regular expressions used by tokenizer.
# Matches one or more whitespace characters
WHITESPACE_TOKENISER = re.compile(r"\S+")
# Matches and captures one of the following: ( ) [ ] { } , " / : ; ? !
PUNCTUATION_TOKENISER = re.compile(r"([\(\)\[\]\{\}\,/:;\?\!\*])")
# Matches and captures full stop at end of string
# (?>!\.\w) is a negative lookbehind that prevents matches if the last full stop
# is preceded by a a full stop then a word character.
FULL_STOP_TOKENISER = re.compile(r"(?<!\.\w)(\.)$")


def tokenize(sentence: str) -> list[str]:
    """Tokenise an ingredient sentence.

    The sentence is split on whitespace characters into a list of tokens.
    If any of these tokens contains of the punctuation marks captured by
    PUNCTUATION_TOKENISER, these are then split and isolated as a separate
    token.

    The returned list of tokens has any empty tokens removed.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to tokenize

    Returns
    -------
    list[str]
        List of tokens from sentence.

    Examples
    --------
    >>> tokenize("2 cups (500 ml) milk")
    ["2", "cups", "(", "500", "ml", ")", "milk"]

    >>> tokenize("1-2 mashed bananas: as ripe as possible")
    ["1-2", "mashed", "bananas", ":", "as", "ripe", "as", "possible"]

    >>> tokenize("1.5 kg bananas, mashed")
    ["1.5", "kg", "bananas", ",", "mashed"]

    >>> tokenize("Freshly grated Parmesan cheese, for garnish.")
    ["Freshly", "grated", "Parmesan", "cheese", ",", "for", "garnish", "."]

    >>> tokenize("2 onions, finely chopped*")
    ["2", "onions", ",", "finely", "chopped", "*"]
    """
    tokens = [
        PUNCTUATION_TOKENISER.split(tok)
        for tok in WHITESPACE_TOKENISER.findall(sentence)
    ]
    flattened = [tok for tok in chain.from_iterable(tokens) if tok]

    # Second pass to separate full stops from end of tokens
    tokens = [FULL_STOP_TOKENISER.split(tok) for tok in flattened]

    return [tok for tok in chain.from_iterable(tokens) if tok]


@lru_cache(maxsize=512)
def stem(token: str) -> str:
    """Stem function with cache to improve performance.

    The stem of a word output by the PorterStemmer is always the same, so we can
    cache the result the first time and return that for subsequent future calls
    without the need to do all the processing again.

    Parameters
    ----------
    token : str
        Token to stem

    Returns
    -------
    str
        Stem of token
    """
    return STEMMER.stem(token)


def pos_tag(tokens: list[str]) -> list[tuple[str]]:
    """Re-implmentation of nltk.pos_tag to avoid having to load the weights each time
    the function is called.

    Parameters
    ----------
    tokens : list[str]
        List of tokens to tag.

    Returns
    -------
    list[tuple[str]]
        List of (token, tag) tuples.
    """
    return TAGGER.tag(tokens)


def pluralise_units(sentence: str) -> str:
    """Pluralise units in the sentence.

    Use the same UNITS dictionary as PreProcessor to make any units in sentence plural

    Parameters
    ----------
    sentence : str
        Input sentence

    Returns
    -------
    str
        Input sentence with any words in the values of UNITS replaced with their plural
        version

    Examples
    --------
    >>> pluralise_units("2 bag")
    '2 bags'

    >>> pluralise_units("13 ounce")
    '13 ounces'

    >>> pluralise_units("1.5 loaf bread")
    '1.5 loaves bread'
    """
    for plural, singular in UNITS.items():
        sentence = re.sub(rf"\b({singular})\b", f"{plural}", sentence)

    return sentence


def convert_to_pint_unit(unit: str, imperial_units: bool = False) -> str | pint.Unit:
    """Convert a unit to a pint.Unit object, if possible.

    If the unit is not found in the pint Unit Registry, just return the input unit.

    Parameters
    ----------
    unit : str
        Unit to find in pint Unit Registry
    imperial_units : bool, optional
        If True, use imperial units instead of US customary units for the following:
        fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.

    Returns
    -------
    str | pint.Unit

    Examples
    --------
    >>> convert_to_pint_unit("")
    ''

    >>> convert_to_pint_unit("oz")
    <Unit('ounce')>

    >>> convert_to_pint_unit("fl oz")
    <Unit('fluid_ounce')>

    >>> convert_to_pint_unit("cup", imperial_units=True)
    <Unit('imperial_cup')>
    """
    if "-" in unit:
        # When checking if a unit is in the unit registry, pint will parse any
        # '-' as a subtraction and attempt to evaluate it, causing an exception.
        # Since no pint.Unit can contain a '-', we'll just return early with
        # the string.
        return unit

    if unit.lower() in MISINTERPRETED_UNITS:
        # Special cases to prevent pint interprettng units incorrect
        # e.g. pinch != pico-inch
        return unit

    # Apply replacements to ensure correct matches in pint Unit Registry
    for regex, replacement in UNIT_REPLACEMENTS:
        unit = regex.sub(replacement, unit)

    if imperial_units:
        for original, replacement in IMPERIAL_UNITS.items():
            unit = unit.replace(original, replacement)

    # If unit not empty string and found in Unit Registry,
    # return pint.Unit object for unit
    if unit != "" and unit in UREG:
        return UREG(unit).units

    return unit


def combine_quantities_split_by_and(text: str) -> str:
    """Combine fractional quantities split by 'and' into single value.

    Parameters
    ----------
    text : str
        Text to combine

    Returns
    -------
    str
        Text with split fractions replaced with
        single decimal value.

    Examples
    --------
    >>> combine_quantities_split_by_and("1 and 1/2 tsp fine grain sea salt")
    "1.5 tsp fine grain sea salt"

    >>> combine_quantities_split_by_and("1 and 1/4 cups dark chocolate morsels")
    "1.25 cups dark chocolate morsels"
    """
    matches = FRACTION_SPLIT_AND_PATTERN.findall(text)

    for match in matches:
        combined_quantity = float(Fraction(match[1]) + Fraction(match[2]))
        rounded = round(combined_quantity, 3)
        text = text.replace(match[0], f"{rounded:g}")

    return text


def replace_string_range(text: str) -> str:
    """Replace range in the form "<num> to <num" with range "<num>-<num>".

    For example
    -----------
    1 to 2 -> 1-2
    8.5 to 12.5 -> 8.5-12.5
    16- to 9-

    Parameters
    ----------
    text : str
        Text to replace within

    Returns
    -------
    str
        Text with string ranges replaced with standardised range

    Examples
    --------
    >>> p = PreProcessor("")
    >>> p._replace_string_range("1 to 2 mashed bananas")
    "1-2 mashed bananas"

    >>> p = PreProcessor("")
    >>> p._replace_string_range("5- or 6- large apples")
    "5-6- large apples"
    """
    return STRING_RANGE_PATTERN.sub(r"\1-\5", text)


def ingredient_amount_factory(
    quantity: str,
    unit: str,
    text: str,
    confidence: float,
    starting_index: int,
    APPROXIMATE: bool = False,
    SINGULAR: bool = False,
    string_units: bool = False,
    imperial_units: bool = False,
) -> IngredientAmount:
    """Create ingredient amount object from parts.

    This function converts the inputs into an IngredientAmout object, with some
    additional processing:
    * Pluralise units, if appropriate
    * Convert the quantity to a float, if appropriate
    * Set the quantity_max value
    * Set the RANGE and MULTIPLIER flags, if appropriate

    Parameters
    ----------
    quantity : str
        Quantity of amount
    unit : str
        Unit of amount
    text : str
        Combined quantity and amount e.g. "1 cup"
    confidence : float
        Average confidence of all tokens contributing to amount
    starting_index : int
        Starting index of first token contributing to amount
    APPROXIMATE : bool, optional
        When True, indicates that the amount is approximate.
        Default is False.
    SINGULAR : bool, optional
        When True, indicates if the amount refers to a singular item of the ingredient.
        Default is False.
    string_units : bool, optional
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Default is False.
    imperial_units : bool, optional
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.

    Returns
    -------
    IngredientAmount
    """
    RANGE = False
    MULTIPLIER = False

    if is_float(quantity):
        # If float, set quantity_max = quantity
        _quantity = float(quantity)
        quantity_max = _quantity
    elif is_range(quantity):
        # If range, set quantity to min of range, set quantity_max to max
        # of range, set RANGE flag to True
        range_parts = [float(x) for x in quantity.split("-")]
        _quantity = min(range_parts)
        quantity_max = max(range_parts)
        RANGE = True
    elif quantity.endswith("x"):
        # If multiplier, set quantity and quantity_max to value without 'x', and
        # set MULTIPLER flag.
        _quantity = float(quantity[:-1])
        quantity_max = _quantity
        MULTIPLIER = True
    else:
        _quantity = quantity
        # Fallback to setting quantity_max to quantity
        quantity_max = _quantity

    _unit = unit
    # Convert unit to pint.Unit
    if not string_units:
        # If the unit is recognised in the pint unit registry, use
        # a pint.Unit object instead of a string. This has the benefit
        # of simplifying alternative unit representations into a single
        # common representation
        _unit = convert_to_pint_unit(_unit, imperial_units)

    # Pluralise unit as necessary
    if _quantity != 1 and _quantity != "" and not RANGE:
        text = pluralise_units(text)
        if isinstance(_unit, str):
            _unit = pluralise_units(_unit)

    return IngredientAmount(
        quantity=_quantity,
        quantity_max=quantity_max,
        unit=_unit,
        text=text,
        confidence=round(confidence, 6),
        starting_index=starting_index,
        APPROXIMATE=APPROXIMATE,
        SINGULAR=SINGULAR,
        RANGE=RANGE,
        MULTIPLIER=MULTIPLIER,
    )

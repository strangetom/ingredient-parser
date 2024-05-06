#!/usr/bin/env python3

import re
from functools import lru_cache
from itertools import chain

import pint
from nltk.stem.porter import PorterStemmer

from .._common import is_float, is_range
from ..dataclasses import IngredientAmount
from ._constants import UNITS

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


STEMMER = PorterStemmer()

# Define regular expressions used by tokenizer.
# Matches one or more whitespace characters
WHITESPACE_TOKENISER = re.compile(r"\S+")
# Matches and captures one of the following: ( ) [ ] { } , " / : ;
PUNCTUATION_TOKENISER = re.compile(r"([\(\)\[\]\{\}\,/:;])")
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

    # Define some replacements to ensure correct matches in pint Unit Registry
    replacements = {
        "fl oz": "floz",
        "fluid oz": "fluid_ounce",
        "fl ounce": "fluid_ounce",
        "fluid ounce": "fluid_ounce",
    }
    for original, replacement in replacements.items():
        unit = unit.replace(original, replacement)

    if imperial_units:
        for original, replacement in IMPERIAL_UNITS.items():
            unit = unit.replace(original, replacement)

    # If unit not empty string and found in Unit Registry,
    # return pint.Unit object for unit
    if unit != "" and unit in UREG:
        return UREG(unit).units

    return unit


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

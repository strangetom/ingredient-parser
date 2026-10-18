#!/usr/bin/env python3

import re
from fractions import Fraction
from functools import lru_cache
from typing import Literal, cast

import pint
from nltk.stem.snowball import EnglishStemmer

from .._common import (
    UREG,
    intermediate_fraction_to_unicode,
    is_float,
    is_fraction,
    is_range,
)
from ..dataclasses import IngredientAmount
from ..perceptron import PerceptronTagger
from ._constants import (
    FLATTENED_UNITS_LIST,
    STRING_NUMBERS,
    UNIT_SYNONYMS,
    UNITS,
    UNITS_RINDEX,
)
from ._loaders import load_ingredient_tagdict
from ._regex import (
    FRACTION_SPLIT_AND_PATTERN,
    PLURAL_UNIT_PATTERN,
    STRING_RANGE_PATTERN,
)

# List of volumetric units that have different country versions.
VOLUMETRIC_UNITS_W_ALTERNATIVES = {
    "cup": {
        "imperial": "imperial_cup",
        "japanese": "jp_cup",
        "australian": "metric_cup",
        "metric": "metric_cup",
    },
    "floz": {
        "imperial": "imperial_fluid_ounce",
    },
    "fluid_ounce": {
        "imperial": "imperial_fluid_ounce",
    },
    "quart": {
        "imperial": "imperial_quart",
    },
    "pint": {
        "imperial": "imperial_pint",
        "australian": "aus_pint",
    },
    "gallon": {
        "imperial": "imperial_gallon",
    },
    "tablespoon": {
        "imperial": "imperial_tablespoon",
        "japanese": "metric_tablespoon",
        "australian": "aus_tablespoon",
        "metric": "metric_tablespoon",
    },
    "tbsp": {
        "imperial": "imperial_tablespoon",
        "japanese": "metric_tablespoon",
        "australian": "aus_tablespoon",
        "metric": "metric_tablespoon",
    },
    "teaspoon": {
        "imperial": "imperial_teaspoon",
        "japanese": "metric_teaspoon",
        "australian": "metric_teaspoon",
        "metric": "metric_teaspoon",
    },
    "tsp": {
        "imperial": "imperial_teaspoon",
        "japanese": "metric_teaspoon",
        "australian": "metric_teaspoon",
        "metric": "metric_teaspoon",
    },
    "ounce": {
        "imperial": "imperial_ounce",
    },
    "oz": {
        "imperial": "imperial_ounce",
    },
    "pound": {
        "imperial": "imperial_pound",
    },
    "lb": {
        "imperial": "imperial_pound",
    },
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
    "unit",  # micronit (micro netwon inch)
    "units",
    "fat",  # femto-technical-atmosphere
]

# List of unit replacements so that these units get converted to the correct pint
# units. Each entry is a tuple of a pre-compliled regex, and the replacement value.
UNIT_REPLACEMENTS = [
    (re.compile(r"\b(fl oz)\b"), "floz"),
    (re.compile(r"\b(fluid oz)\b"), "fluid_ounce"),
    (re.compile(r"\b(fl ounce)\b"), "fluid_ounce"),
    (re.compile(r"\b(fluid ounce)\b"), "fluid_ounce"),
    (re.compile(r"\b(C)\b", re.I), "cup"),
    (re.compile(r"\b(qt)\b"), "quart"),
    (re.compile(r"\b(Cl)\b"), "centiliter"),
    (re.compile(r"\b(G)\b", re.I), "gram"),
    (re.compile(r"\b(Ml)\b"), "milliliter"),
    (re.compile(r"\b(Mm)\b"), "millimeter"),
    (re.compile(r"\b(Pt)\b"), "pint"),
    (re.compile(r"\b(Tb)\b", re.I), "tablespoon"),
    (re.compile(r"\b(T)\b"), "tablespoon"),
    (re.compile(r"\b(t)\b"), "teaspoon"),
    (re.compile(r"\b(Ts)\b"), "tablespoon"),
    (re.compile(r"\b(ts)\b"), "teaspoon"),
]

STEMMER = EnglishStemmer()


@lru_cache(maxsize=2048)
def stem(token: str) -> str:
    """Stem function with cache to improve performance.

    The stem of a word output by the stemmer is always the same, so we can
    cache the result the first time and return that for subsequent future calls
    without the need to do all the processing again.

    Parameters
    ----------
    token : str
        Token to stem.

    Returns
    -------
    str
        Stem of token.
    """
    return STEMMER.stem(token)


@lru_cache
def get_pos_tagger() -> PerceptronTagger:
    """Cached function to return part of speech tagger.

    The returned part of speech tagger is the default English part of speech tagger from
    NLTK, but with it's tagdict updated with addition ingredient sentence specific
    entries.

    Returns
    -------
    PerceptronTagger
        PerceptronTagger part of speech tagger object.
    """
    tagger = PerceptronTagger()
    ingredient_tagdict = load_ingredient_tagdict()
    tagger.tagdict.update(ingredient_tagdict)
    return tagger


def pos_tag(tokens: list[str]) -> list[tuple[str, str]]:
    """Tag tokens with parts of speech.

    This is a modification of NLTK's default part of speech tagging functionality which
    extends the tagdict with additional, ingredient sentence specific entries.
    The tagdict is a dict of token:tag pairs which bypass the part of speech tagging
    model.

    Parameters
    ----------
    tokens : list[str]
        List of tokens.

    Returns
    -------
    list[tuple[str, str]]
        List of (token, tag) pairs.
    """
    tagger = get_pos_tagger()
    return tagger.tag(tokens)


@lru_cache(maxsize=5_000)
def is_numeric(token: str) -> bool:
    """Return True if token is numeric.

    This function is cached because it is called for each token and some tokens occur
    frequently in recipe ingredient sentences, so there's no point redoing the
    calculation in full each time a repeat token is encountered.

    Parameters
    ----------
    token : str
        Token to check.

    Returns
    -------
    bool
        True if token is numeric, else False.

    Examples
    --------
    >>> is_numeric("1")
    True

    >>> is_numeric("1-2")
    True

    >>> is_numeric("dozen")
    True

    >>> is_numeric("1x")
    True

    >>> is_numeric("three")
    True

    >>> is_numeric("#1$2")
    True

    >>> is_numeric("beef")
    False
    """
    if token == "00":
        # Special cases of digits that don't represent numbers
        return False

    lower = token.lower()
    if lower in STRING_NUMBERS or lower == "dozen":
        # Numbers written in words are considered numeric.
        return True

    if token.endswith("x"):
        # Strip trailing x so we can check the remaining token.
        token = token[:-1]

    if is_fraction(token):
        # Fraction tokens e.g. #1$4 or 1#2$3
        return True

    if "-" in token[1:]:
        # Check for ranges, but not negative numbers
        parts = token.split("-")
        return all(is_numeric(part) for part in parts)

    return is_float(token)


def pluralise_known_unit(s: str) -> str:
    """Substitute singular form of known units in input string with plural form.

    Parameters
    ----------
    s : str
        String to perform substitution on.

    Returns
    -------
    str
        Input string with singular units substituted with plural forms.
    """

    def singular_to_plural(match: re.Match) -> str:
        """Convert singular form of unit to plural form.

        If, for any reason, the captured singular form does not occur in UNITS_RINDEX,
        return the singular form.

        Parameters
        ----------
        match : re.Match
            Regular expression match capturing singular form unit.

        Returns
        -------
        str
            Plural form of captured unit.
        """
        singular_unit: str = match.group(0)
        return UNITS_RINDEX.get(singular_unit, singular_unit)

    return PLURAL_UNIT_PATTERN.sub(singular_to_plural, s)


def pluralise_units(sentence: str, custom_units: dict[str, str]) -> str:
    """Pluralise units in the sentence.

    Parameters
    ----------
    sentence : str
        Input sentence.
    custom_units : dict[str, str]
        Dict of custom singular: plural pairs of units

    Returns
    -------
    str
        Input sentence with any words in the values of UNITS replaced with their plural
        version.

    Examples
    --------
    >>> pluralise_units("2 bag", {})
    '2 bags'

    >>> pluralise_units("13 ounce", {})
    '13 ounces'

    >>> pluralise_units("1.5 loaf bread", {})
    '1.5 loaves bread'

    >>> pluralise_units("2 blarg bread", {"blargs": "blarg"})
    '2 blargs bread'
    """
    sentence = pluralise_known_unit(sentence)

    def singular_to_plural(match: re.Match) -> str:
        """Convert singular form of unit to plural form.

        If, for any reason, the captured singular form does not occur in UNITS_RINDEX,
        return the singular form.

        Parameters
        ----------
        match : re.Match
            Regular expression match capturing singular form unit.

        Returns
        -------
        str
            Plural form of captured unit.
        """
        singular_unit: str = match.group(0)
        return custom_units.get(singular_unit, singular_unit)

    return PLURAL_UNIT_PATTERN.sub(singular_to_plural, sentence)


@lru_cache(maxsize=512)
def convert_to_pint_unit(
    unit: str,
    volumetric_units_system: Literal[
        "us_customary", "imperial", "metric", "australian", "japanese"
    ] = "us_customary",
) -> str | pint.Unit:
    """Convert a unit to a pint.Unit object, if possible.

    If the unit is not found in the pint Unit Registry, just return the input unit.

    Parameters
    ----------
    unit : str
        Unit to find in pint Unit Registry.
    volumetric_units_system : Literal[
        "us_customary", "imperial", "metric", "australian", "japanese"
    ], optional
        Sets the units system for volumetric measurements, like "cup" or "tablespoon".
        Default is "us_customary".

    Returns
    -------
    str | pint.Unit
        Pint.Unit object if unit found in Pint unit registry, otherwise return input
        unit.

    Examples
    --------
    >>> convert_to_pint_unit("")
    ''

    >>> convert_to_pint_unit("oz")
    <Unit('ounce')>

    >>> convert_to_pint_unit("fl oz")
    <Unit('fluid_ounce')>

    >>> convert_to_pint_unit("cup", volumetric_units_system="imperial")
    <Unit('imperial_cup')>
    """
    if "-" in unit:
        # When checking if a unit is in the unit registry, pint will parse any
        # '-' as a subtraction and attempt to evaluate it, causing an exception.
        # Since no pint.Unit can contain a '-', we'll just return early with
        # the string.
        return unit

    if '"' in unit or "'" in unit:
        # If the unit contains " or ', this will cause a TokenError when pint tries to
        # parse the unit.
        # Since there aren't any pint units that contain these characters, just return
        # early here to avoid the problem.
        return unit

    original_unit = unit

    if unit.lower() in MISINTERPRETED_UNITS:
        # Special cases to prevent pint interpreting units incorrectly
        # e.g. pinch != pico-inch
        return original_unit

    # Apply replacements to ensure correct matches in pint Unit Registry
    for regex, replacement in UNIT_REPLACEMENTS:
        unit = regex.sub(replacement, unit)

    # If the unit is not in lowercase, convert to lowercase.
    # Keep the original unit so we can return it as provided to this function if we
    # can't convert to a pint.Unit object.
    if unit != unit.lower():
        unit = unit.lower()
    if (
        unit in VOLUMETRIC_UNITS_W_ALTERNATIVES
        and volumetric_units_system != "us_customary"
    ):
        # Convert unit to country specific version e.g. cups -> imperial_cup if a
        # replacement is defined.
        if alt := VOLUMETRIC_UNITS_W_ALTERNATIVES[unit].get(volumetric_units_system):
            unit = unit.replace(unit, alt)

    if unit == "":
        return original_unit

    # Try to return unit from Unit Registry otherwise return original unit.
    try:
        return cast(pint.Unit, UREG(unit).units)
    except pint.UndefinedUnitError:
        return original_unit


@lru_cache(maxsize=512)
def is_unit_synonym(unit1: str, unit2: str) -> bool:
    """Check if given units are synonyms.

    Parameters
    ----------
    unit1 : str
        First unit to check.
    unit2 : str
        Second unit to check.

    Returns
    -------
    bool
        True if units are synonyms.

    Examples
    --------
    >>> is_unit_synonym("oz", "ounce")
    True

    >>> is_unit_synonym("cups", "c")
    True

    >>> is_unit_synonym("kg", "g")
    False
    """
    # If not in units list, then cannot be unit synonyms
    if unit1 not in FLATTENED_UNITS_LIST or unit2 not in FLATTENED_UNITS_LIST:
        return False

    # Make singular if plural
    unit1 = UNITS.get(unit1, unit1)
    unit2 = UNITS.get(unit2, unit2)

    for synonyms in UNIT_SYNONYMS:
        if unit1 in synonyms and unit2 in synonyms:
            return True

    return False


def combine_quantities_split_by_and(text: str) -> str:
    """Combine fractional quantities split by 'and' into single value.

    Parameters
    ----------
    text : str
        Text to combine.

    Returns
    -------
    str
        Text with split fractions replaced with single value.

    Examples
    --------
    >>> combine_quantities_split_by_and("1 and 1/2 tsp fine grain sea salt")
    "1#1$2 tsp fine grain sea salt"

    >>> combine_quantities_split_by_and("1 and 1/4 cups dark chocolate morsels")
    "1#1$4 cups dark chocolate morsels"
    """
    matches = FRACTION_SPLIT_AND_PATTERN.findall(text)

    for match in matches:
        replacement = match[1] + "#" + match[2].replace("/", "$")
        text = text.replace(match[0], replacement)

    return text


def replace_string_range(text: str) -> str:
    """Replace range in the form "<num> to <num" with range "<num>-<num>".

    For example:
    1 to 2 -> 1-2
    8.5 to 12.5 -> 8.5-12.5
    16- to 9- -> 19-9

    Parameters
    ----------
    text : str
        Text to replace within.

    Returns
    -------
    str
        Text with string ranges replaced with standardised range.

    Examples
    --------
    >>> replace_string_range("1 to 2 mashed bananas")
    "1-2 mashed bananas"

    >>> replace_string_range("5- or 6- large apples")
    "5-6- large apples"
    """
    return STRING_RANGE_PATTERN.sub(r"\1-\5", text)


@lru_cache(maxsize=512)
def to_frac(token: str) -> Fraction:
    """Convert a QTY token into a Fraction object.

    Parameters
    ----------
    token : str
        Token with QTY label.

    Returns
    -------
    Fraction
        Fraction object representing the same quantity as token.
    """
    if is_fraction(token):
        fraction_parts = [p.replace("$", "/") for p in token.split("#") if p]
        return sum((Fraction(p) for p in fraction_parts), start=Fraction(0))

    return Fraction(token)


def ingredient_amount_factory(
    quantity: str,
    unit: str,
    text: str,
    confidence: float,
    starting_index: int,
    APPROXIMATE: bool = False,
    SINGULAR: bool = False,
    PREPARED_INGREDIENT: bool = False,
    string_units: bool = False,
    volumetric_units_system: Literal[
        "us_customary", "imperial", "metric", "australian", "japanese"
    ] = "us_customary",
    custom_units: dict[str, str] | None = None,
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
        Quantity of amount.
    unit : str
        Unit of amount.
    text : str
        Combined quantity and amount e.g. "1 cup".
    confidence : float
        Average confidence of all tokens contributing to amount.
    starting_index : int
        Starting index of first token contributing to amount.
    APPROXIMATE : bool, optional
        When True, indicates that the amount is approximate.
        Default is False.
    SINGULAR : bool, optional
        When True, indicates if the amount refers to a singular item of the ingredient.
        Default is False.
    PREPARED_INGREDIENT : bool, optional
        When True, indicates the amount applies to the prepared ingredient.
        When False, indicates the amount applies to the ingredient before preparation.
        Default is False.
    string_units : bool, optional
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Default is False.
    volumetric_units_system : Literal[
        "us_customary", "imperial", "metric", "australian", "japanese"
    ], optional
        Set the country standard for volumetric units such as cups, tablespoon.
        This has no effect is string_units=True.

    Returns
    -------
    IngredientAmount
        IngredientAmount object for given inputs.
    """
    if custom_units is None:
        custom_units = {}

    RANGE = False
    MULTIPLIER = False

    if quantity.endswith("x"):
        # If multiplier, set MULTIPLER flag then strip "x" suffix and process quantity
        # as normal.
        MULTIPLIER = True
        quantity = quantity.removesuffix("x")

    if is_range(quantity):
        # If range, set quantity to min of range, set quantity_max to max
        # of range, set RANGE flag to True
        range_parts = [to_frac(x) for x in quantity.split("-")]
        _quantity = min(range_parts)
        quantity_max = max(range_parts)
        RANGE = True
    elif is_float(quantity) or is_fraction(quantity):
        # If float or fraction, set quantity_max = quantity
        _quantity = to_frac(quantity)
        quantity_max = _quantity
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
        _unit = convert_to_pint_unit(_unit, volumetric_units_system)

    # Pluralise unit as necessary.
    if (_quantity != 1 and _quantity != "" and not RANGE) or (
        quantity_max != 1 and quantity_max != "" and RANGE
    ):
        text = pluralise_units(text, custom_units)
        if isinstance(_unit, str):
            _unit = pluralise_units(_unit, custom_units)

    # Fix up text:
    # 1. Replace intermediate fractions with unicode fraction
    # 2. Remove additional leading and trailing spaces
    # 3. Remove additional spaces in fraction ranges
    text = intermediate_fraction_to_unicode(text.strip())
    text = text.replace("- ", "-")

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
        PREPARED_INGREDIENT=PREPARED_INGREDIENT,
    )

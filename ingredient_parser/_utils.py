#!/usr/bin/env python3

import collections
import os
import platform
import re
import subprocess
from importlib.resources import as_file, files
from itertools import islice
from typing import Iterator

import pint
from nltk import data, download

from ._constants import UNITS
from .preprocess.regex import RANGE_PATTERN

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
        return pint.Unit(unit)

    return unit


def consume(iterator: Iterator, n: int) -> None:
    """Advance the iterator n-steps ahead. If n is none, consume entirely.
    See consume from https://docs.python.org/3/library/itertools.html#itertools-recipes

    Parameters
    ----------
    iterator : Iterator
        Iterator to advance.
    n : int
        Number of iterations to advance by.

    Examples
    --------
    >>> it = iter(range(10))
    >>> consume(it, 3)
    >>> next(it)
    3

    >>> it = iter(range(10))
    >>> consume(it, None)
    >>> next(it)
    StopIteration
    """
    if n is None:
        # Feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # Advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)


def show_model_card() -> None:
    """Open model card in default application."""
    with as_file(files(__package__) / "ModelCard.md") as p:
        if platform.system() == "Darwin":  # macOS
            subprocess.call(("open", p))
        elif platform.system() == "Windows":  # Windows
            os.startfile(p)
        else:  # linux variants
            subprocess.call(("xdg-open", p))


def download_nltk_resources() -> None:
    """Check if required nltk resources can be found and if not, download them."""
    try:
        data.find(
            "taggers/averaged_perceptron_tagger/averaged_perceptron_tagger.pickle"
        )
    except LookupError:
        print("Downloading required NLTK resource: averaged_perceptron_tagger")
        download("averaged_perceptron_tagger")


def is_float(value: str) -> bool:
    """Check if the value can be converted to a float.

    Parameters
    ----------
    value : str
        Value to check

    Returns
    -------
    bool
        True if the value can be converted to float, else False

    Examples
    --------
    >>> is_float("3")
    True

    >>> is_float("2.5")
    True

    >>> is_float("1-2")
    False
    """
    try:
        _ = float(value)
        return True
    except ValueError:
        return False


def is_range(value: str) -> bool:
    """Check if the value is a range e.g. 100-200.

    Parameters
    ----------
    value : str
        Value to check

    Returns
    -------
    bool
        True if the value is a range, else False

    Examples
    --------
    >>> is_range("1-2")
    True

    >>> is_float("100-500")
    True

    >>> is_float("1")
    False
    """
    return RANGE_PATTERN.match(value)

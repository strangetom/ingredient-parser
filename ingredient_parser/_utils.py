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

UREG = pint.UnitRegistry()


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


def convert_to_pint_unit(unit: str) -> str | pint.Unit:
    """Convert a unit to a pint.Unit object, if possible.
    If the unit is not found in the pint Unit Registry, just return the input unit.

    Parameters
    ----------
    unit : str
        Unit to find in pint Unit Registry

    Returns
    -------
    str | pint.Unit
        pint.Unit object if unit found in Unit Registry, else input string

    Examples
    --------
    >>> convert_to_pint_unit("")
    ''

    >>> convert_to_pint_unit("oz")
    <Unit('ounce')>

    >>> convert_to_pint_unit("fl oz)
    <Unit('fluid_ounce')>
    """
    # Define some replacements to ensure correct matches in pint Unit Registry
    replacements = {
        "fl oz": "floz",
        "fluid oz": "fluid_ounce",
        "fl ounce": "fluid_ounce",
        "fluid ounce": "fluid_ounce",
    }
    for original, replacement in replacements.items():
        unit = unit.replace(original, replacement)

    # If unit not empty string and found in Unit Registry, return pint.Unit object
    # for unit
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

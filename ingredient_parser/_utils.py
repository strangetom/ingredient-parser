#!/usr/bin/env python3

import collections
import os
import platform
import re
import subprocess
from importlib.resources import as_file, files
from itertools import islice
from typing import Iterator

from nltk import data, download

from ._constants import UNITS


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

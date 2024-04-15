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

# Regex pattern for matching a numeric range e.g. 1-2, 2-3.
RANGE_PATTERN = re.compile(r"\d+\s*[\-]\d+")


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
    return RANGE_PATTERN.match(value) is not None

#!/usr/bin/env python3

import collections
import os
import platform
import re
import subprocess
from importlib.resources import as_file, files
from itertools import groupby, islice
from operator import itemgetter
from typing import Generator, Iterator

import nltk

SUPPORTED_LANGUAGES = ["en"]

# Regex pattern for matching a numeric range e.g. 1-2, 2-3, #1$2-1#3$4.
RANGE_PATTERN = re.compile(r"^[\d\#\$]+\s*[\-][\d\#\$]+$")


def consume(iterator: Iterator, n: int | None) -> None:
    """Advance the iterator n-steps ahead. If n is none, consume entirely.

    See consume from https://docs.python.org/3/library/itertools.html#itertools-recipes

    Parameters
    ----------
    iterator : Iterator
        Iterator to advance.
    n : int | None
        Number of iterations to advance by.
        If None, consume entire iterator.

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


def group_consecutive_idx(idx: list[int]) -> Generator[Iterator[int], None, None]:
    """Yield groups of consecutive indices.

    Given a list of integers, yield groups of integers where the value of each in a
    group is adjacent to the previous element's value.

    Parameters
    ----------
    idx : list[int]
        List of indices

    Yields
    ------
    list[list[int]]
        List of lists, where each sub-list contains consecutive indices

    Examples
    --------
    >>> groups = group_consecutive_idx([0, 1, 2, 4, 5, 6, 8, 9])
    >>> [list(g) for g in groups]
    [[0, 1, 2], [4, 5, 6], [8, 9]]
    """
    for _, g in groupby(enumerate(idx), key=lambda x: x[0] - x[1]):
        yield map(itemgetter(1), g)


def show_model_card(lang: str = "en") -> None:
    """Open model card for specified langauge in default application.

    Parameters
    ----------
    lang : str, optional
        Selected language to open model card for.
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f'Unsupported language "{lang}"')

    with as_file(files(__package__) / lang / f"ModelCard.{lang}.md") as p:
        if platform.system() == "Darwin":  # macOS
            subprocess.call(("open", p))
        elif platform.system() == "Windows":  # Windows
            os.startfile(p)
        else:  # linux variants
            subprocess.call(("xdg-open", p))


def download_nltk_resources() -> None:
    """Check if required nltk resources can be found and if not, download them."""
    try:
        nltk.data.find(
            "taggers/averaged_perceptron_tagger_eng/averaged_perceptron_tagger_eng.classes.json"
        )
        nltk.data.find(
            "taggers/averaged_perceptron_tagger_eng/averaged_perceptron_tagger_eng.tagdict.json"
        )
        nltk.data.find(
            "taggers/averaged_perceptron_tagger_eng/averaged_perceptron_tagger_eng.weights.json"
        )
    except LookupError:
        print("Downloading required NLTK resource: averaged_perceptron_tagger_eng")
        nltk.download("averaged_perceptron_tagger_eng")


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

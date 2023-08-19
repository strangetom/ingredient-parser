#!/usr/bin/env python3

import os
import platform
import re
import subprocess
from importlib.resources import as_file, files
from itertools import groupby
from operator import itemgetter
from typing import Generator, Iterator

from ._constants import UNITS, UNIT_MODIFIERS


def find_idx(labels: list[str], key: str) -> list[int]:
    """Find indices of elements in list matching key.

    Return the indices of every element in the input list whose value is equal to the
    given key.
    If there is an element with the COMMA label before an element with label key,
    include this in the list of matched indices

    Parameters
    ----------
    labels : list[str]
        List to search for key in
    key : str
        Key to find in list

    Returns
    -------
    list[int]
        List of indices of elements with label key
        Includes elements with label COMMA if the element is previous to a key label

    Examples
    -------
    >>> find_idx(["QTY", "UNIT", "NAME", "NAME", "COMMENT", "COMMENT"], "NAME")
    [2, 3]

    >>> find_idx(["QTY", "UNIT", "NAME", "COMMA", "COMMENT", "COMMENT"], "COMMENT")
    [4, 5, 6]
    """
    matches = []
    prev_el = ""
    for idx, el in enumerate(labels):
        if el == key:
            if prev_el == "COMMA":
                matches.append(idx - 1)
            matches.append(idx)

        prev_el = el
    return matches


def join_adjacent(tokens: list[str], idx: list[int]) -> str | list[str]:
    """Join tokens with adjacent indices in idx list into strings.

    Given a list of tokens and list of indices for token with a particular value,
    join all the token with adjacent indices in the idx list into space seperated
    strings.

    If idx is an empty list, return an empty string.

    If there is only one group of adjacent values in idx, return a string.

    If there are multiple groups of adjacent values in idx, return a list of strings.

    Parameters
    ----------
    tokens : list[str]
        List of ingredient sentence tokens
    idx : list[int]
        Indices of tokens to group and join

    Returns
    -------
    str | list[str]
        List of strings, with adjacent tokens joined
        If the list only contains one element, return as a string

    Examples
    --------
    >>> join_adjacent(["a", "b", "c", "d", "e", "f"], [0, 1, 3, 4, 5])
    ['a b', 'd e f']
    """
    grouped = []
    for group in group_consecutive_idx(idx):
        joined = " ".join([tokens[idx] for idx in group])
        grouped.append(joined)

    if len(grouped) == 0:
        return ""
    elif len(grouped) == 1:
        return grouped[0]
    else:
        return grouped


def average(labels: list[str], scores: list[float], key: str) -> float:
    """Average the scores for labels matching key

    Given a particular label (key), find the indices of the labels that have that key.
    Then use those indices to take the average of the associated score in the scores
    input.

    Parameters
    ----------
    labels : list[str]
        List of labels to search key for
    scores : list[float]
        Confidence score for each label
    key : str
        Key to calculate confidence for

    Returns
    -------
    float
        Confidence, average of all labels with given key
    """
    score_list = []
    for idx, el in enumerate(labels):
        if el == key:
            score_list.append(scores[idx])

    if len(score_list) == 0:
        return 0

    average = sum(score_list) / len(score_list)
    return round(average, 4)


def show_model_card() -> None:
    """Open model card in default application."""
    with as_file(files(__package__) / "ModelCard.md") as p:
        if platform.system() == "Darwin":  # macOS
            subprocess.call(("open", p))
        elif platform.system() == "Windows":  # Windows
            os.startfile(p)
        else:  # linux variants
            subprocess.call(("xdg-open", p))

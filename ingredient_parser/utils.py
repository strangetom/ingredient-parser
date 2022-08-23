#!/usr/bin/env python3

import argparse
import json
import os
import pickle
from itertools import groupby
from operator import itemgetter
from typing import Any, Dict, Generator, Iterator, List, Union


def find_idx(labels: List[str], key: str) -> List[int]:
    """Find indices of elements matching key in list

    Parameters
    ----------
    labels : List[str]
        List to search for key in
    key : str
        Key to find in list
    """
    matches = []
    for idx, el in enumerate(labels):
        if el == key:
            matches.append(idx)
    return matches


def group_consecutive_idx(idx: List[int]) -> Generator[Iterator[int], None, None]:
    """Yield groups of consecutive indices

    Parameters
    ----------
    idx : List[int]
        List of indices

    Yields
    ------
    List[List[int]]
        List of lists, where each sub-list contains consecutive indices
    """
    for k, g in groupby(enumerate(idx), key=lambda x: x[0] - x[1]):
        yield map(itemgetter(1), g)


def join_adjacent(tokens: List[str], idx: List[int]) -> Union[str, List[str]]:
    """Join adjacent tokens with same label into space separated string

    Parameters
    ----------
    tokens : List[str]
        List of ingredient sentence tokens
    idx : List[int]
        Indices of tokens to group and join

    Returns
    -------
    Union(str, List[str])
        List of strings, with adjacent tokens joined
        If the list only contains one element, return as a string
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


def average(labels: List[str], scores: List[float], key: str) -> float:
    """Average the scores for labels matching key

    Parameters
    ----------
    labels : List[str]
        List of labels to search key for
    scores : List[float]
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

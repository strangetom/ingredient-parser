#!/usr/bin/env python3

import re
from itertools import groupby
from operator import itemgetter
from typing import Generator, Iterator, List, Union

from ._constants import UNITS


def find_idx(labels: List[str], key: str) -> List[int]:
    """Find indices of elements in list matching key.

    Return the indices of every element in the input list whose value is equal to the
    given key.
    If there is an element with the COMMA label before an element with label key,
    include this in the list of matched indices

    Parameters
    ----------
    labels : List[str]
        List to search for key in
    key : str
        Key to find in list

    Returns
    -------
    List[int]
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


def group_consecutive_idx(idx: List[int]) -> Generator[Iterator[int], None, None]:
    """Yield groups of consecutive indices

    Given a list of integers, yield groups of integers where the value of each in a
    group is adjacent to the previous element's value.

    Parameters
    ----------
    idx : List[int]
        List of indices

    Yields
    ------
    List[List[int]]
        List of lists, where each sub-list contains consecutive indices

    Examples
    -------
    >>> groups = group_consecutive_idx([0, 1, 2, 4, 5, 6, 8, 9])
    >>> [list(g) for g in groups]
    [[0, 1, 2], [4, 5, 6], [8, 9]]
    """
    for k, g in groupby(enumerate(idx), key=lambda x: x[0] - x[1]):
        yield map(itemgetter(1), g)


def join_adjacent(tokens: List[str], idx: List[int]) -> Union[str, List[str]]:
    """Join tokens with adjacent indices in idx list into strings.

    Given a list of tokens and list of indices for token with a particular value,
    join all the token with adjacent indices in the idx list into space seperated
    strings.

    If idx is an empty list, return an empty string.

    If there is only one group of adjacent values in idx, return a string.

    If there are multiple groups of adjacent values in idx, return a list of strings.

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

    Examples
    -------
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


def average(labels: List[str], scores: List[float], key: str) -> float:
    """Average the scores for labels matching key

    Given a particular label (key), find the indices of the labels that have that key.
    Then use those indices to take the average of the associated score in the scores
    input.

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


def fix_punctuation(sentence: str) -> str:
    """Fix punctuation when joining a list into a string

    1. Remove the ", " from start of the sentence
    2. Remove the space following an opening parens "(" and the space preceeding a
       closing parens ")" caused by using " ".join to turn a list into a sentence
    3. Remove the space preceeding a comma

    Parameters
    ----------
    sentence : str
        Sentence in which to fix punctuation

    Returns
    -------
    str
        Modified sentence

    Examples
    -------
    >>> fix_punctuation(", some words")
    'some words'

    >>> fix_punctuation("( text in brackets )")
    '(text in brackets)'

    >>> fix_punctuation("a comma follows this text ,")
    'a comma follows this text,'
    """
    # Let's not have any sentence fragments start with a comma
    if sentence.startswith(", "):
        sentence = sentence[2:]

    return sentence.replace("( ", "(").replace(" )", ")").replace(" ,", ",")


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

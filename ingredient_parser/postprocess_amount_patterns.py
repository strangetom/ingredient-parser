#!/usr/bin/env python3

import collections
from enum import Flag
from itertools import islice
from typing import Any, Iterator


class IngredientAmountFlags(Flag):
    APPROXIMATE = 0
    SINGULAR = 1


def consume(iterator: Iterator, n: int) -> None:
    """Advance the iterator n-steps ahead. If n is none, consume entirely.
    See consume from https://docs.python.org/3/library/itertools.html#itertools-recipes

    Parameters
    ----------
    iterator : Iterator
        Iterator to advance.
    n : int
        Number of iterations to advance by.
    """
    if n is None:
        # Feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # Advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)


def match_pattern(
    tokens: list[str], labels: list[str], pattern: list[str]
) -> list[tuple[int]]:
    """Find a pattern of labels and return the indicesof the start and end of match.

    For example, consider the sentence:
    One 15-ounce can diced tomatoes, with liquid

    It has the tokens and labels:
    ['1', '15', 'ounce', 'can', 'diced', 'tomatoes', ',', 'with', 'liquid']
    ['QTY', 'QTY', 'UNIT', 'UNIT', 'COMMENT', 'NAME', 'COMMA', 'COMMENT', 'COMMENT']

    If we search for the pattern:
    ["QTY", "QTY", "UNIT", "UNIT"]

    Then we get:
    [(0, 3)]

    Raises
    ------
    ValueError
        When the length of tokens and labels are not equal.

    Parameters
    ----------
    tokens : list[str]
        List of tokens to return matching pattern from.
    labels : list[str]
        List of labels to find matching pattern in.
    pattern : list[str]
        Pattern to match inside labels.

    Returns
    -------
    list[tuple[int]]
        Tuple of start index end index for matching pattern.
    """

    if len(tokens) != len(labels):
        raise ValueError("The length of tokens and labels must be the same.")

    if len(pattern) > len(tokens):
        # We can never find a match.
        return []

    plen = len(pattern)
    matches = []

    indices = iter(range(len(labels)))
    for i in indices:
        # Short circuit: If the label[i] is not equal to the first element of pattern
        # skip to next iteration
        if labels[i] == pattern[0] and labels[i : i + plen] == pattern:
            matches.append((i, i + plen))
            # Advance iterator to prevent overlapping matches
            consume(indices, plen)

    return matches


def sizable_unit_pattern(
    tokens: list[str], labels: list[str], scores: list[float]
) -> list[dict[str, Any]]:
    """Identify sentences which match the pattern where there is a quantity-unit pair
    split by one or mroe quantity-unit pairs e.g.

    * 1 28 ounce can
    * 2 17.3 oz (484g) package

    Return the correct sets of quantities and units, or an empty list.

    For example, for the sentence: 1 28 ounce can; the correct amounts are:
    [
        {"quantity": "1", "unit": ["can"], "score": [...]},
        {"quantity": "28", "unit": ["ounce"], "score": [...]},
    ]

    Parameters
    ----------
    tokens : list[str]
        Tokens for input sentence
    labels : list[str]
        Labels for input sentence tokens
    scores : list[float]
        Scores for each label

    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries for each set of amounts.
        The dictionary contains:
            quantity: str
            unit: list[str]
            score: list[float]
    """
    # We assume that the pattern will not be longer than the first element defined here.
    patterns = [
        ["QTY", "QTY", "UNIT", "QTY", "UNIT", "QTY", "UNIT", "UNIT"],
        ["QTY", "QTY", "UNIT", "QTY", "UNIT", "UNIT"],
        ["QTY", "QTY", "UNIT", "UNIT"],
    ]

    # List of possible units at end of pattern that constitute a match
    end_units = [
        "bag",
        "block",
        "box",
        "can",
        "envelope",
        "jar",
        "package",
        "packet",
        "tin",
    ]

    # Only keep QTY and UNIT tokens
    tokens = [token for token, label in zip(tokens, labels) if label in ["QTY", "UNIT"]]
    scores = [score for score, label in zip(scores, labels) if label in ["QTY", "UNIT"]]
    labels = [label for label in labels if label in ["QTY", "UNIT"]]

    amount_groups = []
    for pattern in patterns:
        for match in match_pattern(tokens, labels, pattern):
            # If the pattern ends with one of end_units, we have found a match for
            # this pattern!
            start, stop = match
            if tokens[stop - 1] in end_units:
                # Pop matches out of tokens and scores
                matching_tokens = [tokens.pop(start) for i in range(start, stop)]
                matching_scores = [scores.pop(start) for i in range(start, stop)]
                # Also pop matches out of labels, but we don't actually need them
                _ = [labels.pop(start) for i in range(start, stop)]

                # The first pair is the first and last items
                first = {
                    "quantity": matching_tokens.pop(0),
                    "unit": [matching_tokens.pop(-1)],
                    "score": [matching_scores.pop(0), matching_scores.pop(-1)],
                }
                amount_groups.append(first)

                for i in range(0, len(matching_tokens), 2):
                    quantity = matching_tokens[i]
                    unit = matching_tokens[i + 1]
                    score = matching_scores[i : i + 1]
                    group = {
                        "quantity": quantity,
                        "unit": [unit],
                        "score": score,
                        "flag": IngredientAmountFlags.SINGULAR,
                    }
                    amount_groups.append(group)

    if len(amount_groups) == 0:
        # If we haven't found any matches so far, return empty list
        # so consumers of the output of this function know there was no match.
        return []

    # Mop up any remaining amounts that didn't fit the pattern.
    amount_groups.extend(fallback_pattern(tokens, labels, scores))

    return amount_groups


def fallback_pattern(
    tokens: list[str], labels: list[str], scores: list[float]
) -> list[dict[str, Any]]:
    """Fallback pattern for grouping quantities and units into amounts.

    Parameters
    ----------
    tokens : list[str]
        Tokens for input sentence
    labels : list[str]
        Labels for input sentence tokens
    scores : list[float]
        Scores for each label

    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries for each set of amounts.
        The dictionary contains:
            quantity: str
            unit: list[str]
            score: list[float]
    """
    approximate_tokens = ["about", "approx.", "approximately"]
    per_unit_tokens = ["each"]

    groups = []
    prev_label = None
    for i, (token, label, score) in enumerate(zip(tokens, labels, scores)):
        if label == "QTY":
            groups.append({"quantity": token, "unit": [], "score": [score]})

            # If QTY preceeded by appoximate token, mark as approximate
            if i > 0 and tokens[i - 1].lower() in approximate_tokens:
                groups[-1]["flag"] = IngredientAmountFlags.APPROXIMATE

        elif label == "UNIT":
            # No quantity found yet, so create a group without a quantity
            if len(groups) == 0:
                groups.append({"quantity": "", "unit": [], "score": []})

            if prev_label == "COMMA":
                groups[-1]["unit"].append(",")

            groups[-1]["unit"].append(token)
            groups[-1]["score"].append(score)

            # If following token implies amount is singular, mark as singular
            if i < len(tokens) and tokens[i + 1].lower() in per_unit_tokens:
                groups[-1]["flag"] = IngredientAmountFlags.SINGULAR

        prev_label = label

    return groups

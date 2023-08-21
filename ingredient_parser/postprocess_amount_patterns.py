#!/usr/bin/env python3

import collections
from dataclasses import dataclass
from itertools import islice
from statistics import mean
from typing import Any, Iterator

from ._utils import pluralise_units


@dataclass
class IngredientAmount:
    """Dataclass for holding ingredient amount, comprising a quantity and a unit."""

    quantity: str
    unit: str
    confidence: float
    APPROXIMATE: bool = False
    SINGULAR: bool = False


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
) -> list[tuple[int, int]]:
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
) -> list[IngredientAmount]:
    """Identify sentences which match the pattern where there is a quantity-unit pair
    split by one or mroe quantity-unit pairs e.g.

    * 1 28 ounce can
    * 2 17.3 oz (484g) package

    Return the correct sets of quantities and units, or an empty list.

    For example, for the sentence: 1 28 ounce can; the correct amounts are:
    [
        IngredientAmount(quantity="1", unit="can", score=0.9...),
        IngredientAmount(uantity="28", unit="ounce", score=0.9...),
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
    list[IngredientAmount]
        List of IngredientAmount objects
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
        "piece",
        "tin",
    ]

    # Only keep QTY and UNIT tokens
    tokens = [token for token, label in zip(tokens, labels) if label in ["QTY", "UNIT"]]
    scores = [score for score, label in zip(scores, labels) if label in ["QTY", "UNIT"]]
    labels = [label for label in labels if label in ["QTY", "UNIT"]]

    amounts = []
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

                # The first amount is the first and last items
                first = IngredientAmount(
                    quantity=matching_tokens.pop(0),
                    unit=matching_tokens.pop(-1),
                    confidence=mean([matching_scores.pop(0), matching_scores.pop(-1)]),
                )
                amounts.append(first)

                for i in range(0, len(matching_tokens), 2):
                    quantity = matching_tokens[i]
                    unit = matching_tokens[i + 1]
                    confidence = mean(matching_scores[i : i + 1])

                    amount = IngredientAmount(
                        quantity=quantity,
                        unit=unit,
                        confidence=confidence,
                        SINGULAR=True,
                    )
                    amounts.append(amount)

    if len(amounts) == 0:
        # If we haven't found any matches so far, return empty list
        # so consumers of the output of this function know there was no match.
        return []

    # Mop up any remaining amounts that didn't fit the pattern.
    amounts.extend(fallback_pattern(tokens, labels, scores))

    return amounts


def fallback_pattern(
    tokens: list[str], labels: list[str], scores: list[float]
) -> list[IngredientAmount]:
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
    amounts = []
    for i, (token, label, score) in enumerate(zip(tokens, labels, scores)):
        if label == "QTY":
            # Whenever we come across a new QTY, create new IngredientAmount
            amounts.append(
                IngredientAmount(quantity=token, unit=[], confidence=[score])
            )

        if label == "UNIT":
            if len(amounts) == 0:
                # Not come across a QTY yet, so create IngredientAmount
                # with no quantity
                amounts.append(IngredientAmount(quantity="", unit=[], confidence=[]))

            if i > 0 and labels[i - 1] == "COMMA":
                # If previous token was a comma, append to unit of last IngredientAmount
                amounts[-1].unit.append(",")

            # Append token and score for unit to last IngredientAmount
            amounts[-1].unit.append(token)
            amounts[-1].confidence.append(score)

        # Check if any flags should be set
        if is_approximate(i, tokens, labels):
            amounts[-1].APPROXIMATE = True

        if is_singular(i, tokens, labels):
            amounts[-1].SINGULAR = True

        if is_singular_and_approximate(i, tokens, labels):
            amounts[-1].APPROXIMATE = True
            amounts[-1].SINGULAR = True

    # Second pass to fix unit and confidence
    # Unit needs converting to a string and making plural if appropriate
    # Confidence needs averaging
    for amount in amounts:
        combined_unit = " ".join(amount.unit)
        # Pluralise the units if appropriate
        if amount.quantity != "1" and amount.quantity != "":
            combined_unit = pluralise_units(combined_unit)

        amount.unit = combined_unit
        amount.confidence = round(mean(amount.confidence), 6)

    return amounts


def is_approximate(i: int, tokens: list[str], labels: list[str]) -> bool:
    """Return True is token at current index is approximate, determined
    by the token label being QTY and the previous token being in a list of
    approximate tokens.

    Parameters
    ----------
    i : int
        Index of current token
    tokens : list[str]
        List of all tokens
    labels : list[str]
        List of all token labels

    Returns
    -------
    bool
        True if current token is approximate
    """
    approximate_tokens = ["about", "approx.", "approximately", "nearly"]

    if i == 0:
        return False

    if labels[i] == "QTY" and tokens[i - 1].lower() in approximate_tokens:
        return True

    return False


def is_singular(i: int, tokens: list[str], labels: list[str]) -> bool:
    """Return True is token at current index is singular, determined
    by the token label being UNIT and the next token being in a list of
    singular tokens.

    Parameters
    ----------
    i : int
        Index of current token
    tokens : list[str]
        List of all tokens
    labels : list[str]
        List of all token labels

    Returns
    -------
    bool
        True if current token is singular
    """
    singular_tokens = ["each"]

    if i == len(tokens) - 1:
        return False

    if labels[i] == "UNIT" and tokens[i + 1].lower() in singular_tokens:
        return True

    return False


def is_singular_and_approximate(i: int, tokens: list[str], labels: list[str]) -> bool:
    """Return True if the current token is approximate and singular, determined by the
    token label being QTY and is preceeded by a token in a list of singular tokens, then
    token in a list of approximate tokens.

    e.g. each nearly 3 ...

    Parameters
    ----------
    i : int
        Index of current token
    tokens : list[str]
        List of all tokens
    labels : list[str]
        List of all token labels

    Returns
    -------
    bool
        True if current token is singular
    """
    approximate_tokens = ["about", "approx.", "approximately", "nearly"]
    singular_tokens = ["each"]

    if i < 2:
        return False

    if (
        labels[i] == "QTY"
        and tokens[i - 1].lower() in approximate_tokens
        and tokens[i - 2].lower() in singular_tokens
    ):
        return True

    return False

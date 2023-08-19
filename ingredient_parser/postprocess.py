#!/usr/bin/env python3

import re
from dataclasses import dataclass
from itertools import groupby
from operator import itemgetter
from statistics import mean
from typing import Generator, Iterator

from ._constants import UNITS


@dataclass
class IngredientAmount:
    """Dataclass for holding ingredient amount, comprising a quantity and a unit."""

    quantity: str
    unit: str
    confidence: float


@dataclass
class IngredientText:
    """Dataclass for holding parsed ingredient strings"""

    text: str
    confidence: float


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


def group_consecutive_idx(idx: list[int]) -> Generator[Iterator[int], None, None]:
    """Yield groups of consecutive indices

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
    -------
    >>> groups = group_consecutive_idx([0, 1, 2, 4, 5, 6, 8, 9])
    >>> [list(g) for g in groups]
    [[0, 1, 2], [4, 5, 6], [8, 9]]
    """
    for k, g in groupby(enumerate(idx), key=lambda x: x[0] - x[1]):
        yield map(itemgetter(1), g)


def postprocess_amounts(
    tokens: list[str], labels: list[str], scores: list[float]
) -> list[IngredientAmount]:
    """Process tokens, labels and scores into IngredientAmount objects, by combining
    QTY labels with any following UNIT labels, up to the next QTY label.

    The confidence is the average confidence of all labels in the IngredientGroup.

    This assumes that the QTY label for an amount always preceeds any associated
    UNIT labels.

    Parameters
    ----------
    tokens : list[str]
        List of tokens for input sentence
    labels : list[str]
        List of labels for each token of input sentence
    scores : list[float]
        List of sores for each label

    Returns
    -------
    list[IngredientAmount]
        List of IngredientAmount objects
    """
    groups = []
    prev_label = None
    for token, label, score in zip(tokens, labels, scores):
        if label == "QTY":
            groups.append({"quantity": token, "unit": [], "score": [score]})

        elif label == "UNIT":
            # No quantity found yet, so create a group without a quantity
            if len(groups) == 0:
                groups.append({"quantity": "", "unit": [], "score": []})

            if prev_label == "COMMA":
                groups[-1]["unit"].append(",")

            groups[-1]["unit"].append(token)
            groups[-1]["score"].append(score)

        prev_label = label

    amounts = []
    for group in groups:
        quantity = group["quantity"]
        combined_unit = " ".join(group["unit"])
        combined_score = round(mean(group["score"]), 6)

        # Pluralise the units if appropriate
        if quantity != 1 and quantity != "":
            combined_unit = pluralise_units(combined_unit)

        amount = IngredientAmount(
            quantity=quantity,
            unit=combined_unit,
            confidence=combined_score,
        )
        amounts.append(amount)

    return amounts


def postprocess(
    tokens: list[str], labels: list[str], scores: list[float], selected: str
) -> IngredientText:
    """Process tokens, labels and scores with selected label into an
    IngredientText object.

    Parameters
    ----------
    tokens : list[str]
        List of tokens for input sentence
    labels : list[str]
        List of labels for each token of input sentence
    scores : list[float]
        List of sores for each label
    selected : str
        Selected label of token to postprocess

    Returns
    -------
    IngredientText
        Object containing ingredient comment text and confidencee
    """

    comment_idx = [i for i, label in enumerate(labels) if label == selected]

    parts = []
    confidence_parts = []
    for group in group_consecutive_idx(comment_idx):
        idx = list(group)
        joined = " ".join([tokens[i] for i in idx])
        confidence = mean([scores[i] for i in idx])

        parts.append(joined)
        confidence_parts.append(confidence)

    if len(parts) == 0:
        return None

    return IngredientString(
        text=fix_punctuation(", ".join(parts)),
        confidence=round(mean(confidence_parts), 6),
    )

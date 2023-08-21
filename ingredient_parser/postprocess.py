#!/usr/bin/env python3

import re
from dataclasses import dataclass
from itertools import groupby
from operator import itemgetter
from statistics import mean
from typing import Generator, Iterator

from .postprocess_amount_patterns import (
    IngredientAmount,
    fallback_pattern,
    sizable_unit_pattern,
)

WORD_CHAR = re.compile(r"\w")


@dataclass
class IngredientText:
    """Dataclass for holding parsed ingredient strings"""

    text: str
    confidence: float


def fix_punctuation(text: str) -> str:
    """Fix some common punctuation errors that result from combining tokens of the
    same label together.

    Parameters
    ----------
    text : str
        Text resulting from combining tokens with same label

    Returns
    -------
    str
        Text, with punctuation errors fixed
    """
    # Remove leading comma
    if text.startswith(", "):
        text = text[2:]

    # Remove trailing comma
    if text.endswith(","):
        text = text[:-1]

    # Correct space following open parens or before close parens
    text = text.replace("( ", "(").replace(" )", ")")

    # Remove parentheses that aren't part of a matching pair
    idx_to_remove = []
    stack = []
    for i, char in enumerate(text):
        if char == "(":
            # Add index to stack when we find an opening parens
            stack.append(i)
        elif char == ")":
            if len(stack) == 0:
                # If the stack is empty, we've found a dangling closing parens
                idx_to_remove.append(i)
            else:
                # Remove last added index from stack when we find a closing parens
                stack.pop()

    # Insert anything left in stack into idx_to_remove
    idx_to_remove.extend(stack)
    text = "".join(char for i, char in enumerate(text) if i not in idx_to_remove)

    return text


def remove_isolated_punctuation(parts: list[str]) -> list[int]:
    """Find elements in list that comprise a single punctuation character.

    Parameters
    ----------
    parts : list[str]
        List of tokens with single label, grouped if consecutive

    Returns
    -------
    list[int]
        Indices of elements in parts to keep

    Examples
    --------

    Deleted Parameters
    ------------------
    sentence : str
        Sentence in which to fix punctuation
    """
    # Only keep a part if contains a word character
    idx_to_keep = [i for i, part in enumerate(parts) if WORD_CHAR.search(part)]
    return idx_to_keep


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

    if match := sizable_unit_pattern(tokens, labels, scores):
        groups = match
    else:
        groups = fallback_pattern(tokens, labels, scores)

    return groups


def postprocess(
    tokens: list[str], labels: list[str], scores: list[float], selected: str
) -> IngredientText | None:
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

    idx = remove_isolated_punctuation(parts)
    parts = [parts[i] for i in idx]
    confidence_parts = [confidence_parts[i] for i in idx]

    text = ", ".join(parts)
    text = fix_punctuation(text)

    if len(parts) == 0:
        return None

    return IngredientText(
        text=text,
        confidence=round(mean(confidence_parts), 6),
    )

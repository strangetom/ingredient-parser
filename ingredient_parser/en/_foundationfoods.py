#!/usr/bin/env python3

from collections import defaultdict
from functools import lru_cache
from importlib.resources import as_file, files
from itertools import groupby
from statistics import mean

import pycrfsuite

from .._common import group_consecutive_idx
from ..dataclasses import FoundationFood


@lru_cache
def load_foundation_foods_model() -> pycrfsuite.Tagger:  # type: ignore
    """Load foundation foods model.

    This function is cached so that when the model has been loaded once, it does not
    need to be loaded again, the cached model is returned.

    Returns
    -------
    pycrfsuite.Tagger
        Foundation foods model loaded into Tagger object.
    """
    ff_tagger = pycrfsuite.Tagger()  # type: ignore
    with as_file(files(__package__) / "ff_model.en.crfsuite") as p:
        ff_tagger.open(str(p))
        return ff_tagger


def join_adjacent_FF_tokens(
    labels: list[str], tokens: list[str], scores: list[float]
) -> list[FoundationFood]:
    """Join adjacent tokens labelled as FF into strings.

    Parameters
    ----------
    labels : list[str]
        List of token labels: FF (foundation food) of NF (not foundation food)
    tokens : list[str]
        List of NAME tokens
    scores : list[float]
        List of confidence scores for labels

    Returns
    -------
    list[FoundationFood]
        List of foundation foods

    Examples
    --------
    >>> join_adjacent_FF_tokens(
    ...     ["FF", "NF", "NF", "FF", "FF"], ["milk", "or", "fortified", "soy", "milk"]
    ... )
    ["milk", "soy milk"]
    """
    foundation_foods = []
    # Group into groups of adjacent FF tags, ignoring any NF tags.
    for label, group in groupby(zip(labels, tokens, scores), key=lambda x: x[0]):
        if label == "NF":
            continue

        group = list(group)
        score = mean([score for _, _, score in group])

        foundation_foods.append(
            FoundationFood(" ".join([tok for _, tok, _ in group]), round(score, 6))
        )

    return foundation_foods


def deduplicate_foundation_foods(
    foundation_foods: list[FoundationFood],
) -> list[FoundationFood]:
    """Deduplicate foundation foods by averaging the score of duplicates.

    Parameters
    ----------
    foundation_foods : list[FoundationFood]
        List of foundation foods found in ingredient name.

    Returns
    -------
    list[FoundationFood]
        Description
    """

    seen_foods = defaultdict(list)
    for ff in foundation_foods:
        seen_foods[ff.text.lower()].append(ff.confidence)

    return [
        FoundationFood(name, mean(confidences))
        for name, confidences in seen_foods.items()
    ]


def extract_foundation_foods(
    tokens: list[str],
    labels: list[str],
    features: list[dict[str, str | bool | int | float]],
) -> list[FoundationFood]:
    """Extract foundation foods from tokens labelled as NAME.

    Parameters
    ----------
    tokens : list[str]
        Sentence tokens
    labels : list[str]
        Labels for sentence tokens
    features : list[dict[str, str | bool| int]]
        Features for sentence tokens

    Returns
    -------
    list[FoundationFood]
        List of foundation foods.
    """
    FF_TAGGER = load_foundation_foods_model()

    name_idx = [idx for idx, label in enumerate(labels) if "NAME" in label]
    name_tokens = [tok for tok, label in zip(tokens, labels) if "NAME" in label]
    name_features = [feat for feat, label in zip(features, labels) if "NAME" in label]

    # We want to join consecutive foundation food tokens together into a single
    # string, but keep any token seperated by a non-foundation food or another
    # non-NAME label separate.
    # First we iterate through groups of consecutive NAME labelled tokens and select
    # any tagged as foundation food. Then we join adjacent foundation food tokens
    # together and append to list.
    foundation_foods = []
    for group in group_consecutive_idx(name_idx):
        group = list(group)
        name_tokens = [tok for idx, tok in enumerate(tokens) if idx in group]
        name_features = [feat for idx, feat in enumerate(features) if idx in group]
        ff_labels = FF_TAGGER.tag(name_features)
        name_scores = [
            FF_TAGGER.marginal(label, i) for i, label in enumerate(ff_labels)
        ]

        foundation_foods.extend(
            join_adjacent_FF_tokens(ff_labels, name_tokens, name_scores)
        )

    return deduplicate_foundation_foods(foundation_foods)

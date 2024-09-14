#!/usr/bin/env python3

from importlib.resources import as_file, files
from itertools import groupby

import pycrfsuite

from .._common import group_consecutive_idx

# Create FF_TAGGER object that can be reused between function calls.
# We only want to load the model into FF_TAGGER once, but only do it
# when we need to (from parse_ingredient() or inspect_parser()) and
# not whenever anything from ingredient_parser is imported.
FF_TAGGER = pycrfsuite.Tagger()  # type: ignore


def load_ffmodel_if_not_loaded():
    """Load foundation foods model into FF_TAGGER variable if not loaded.

    There isn't a simple way to check if the model if loaded or not, so
    we try to call FF_TAGGER.labels() which will raise a ValueError if the
    model is not loaded yet.
    """
    try:
        FF_TAGGER.labels()
    except ValueError:
        with as_file(files(__package__) / "ff_model.en.crfsuite") as p:
            FF_TAGGER.open(str(p))


def join_adjacent_FF_tokens(labels: list[str], tokens: list[str]) -> list[str]:
    """Join adjacent tokens labelled as FF into strings.

    Parameters
    ----------
    labels : list[str]
        List of token labels: FF (foundation food) of NF (not foundation food)
    tokens : list[str]
        List of NAME token

    Returns
    -------
    list[str]
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
    for label, group in groupby(zip(labels, tokens), key=lambda x: x[0]):
        if label == "NF":
            continue

        foundation_food = " ".join([tok for _, tok in group])
        if foundation_food:
            foundation_foods.append(foundation_food)

    return foundation_foods


def extract_foundation_foods(
    tokens: list[str], labels: list[str], features: list[dict[str, str | bool]]
) -> list[str] | None:
    """Extract foundation foods from tokens labelled as NAME.

    Parameters
    ----------
    tokens : list[str]
        Sentence tokens
    labels : list[str]
        Labels for sentence tokens
    features : list[dict[str, str | bool]]
        Features for sentence tokens

    Returns
    -------
    list[str] | None
        List of foundation foods, or None.
    """
    load_ffmodel_if_not_loaded()

    name_idx = [idx for idx, label in enumerate(labels) if label == "NAME"]
    name_tokens = [tok for tok, label in zip(tokens, labels) if label == "NAME"]
    name_features = [feat for feat, label in zip(features, labels) if label == "NAME"]

    ff_labels = FF_TAGGER.tag(name_features)

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

        foundation_foods.extend(join_adjacent_FF_tokens(ff_labels, name_tokens))

    if foundation_foods:
        return foundation_foods

    return None

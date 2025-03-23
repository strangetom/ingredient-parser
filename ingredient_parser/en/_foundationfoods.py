#!/usr/bin/env python3

import string
from functools import lru_cache

import numpy as np

from ..dataclasses import FoundationFood
from ._constants import EMBEDDING_POS_TAGS, STOP_WORDS
from ._loaders import FDCIngredient, load_embeddings_model, load_foundation_foods_data
from ._utils import stem

# Dict of ingredient name tokens that bypass the usual foundation food matching process.
# We do this because the embedding distance approach sometime gives poor results when
# the name we're trying to match only has one token.
FOUNDATION_FOOD_OVERRIDES: dict[tuple[str, ...], FoundationFood] = {
    ("salt",): FoundationFood(
        "Salt, table, iodized", 1, 746775, "Spices and Herbs", "foundation_food"
    ),
    ("egg",): FoundationFood(
        "Eggs, Grade A, Large, egg whole",
        1,
        748967,
        "748967",
        "foundation_food",
    ),
    ("eggs",): FoundationFood(
        "Eggs, Grade A, Large, egg whole",
        1,
        748967,
        "748967",
        "foundation_food",
    ),
}


def prepare_tokens(tokens: list[str], pos_tags: list[str]) -> list[str]:
    """Prepare tokens for use with embeddings model.

    This involves obtaning the stem for the token and discarding tokens whose POS tag is
    not in EMBEDDING_POS_TAGS, which are numeric, which are punctuation, or which are
    in STOP_WORDS.

    Parameters
    ----------
    tokens : list[str]
        List of tokens
    pos_tags : list[str]
        List of POS tags for tokens

    Returns
    -------
    list[str]
        Prepared tokens.
    """
    return [
        stem(token.lower())
        for token, pos in zip(tokens, pos_tags)
        if pos in EMBEDDING_POS_TAGS
        and not token.isnumeric()
        and not token.isdigit()
        and not token.isdecimal()
        and not token.isspace()
        and token not in string.punctuation
        and token not in STOP_WORDS
        and len(token) > 1
    ]


def token_similarity(token1: str, token2: str, model) -> float:
    """Calculate similarity between two word embeddings.

    This uses the reciprocal euclidean distance transformed by a sigmoid function to
    return a value between 0 and 1.
    1 indicates an exact match (i.e. token1 and token2 are the same).
    0 indicates no match whatsoever.

    Parameters
    ----------
    token1 : str
        First token.
    token2 : str
        Second token.
    model : floret
        Embeddings model.

    Returns
    -------
    float
        Value between 0 and 1.
    """
    euclidean_dist = np.linalg.norm(model[token1] - model[token2])

    if euclidean_dist == 0:
        return 1
    elif euclidean_dist == np.inf:
        return 0
    else:
        sigmoid = 1 / (1 + np.exp(-1 / euclidean_dist))
        return float(sigmoid)


@lru_cache(maxsize=512)
def max_token_similarity(token: str, fdc_ingredient: tuple[str, ...], model) -> float:
    """Calculate the maximum similarity of token to FDC Ingredient description tokens.

    Similarlity score is calculated from the euclidean distance between token and
    all tokens that make up the FDC Ingredient description.
    The reciprocal of this distance if transformed using a signmoid function to return
    the score between 0 and 1.
    A score of 1 indicates that token is found exactly in fdc_ingredient.

    Parameters
    ----------
    token : str
        Token to calculate similarity of.
    fdc_ingredient : tuple[str, ...]
        FDC Ingredient description tokens to calculate maximum token similarity to.
    model : floret
        Embeddings model.

    Returns
    -------
    float
        Membership score between 0 and 1, where 1 indicates exact match.
    """
    return max(token_similarity(token, t, model) for t in fdc_ingredient)


@lru_cache(maxsize=512)
def fuzzy_document_distance(
    ingredient_name: tuple[str, ...], fdc_ingredient: tuple[str, ...]
) -> float:
    """Calculate fuzzy document distance between ingredient name and FDC ingredient.

    Implementation of https://doi.org/10.1109/ACCESS.2021.3058559.

    Tuples are used here to allow for LRU caching.

    Parameters
    ----------
    ingredient_name : tuple[str, ...]
        Tokens for ingredient name.
    fdc_ingredient : tuple[str, ...]
        Tokens for FDC Ingredient description.

    Returns
    -------
    float
        Fuzzy document distance.
        Smaller values mean closer match.
    """
    model = load_embeddings_model()

    # Remove out of vocabularly words
    ingredient_name = tuple(token for token in ingredient_name if token in model)
    fdc_ingredient = tuple(token for token in fdc_ingredient if token in model)

    # If either document only contains out of vocab words, return infinite distance
    if not ingredient_name or not fdc_ingredient:
        return float("inf")

    # Calculate fuzzy intersection
    union_membership = 0.0
    cj1_membership = 0.0
    cj2_membership = 0.0

    tokens = set(ingredient_name) | set(fdc_ingredient)
    for token in tokens:
        union_membership += max_token_similarity(
            token, ingredient_name, model
        ) * max_token_similarity(token, fdc_ingredient, model)
        cj1_membership += max_token_similarity(token, ingredient_name, model)
        cj2_membership += max_token_similarity(token, fdc_ingredient, model)

    res = union_membership / (cj1_membership + cj2_membership - union_membership)
    return 1 - res


def match_foundation_foods(
    tokens: list[str],
    pos: list[str],
) -> FoundationFood | None:
    """Match ingredient name to foundation foods from FDC Ingredient.

    Parameters
    ----------
    tokens : list[str]
        Ingredient name tokens
    pos : list[str]
        Part of speech tags for tokens

    Returns
    -------
    FoundationFood | None
        Matching foundation food, or None if no match can be found.
    """
    if tuple(t.lower() for t in tokens) in FOUNDATION_FOOD_OVERRIDES:
        return FOUNDATION_FOOD_OVERRIDES[tuple(t.lower() for t in tokens)]

    fdc_ingredients = load_foundation_foods_data()

    ingredient_name_tokens = prepare_tokens(tokens, pos)

    scores: list[tuple[float, FDCIngredient]] = []
    for fdc_ingredient in fdc_ingredients:
        fdc_ingredient_tokens = prepare_tokens(
            fdc_ingredient.tokens, fdc_ingredient.pos_tags
        )
        score = fuzzy_document_distance(
            tuple(ingredient_name_tokens), tuple(fdc_ingredient_tokens)
        )
        scores.append((score, fdc_ingredient))

    # Sort to find best score
    best_score, best_fdc_match = sorted(scores, key=lambda x: x[0])[0]

    if best_score <= 0.35:
        return FoundationFood(
            text=best_fdc_match.description,
            confidence=round(1 - best_score, 6),
            fdc_id=best_fdc_match.fdc_id,
            category=best_fdc_match.category,
            data_type=best_fdc_match.data_type,
        )
    else:
        return None

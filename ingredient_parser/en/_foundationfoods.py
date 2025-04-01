#!/usr/bin/env python3

import string
from functools import lru_cache

import numpy as np

from ..dataclasses import FoundationFood
from ._loaders import FDCIngredient, load_embeddings_model, load_foundation_foods_data
from ._utils import prepare_embeddings_tokens

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
        "Dairy and Egg Products",
        "foundation_food",
    ),
    ("eggs",): FoundationFood(
        "Eggs, Grade A, Large, egg whole",
        1,
        748967,
        "Dairy and Egg Products",
        "foundation_food",
    ),
}

# List of preferred FDC data types.
# Increasing value indicates decreasing preference.
PREFERRED_DATATYPES = {
    "foundation_food": 0,  #  Most preferred
    "sr_legacy_food": 1,
    "survey_fndds_food": 2,
}


@lru_cache
def get_vector(token: str) -> np.ndarray:
    """Get embedding vector for token.

    This function exists solely so this operation can be LRU cached.

    Parameters
    ----------
    token : str
        Token to return embedding vector for.

    Returns
    -------
    np.ndarray
        Embedding vector
    """
    model = load_embeddings_model()
    return model[token]


@lru_cache(maxsize=512)
def token_similarity(token1: str, token2: str) -> float:
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

    Returns
    -------
    float
        Value between 0 and 1.
    """
    euclidean_dist = np.linalg.norm(get_vector(token1) - get_vector(token2))

    if euclidean_dist == 0:
        return 1
    elif euclidean_dist == np.inf:
        return 0
    else:
        sigmoid = 1 / (1 + np.exp(-1 / euclidean_dist))
        return float(sigmoid)


@lru_cache(maxsize=512)
def max_token_similarity(token: str, fdc_ingredient: tuple[str, ...]) -> float:
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

    Returns
    -------
    float
        Membership score between 0 and 1, where 1 indicates exact match.
    """
    return max(token_similarity(token, t) for t in fdc_ingredient)


@lru_cache(maxsize=512)
def fuzzy_document_distance(
    ingredient_name: tuple[str, ...], fdc_ingredient: tuple[str, ...]
) -> float:
    """Calculate fuzzy document distance between ingredient name and FDC ingredient.

    Implementation of https://doi.org/10.1109/ACCESS.2021.3058559.

    Tuples are used for inputs to allow for LRU caching.

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
    # If either document only contains out of vocab words, return infinite distance
    if not ingredient_name or not fdc_ingredient:
        return float("inf")

    # Calculate fuzzy intersection from the tokens that are similar in both the
    # ingredient and FDC ingredient name, to the tokens that are similar to only
    # one of the ingredient or FDC name.
    union_membership = 0.0
    ingred_membership = 0.0
    fdc_membership = 0.0

    tokens = set(ingredient_name) | set(fdc_ingredient)
    for token in tokens:
        token_ingred_score = max_token_similarity(token, ingredient_name)
        token_fdc_score = max_token_similarity(token, fdc_ingredient)

        union_membership += token_ingred_score * token_fdc_score
        ingred_membership += token_ingred_score
        fdc_membership += token_fdc_score

    res = union_membership / (ingred_membership + fdc_membership - union_membership)
    return 1 - res


def rescore_considering_preferred_datatype(
    sorted_scores: list[tuple[float, FDCIngredient]],
) -> tuple[float, FDCIngredient]:
    """Rescore FDC ingredient considering data type preferences.

    If there are other FDC Ingredients with scores within 2.5% of the best, select the
    FDC Ingredient from the most preferred datatype. If there are multiple from the same
    datatype, select the one with the lowest score.

    Parameters
    ----------
    sorted_scores : list[tuple[float, FDCIngredient]]
        Tuple of (score, FDCIngredient), sorted in order of increasing score.

    Returns
    -------
    tuple[float, FDCIngredient]
        Tuple of (best score, FDC Ingredient)
    """
    best_score = sorted_scores[0][0]

    # If the best score, return that item.
    # The FDC data does not contain duplicates, so this is an exact match.
    if best_score == 0:
        return sorted_scores[0]

    alternatives = [
        (score, fdc)
        for (score, fdc) in sorted_scores
        if score != float("inf") and (score - best_score) / best_score <= 0.025
    ]
    if len(alternatives) == 1:
        # If nothing else within 2.5% of best, return best
        return alternatives[0]

    # Sort alternatives, first by preferred dataset, then by score
    sorted_alternatives = sorted(
        alternatives, key=lambda x: (PREFERRED_DATATYPES[x[1].data_type], x[0])
    )
    return sorted_alternatives[0]


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
    override_name = tuple(t.lower() for t in tokens if t not in string.punctuation)
    if override_name in FOUNDATION_FOOD_OVERRIDES:
        return FOUNDATION_FOOD_OVERRIDES[override_name]

    # Prepare ingredient name tokens and remove out of vocabulary tokens
    model = load_embeddings_model()
    ingredient_name_tokens = tuple(
        token
        for token, _ in prepare_embeddings_tokens(tuple(tokens), tuple(pos))
        if token in model
    )

    # Score matches between ingredient name and FDC ingredient description tokens
    # Note that load_foundation_foods_data is a cached function
    scores: list[tuple[float, FDCIngredient]] = []
    for fdc_ingredient in load_foundation_foods_data():
        score = fuzzy_document_distance(ingredient_name_tokens, fdc_ingredient.tokens)
        scores.append((score, fdc_ingredient))

    # Sort to find best score
    sorted_scores = sorted(scores, key=lambda x: x[0])

    # If the best score is inf, return None
    if sorted_scores[0][0] == float("inf"):
        return None

    # Reorder results to account for data type preferences
    best_score, best_fdc_match = rescore_considering_preferred_datatype(sorted_scores)
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

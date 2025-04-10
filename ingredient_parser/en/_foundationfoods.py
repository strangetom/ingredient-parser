#!/usr/bin/env python3

import string
from functools import lru_cache
from typing import NamedTuple

import numpy as np

from ..dataclasses import FoundationFood
from ._loaders import FDCIngredient, load_embeddings_model, load_foundation_foods_data
from ._utils import prepare_embeddings_tokens


class FuzzyScore(NamedTuple):
    full_score: float
    noun_score: float


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
    ("butter",): FoundationFood(
        "Butter, stick, unsalted",
        1,
        789828,
        "Dairy and Egg Products",
        "foundation_food",
    ),
    ("cucumber",): FoundationFood(
        "Cucumber, with peel, raw",
        1,
        2346406,
        "Vegetables and Vegetable Products",
        "foundation_food",
    ),
}

SPELLING_CORRECTIONS = {
    "yoghurt": "yogurt",
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

    Similarity score is calculated from the euclidean distance between token and
    all tokens that make up the FDC Ingredient description.
    The reciprocal of this distance if transformed using a sigmoid function to return
    the score between 0 and 1.
    A score of 1 indicates that token is found exactly in fdc_ingredient.

    If the token under test is a noun, the similarity score is weighted to increase the
    score.

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


def token_union(
    ingredient_name: tuple[str, ...],
    ingredient_pos_tags: tuple[str, ...],
    fdc_ingredient: tuple[str, ...],
    fdc_pos_tags: tuple[str, ...],
) -> set[tuple[str, str]]:
    """Return union of tokens from ingredient name and FDC ingredient, with the token's
    part of speech tag.

    If the token appears in both the ingredient and FDC ingredient with different part
    of speech tags, use the tag from the ingredient token.

    Parameters
    ----------
    ingredient_name : tuple[str, ...]
        Tokens for ingredient name.
    ingredient_pos_tags : tuple[str, ...]
        Part of speech tags for ingredient name tokens.
    fdc_ingredient : tuple[str, ...]
        Tokens for FDC ingredient description.
    fdc_pos_tags : tuple[str, ...]
        Part of speech tags for FDC ingredient tokens.

    Returns
    -------
    set[tuple[str, str]]
        Set of (token, pos) pairs.
    """
    tokens = []
    pos_tags = []
    for token, pos in zip(
        ingredient_name + fdc_ingredient, ingredient_pos_tags + fdc_pos_tags
    ):
        if token not in tokens:
            tokens.append(token)
            pos_tags.append(pos)

    return {(token, pos) for token, pos in zip(tokens, pos_tags)}


@lru_cache(maxsize=512)
def fuzzy_document_distance(
    ingredient_name: tuple[str, ...],
    ingredient_pos_tags: tuple[str, ...],
    fdc_ingredient: tuple[str, ...],
    fdc_pos_tags: tuple[str, ...],
) -> FuzzyScore:
    """Calculate fuzzy document distance between ingredient name and FDC ingredient.

    Tuples are used for inputs to allow for LRU caching.
    Implementation of https://doi.org/10.1109/ACCESS.2021.3058559, but modified to add
    additional weight to nouns compared to non-noun tokens.

    Parameters
    ----------
    ingredient_name : tuple[str, ...]
        Tokens for ingredient name.
    ingredient_pos_tags : tuple[str, ...]
        Part of speech tags for ingredient name tokens.
    fdc_ingredient : tuple[str, ...]
        Tokens for FDC ingredient description.
    fdc_pos_tags : tuple[str, ...]
        Part of speech tags for FDC ingredient tokens.

    Returns
    -------
    FuzzyScore
        Fuzzy document distance.
        Smaller values mean closer match.
    """
    # If either document only contains out of vocab words, return infinite distance
    if not ingredient_name or not fdc_ingredient:
        return FuzzyScore(float("inf"), float("inf"))

    # Calculate fuzzy intersection from the tokens that are similar in both the
    # ingredient and FDC ingredient name, to the tokens that are similar to only
    # one of the ingredient or FDC name.
    union_membership = 0.0
    ingred_membership = 0.0
    fdc_membership = 0.0

    union_membership_noun = 0.0
    ingred_membership_noun = 0.0
    fdc_membership_noun = 0.0

    for token, pos in token_union(
        ingredient_name, ingredient_pos_tags, fdc_ingredient, fdc_pos_tags
    ):
        token_ingred_score = max_token_similarity(token, ingredient_name)
        token_fdc_score = max_token_similarity(token, fdc_ingredient)

        if pos.startswith("NN"):
            union_membership_noun += token_ingred_score * token_fdc_score
            ingred_membership_noun += token_ingred_score
            fdc_membership_noun += token_fdc_score

        union_membership += token_ingred_score * token_fdc_score
        ingred_membership += token_ingred_score
        fdc_membership += token_fdc_score

    # Protect against divide by zero errors
    if (ingred_membership_noun + fdc_membership_noun - union_membership_noun) > 0:
        res_noun = union_membership_noun / (
            ingred_membership_noun + fdc_membership_noun - union_membership_noun
        )
    else:
        res_noun = 0

    if (ingred_membership + fdc_membership - union_membership) > 0:
        res = union_membership / (ingred_membership + fdc_membership - union_membership)
    else:
        res = 0

    return FuzzyScore(1 - res, 1 - res_noun)


def match_foundation_foods(
    tokens: list[str],
    pos: list[str],
) -> FoundationFood | None:
    """Match ingredient name to foundation foods from FDC Ingredient.

    The matching process follows these steps:
    1. Check if the input tokens match one of the overrides and if they do, return that.
    2. Prepare the ingredient tokens for scoring using the embedding model.
    3. Iterate through each of the FDC data types in order of preference
       i.   Score the match between the input ingredient and each FDC ingredient
       ii.  Sort the scores smallest to largest (smaller is better)
       iii. If the best (smallest) score is <= 0.25, return that ingredient
       iv.  If the best score is not <= 0.25, store it for fallback checking
    4. If we haven't found a suitable match after iterating through all data types, take
       the best match from each data type and select the best of those. If the score is
       <= 0.4 return that match.
    5. Return None, if not suitable match is found.

    Parameters
    ----------
    tokens : list[str]
        Ingredient name tokens.
    pos : list[str]
        Part of speech tags for ingredient name tokens.

    Returns
    -------
    FoundationFood | None
        Matching foundation food, or None if no match can be found.
    """
    override_name = tuple(t.lower() for t in tokens if t not in string.punctuation)
    if override_name in FOUNDATION_FOOD_OVERRIDES:
        return FOUNDATION_FOOD_OVERRIDES[override_name]

    foundation_foods = load_foundation_foods_data()

    # Prepare ingredient name tokens
    # We don't require tokens be in the model vocabulary because fasttext/floret models
    # should be able to handle out of vocabulary words.
    # Prepareation also include making some spelling modifications.
    ingredient_name_tokens = []
    ingredient_token_pos = []
    for name_token, name_pos in prepare_embeddings_tokens(tuple(tokens), tuple(pos)):
        ingredient_token_pos.append(name_pos)
        if name_token in SPELLING_CORRECTIONS:
            ingredient_name_tokens.append(SPELLING_CORRECTIONS[name_token])
        else:
            ingredient_name_tokens.append(name_token)

    fallback_scores: list[tuple[FuzzyScore, FDCIngredient]] = []
    # Iterate through preferred data types in order. If we find a good enough match,
    # return it immediately.
    for data_type in PREFERRED_DATATYPES:
        scores: list[tuple[FuzzyScore, FDCIngredient]] = []
        for fdc_ingredient in foundation_foods[data_type]:
            score = fuzzy_document_distance(
                tuple(ingredient_name_tokens),
                tuple(ingredient_token_pos),
                fdc_ingredient.tokens,
                fdc_ingredient.pos_tags,
            )
            scores.append((score, fdc_ingredient))

        if not scores:
            continue

        # Sort to find best score.
        # Sort is initially by FuzzyScore.full_score, then FuzzyScore.noun_score (if the
        # score is the same for more than one item).
        sorted_scores = sorted(scores, key=lambda x: x[0])
        best_score, best_fdc_match = sorted_scores[0]

        # If the best score is inf, return None
        if best_score.full_score == float("inf"):
            continue

        if best_score.full_score <= 0.25:
            return FoundationFood(
                text=best_fdc_match.description,
                confidence=round(1 - best_score.full_score, 6),
                fdc_id=best_fdc_match.fdc_id,
                category=best_fdc_match.category,
                data_type=best_fdc_match.data_type,
            )
        else:
            fallback_scores.append((best_score, best_fdc_match))

    if not fallback_scores:
        return None

    # Sort fallback matches based on best noun score
    sorted_fallback_scores = sorted(
        fallback_scores, key=lambda x: (x[0].noun_score, x[0].full_score)
    )
    best_fallback_score, best_fallback_fdc_match = sorted_fallback_scores[0]

    if best_fallback_score.full_score <= 0.4:
        return FoundationFood(
            text=best_fallback_fdc_match.description,
            confidence=round(1 - best_fallback_score.full_score, 6),
            fdc_id=best_fallback_fdc_match.fdc_id,
            category=best_fallback_fdc_match.category,
            data_type=best_fallback_fdc_match.data_type,
        )

    return None

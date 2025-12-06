#!/usr/bin/env python3


import logging

from ...dataclasses import FoundationFood
from ._ff_constants import FOUNDATION_FOOD_OVERRIDES
from ._ff_utils import (
    normalise_spelling,
    prepare_embeddings_tokens,
)
from ._fuzzy import get_fuzzy_matcher
from ._usif import get_usif_matcher

logger = logging.getLogger("ingredient-parser.foundation-foods")


def match_foundation_foods(tokens: list[str], name_idx: int) -> FoundationFood | None:
    """Match ingredient name to foundation foods from FDC ingredient.

    This is done in three stages.
    The first stage prepares and normalises the tokens.

    The second stage uses an Unsupervised Smooth Inverse Frequency calculation to down
    select the possible candidate matching FDC ingredients.

    The third stage selects the best of these candidates using a fuzzy embedding
    document metric.

    The need for two stages is that the ingredient embeddings do not seem to be as
    accurate as off the shelf pre-trained general embeddings are for general tasks.
    Improving the quality of the embeddings might remove the need for the second stage.

    Parameters
    ----------
    tokens : list[str]
        Ingredient name tokens.
    name_idx : int
        Index of corresponding name in ParsedIngredient.names list.

    Returns
    -------
    FoundationFood | None
    """
    logger.debug(f"Matching FDC ingredient for ingredient name tokens: {tokens}")
    prepared_tokens = prepare_embeddings_tokens(tuple(tokens))
    logger.debug(f"Prepared tokens: {prepared_tokens}.")
    if not prepared_tokens:
        logger.debug("Ingredient name has no tokens in embedding vocabulary.")
        return None

    normalised_tokens = normalise_spelling(prepared_tokens)

    if tuple(normalised_tokens) in FOUNDATION_FOOD_OVERRIDES:
        logger.debug("Returning FDC ingredient from override list.")
        match = FOUNDATION_FOOD_OVERRIDES[tuple(normalised_tokens)]
        match.name_index = name_idx
        return match

    u = get_usif_matcher()
    candidate_matches = u.find_candidate_matches(normalised_tokens, n=50)
    if not candidate_matches:
        logger.debug("No matching FDC ingredients found with uSIF matcher.")
        return None

    fuzzy = get_fuzzy_matcher()
    best_match = fuzzy.find_best_match(
        normalised_tokens, [m.fdc for m in candidate_matches]
    )

    if best_match.score <= 0.4:
        return FoundationFood(
            text=best_match.fdc.description,
            confidence=round(1 - best_match.score, 6),
            fdc_id=best_match.fdc.fdc_id,
            category=best_match.fdc.category,
            data_type=best_match.fdc.data_type,
            name_index=name_idx,
        )

    logger.debug("No FDC ingredients found with good enough match.")
    return None

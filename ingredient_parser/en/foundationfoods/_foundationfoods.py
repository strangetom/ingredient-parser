#!/usr/bin/env python3


import logging

from ingredient_parser.en.foundationfoods._ff_dataclasses import FDCIngredientMatch

from ...dataclasses import FoundationFood
from ._bm25 import get_bm25_matcher
from ._ff_constants import FOUNDATION_FOOD_OVERRIDES, NON_RAW_FOOD_VERB_STEMS
from ._ff_utils import (
    normalise_spelling,
    prepare_embeddings_tokens,
)
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

    # Bias the results towards selecting the raw version of a FDC ingredient, but
    # only if the ingredient name tokens don't already include a verb that indicates
    # the food is not raw (e.g. cooked)
    if len(set(normalised_tokens) & NON_RAW_FOOD_VERB_STEMS) == 0:
        normalised_tokens.append("raw")

    u = get_usif_matcher()
    usif_matches = u.score_matches(normalised_tokens)
    if not usif_matches:
        logger.debug("No matching FDC ingredients found with uSIF matcher.")
        return None

    bm25 = get_bm25_matcher()
    bm25_matches = bm25.score_matches(normalised_tokens)

    fused_matches = merge_matches(bm25_matches, usif_matches)
    best_match = fused_matches[0]

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


DATASET_PREFERENCE = [
    "survey_fndds_food",
    "sr_legacy_food",
    "foundation_food",
]


def merge_matches(
    bm25_matches: list[FDCIngredientMatch], usif_matches: list[FDCIngredientMatch]
) -> list[FDCIngredientMatch]:
    """Merge matches from BM25 and uSIF matchers using reciprocal rank fusion.


    Parameters
    ----------
    bm25_matches : list[FDCIngredientMatch]
        Matches return from BM25 matcher.
    usif_matches : list[FDCIngredientMatch]
        Matches return from uSIF matcher.

    Returns
    -------
    list[FDCIngredientMatch]
        Ordered list of matches.
    """
    # Create dict for uSIF matches for quickly looking up the rank of an entry by FDC ID
    usif_dict = {f.fdc.fdc_id: rank for rank, f in enumerate(usif_matches)}

    fused_matches = []
    for rank, match in enumerate(bm25_matches):
        fdc_id = match.fdc.fdc_id

        bm25_rank = 1 / (60 + rank)
        usif_rank = 1 / (60 + usif_dict[fdc_id])
        fused_rank = bm25_rank + usif_rank
        fused_matches.append(
            FDCIngredientMatch(
                fdc=match.fdc,
                score=fused_rank,
            )
        )

    # When resolving identical scores, prefer the ingredient with the word "raw" in it.
    return sorted(
        fused_matches,
        key=lambda x: (x.score, DATASET_PREFERENCE.index(x.fdc.data_type)),
        reverse=True,
    )

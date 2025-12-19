#!/usr/bin/env python3


import logging

import numpy as np

from ingredient_parser.en.foundationfoods._ff_dataclasses import (
    FDCIngredientMatch,
)

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
    print(normalised_tokens)

    u = get_usif_matcher()
    usif_matches = u.score_matches(normalised_tokens)
    if not usif_matches:
        logger.debug("No matching FDC ingredients found with uSIF matcher.")
        return None

    print("uSIF matches:")
    for m in usif_matches[:10]:
        print(f"{m.score}: {m.fdc.description}")
    print()

    bm25 = get_bm25_matcher()
    bm25_matches = bm25.score_matches(normalised_tokens)

    print("BM25 matches:")
    for m in bm25_matches[:10]:
        print(f"{m.score}: {m.fdc.description}")
    print()

    fused_matches = dbsf(bm25_matches, usif_matches)
    best_match = fused_matches[0]

    print("Fused matches:")
    for m in fused_matches[:10]:
        print(f"{m.score}: {m.fdc.description}")
    print()

    if best_match.score >= 0.4:
        return FoundationFood(
            text=best_match.fdc.description,
            confidence=round(best_match.score, 6),
            fdc_id=best_match.fdc.fdc_id,
            category=best_match.fdc.category,
            data_type=best_match.fdc.data_type,
            name_index=name_idx,
        )

    logger.debug("No FDC ingredients found with good enough match.")
    return None


def estimate_matcher_confidence(scores: list[float]) -> float:
    """Calculate confidence of a matcher function from the spread of scores.

    A larger gap between the best two scores indicates higher confidence. Beacuse the
    difference between the best two scores is considered relative to the best score,
    this approach will work for scores that have an arbitrary scale.

    Additionally, lower variance in the non-top scores also indicates higher confidence.

    The two metrics are combined to estimate the matcher confidence.

    Parameters
    ----------
    scores : list[float]
        List of matcher scores.

    Returns
    -------
    float
        Description
    """
    if len(scores) < 2:
        return 1.0

    sorted_scores = sorted(scores, reverse=True)
    max_score = sorted_scores[0]
    second_max = sorted_scores[1]

    gap = max_score - second_max
    relative_gap = gap / max_score

    if len(scores) > 2:
        # Calculate coefficient of variation for scores below top
        remaining_scores = sorted_scores[1:]
        remaining_std = np.std(remaining_scores)
        remaining_mean = np.mean(remaining_scores)
        if remaining_mean > 0:
            cv = remaining_std / remaining_mean
            # Lower CV = more concentrated = clearer winner
            distribution_factor = 1.0 / (1.0 + cv)
        else:
            distribution_factor = 1.0
    else:
        distribution_factor = 1.0

    # Combine gap and distribution (weighted average)
    confidence = 0.7 * relative_gap + 0.3 * distribution_factor
    return float(confidence)


def normalize_scores(scores: list[float]) -> list[float]:
    """Normalize list of scores.

    Parameters
    ----------
    scores : list[float]
        List of scores to normalize.

    Returns
    -------
    list[float]
        Normalized scores.
    """
    if not scores:
        return []

    scores_array = np.array(scores)

    # Handle case where all scores are identical
    if np.all(scores_array == scores_array[0]):
        return [0.5] * len(scores)

    # Use 5th and 95th percentiles to calculate normalization interval.
    min_ = min(scores_array)
    max_ = max(scores_array)
    # Ensure that the range is never 0
    range_val = max(max_ - min_, 1e-9)

    normalized = []
    for score in scores_array:
        norm_score = (score - min_) / range_val
        # Clip to [0, 1] to handle cases where range_val is really small.
        norm_score = max(0.0, min(1.0, norm_score))
        normalized.append(norm_score)

    return normalized


# List of FDC data preferences, least preferred to most preferred.
DATASET_PREFERENCE = [
    "survey_fndds_food",
    "sr_legacy_food",
    "foundation_food",
]


def dbsf(
    bm25_matches: list[FDCIngredientMatch],
    usif_matches: list[FDCIngredientMatch],
    top_n: int = 100,
) -> list[FDCIngredientMatch]:
    """Distribution-based score fusion of BM25 and uSIF match results.

    Fuse the matches from BM25 matcher and uSIF matcher by normalising their scores
    based on the score distribution statistics and summing the normalised scores for
    each match.

    The provided `bm25_matches` and `usif_matches` lists contain the raw scores for all
    possible FDC ingredients. We only consider the `top_n` of these to avoid the
    distribution statistics being skewed by the poor matches. This is beacuse there are
    far more poor matches than there are good matches.

    The fusing of the normalised scores for a match is weighted by the confidence of
    each matcher. If a matcher has one score significantly higher than all others, then
    it is more confidence and we account for that be increasing the confidence in that
    matcher.

    References
    ----------
    .. [1] D. Kim, B. Kim, D. Han, and M. Eibich, ‘AutoRAG: Automated Framework for
    optimization of Retrieval Augmented Generation Pipeline’, Oct. 28, 2024,
    arXiv: arXiv:2410.20878. doi: 10.48550/arXiv.2410.20878.

    Parameters
    ----------
    bm25_matches : list[FDCIngredientMatch]
        List of FDCIngredientMatch from the BM25 matcher.
    usif_matches : list[FDCIngredientMatch]
        List of FDCIngredientMatch from the uSIF matcher.
    top_n : int, optional
        Number of top matches to consider.

    Returns
    -------
    list[FDCIngredientMatch]
        List of FDCIngredientMatch ordered best to worse.
    """
    # Limit to best `top_n` results to prevent the normalisation being dominated by poor
    # matches.
    bm25_matches = bm25_matches[:top_n]
    usif_matches = usif_matches[:top_n]

    # Estimate matcher confidences based on spread of (unnormalised) scores
    bm25_conf = estimate_matcher_confidence([m.score for m in bm25_matches])
    usif_conf = estimate_matcher_confidence([m.score for m in usif_matches])
    total_conf = bm25_conf + usif_conf
    bm25_conf = bm25_conf / total_conf * 2
    usif_conf = usif_conf / total_conf * 2

    # Normalize both score distributions
    bm25_normalized = normalize_scores([m.score for m in bm25_matches])
    print("BM25 normalised scores:")
    for s in bm25_normalized[:10]:
        print(f"{s}")
    print()
    usif_normalized = normalize_scores([m.score for m in usif_matches])
    print("uSIF normalised scores:")
    for s in usif_normalized[:10]:
        print(f"{1 - s}")
    print()

    # Create dict mapping fdc_id to normalized score
    usif_dict = {
        match.fdc.fdc_id: norm_score
        for match, norm_score in zip(usif_matches, usif_normalized)
    }
    bm25_dict = {
        match.fdc.fdc_id: norm_score
        for match, norm_score in zip(bm25_matches, bm25_normalized)
    }

    fused_matches = []
    fdc_entries = set(m.fdc for m in bm25_matches) | set(m.fdc for m in usif_matches)
    for fdc in fdc_entries:
        bm25_norm_score = bm25_dict.get(fdc.fdc_id, 0)
        # uSIF scores are inverted (i.e. smaller = better). Therefore, after
        # normalisation, subtract from one to make bigger = better.
        usif_norm_score = 1 - usif_dict.get(fdc.fdc_id, 1)

        fused_score = bm25_conf * bm25_norm_score + usif_conf * usif_norm_score
        fused_matches.append(FDCIngredientMatch(fdc=fdc, score=float(fused_score / 2)))

    # When resolving identical scores, use the preferred dataset.
    return sorted(
        fused_matches,
        key=lambda x: (x.score, DATASET_PREFERENCE.index(x.fdc.data_type)),
        reverse=True,
    )

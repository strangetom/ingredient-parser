#!/usr/bin/env python3


import logging

import numpy as np

from ingredient_parser.en._loaders import load_embeddings_model
from ingredient_parser.en.foundationfoods._ff_dataclasses import (
    FDCIngredient,
    FDCIngredientMatch,
)

from ...dataclasses import FoundationFood
from ._bm25 import get_bm25_ranker
from ._ff_constants import (
    FOUNDATION_FOOD_OVERRIDES,
    NON_RAW_FOOD_NOUN_STEMS,
    NON_RAW_FOOD_VERB_STEMS,
)
from ._ff_dataclasses import IngredientToken
from ._ff_utils import (
    normalise_spelling,
    prepare_tokens,
    strip_ambiguous_leading_adjectives,
)
from ._fuzzy import get_fuzzy_ranker
from ._usif import get_usif_ranker

logger = logging.getLogger("ingredient-parser.foundation-foods")

# Constant defining the top k matches to use wherever we limit the matches considered.
TOP_K = 50

# List of FDC data preferences, least preferred to most preferred.
DATASET_PREFERENCE = [
    "survey_fndds_food",
    "sr_legacy_food",
    "foundation_food",
]


def match_foundation_foods(
    tokens: list[str], pos_tags: list[str], name_idx: int
) -> FoundationFood | None:
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
    pos_tags : list[str]
        POS tags for tokens.
    name_idx : int
        Index of corresponding name in ParsedIngredient.names list.

    Returns
    -------
    FoundationFood | None
    """
    name_tokens = [IngredientToken(token, tag) for token, tag in zip(tokens, pos_tags)]

    name_tokens = strip_ambiguous_leading_adjectives(name_tokens)
    logger.debug(f"Matching FDC ingredient for ingredient name tokens: {tokens}")
    prepared_tokens = prepare_tokens(tuple(name_tokens))
    if not prepared_tokens:
        logger.debug("Ingredient name has no tokens valid for matching.")
        return None
    else:
        logger.debug(f"Prepared tokens: {prepared_tokens}.")

    normalised_tokens = normalise_spelling(prepared_tokens)

    if tuple([t.token for t in normalised_tokens]) in FOUNDATION_FOOD_OVERRIDES:
        logger.debug("Returning FDC ingredient from override list.")
        match = FOUNDATION_FOOD_OVERRIDES[tuple([t.token for t in normalised_tokens])]
        match.name_index = name_idx
        return match

    # Determine if there any of the normalised tokens are in the embeddings model.
    # If not, we will skip the semantic (embeddings based) rankers.
    embeddings = load_embeddings_model()
    normalised_embeddings_tokens = [
        t for t in normalised_tokens if t.token in embeddings
    ]
    has_tokens_in_embeddings = len(normalised_embeddings_tokens) > 0
    if not has_tokens_in_embeddings:
        logger.debug(
            (
                "Skipping semantic rankers (uSIF, Fuzzy) because ingredient name "
                "does not contain any tokens present in the embeddings model."
            )
        )

    # Bias the results towards selecting the raw version of a FDC ingredient, but
    # only if the ingredient name tokens don't already include a verb or noun that
    # indicates the food is not raw (e.g. cooked)
    if (
        len(set(normalised_tokens) & NON_RAW_FOOD_VERB_STEMS) == 0
        and len(set(normalised_tokens) & NON_RAW_FOOD_NOUN_STEMS) == 0
    ):
        logger.debug("Biasing tokens towards raw FDC ingredients.")
        normalised_tokens.append(IngredientToken("raw", "JJ"))
        normalised_embeddings_tokens.append(IngredientToken("raw", "JJ"))

    bm25 = get_bm25_ranker()
    bm25_matches = bm25.rank_matches(normalised_tokens)
    print("BM25 matches:")
    for m in bm25_matches[:10]:
        print(f"{m.score:.4f}: {m.fdc.description}")
    print()

    if not has_tokens_in_embeddings:
        # No other possible matching techniques, so just pick the best from BM25.
        best_match = bm25_matches[0]
        return FoundationFood(
            text=best_match.fdc.description,
            confidence=1.0,
            fdc_id=best_match.fdc.fdc_id,
            category=best_match.fdc.category,
            data_type=best_match.fdc.data_type,
            name_index=name_idx,
        )

    usif_matches = []
    if has_tokens_in_embeddings:
        u = get_usif_ranker()
        usif_matches = u.rank_matches(normalised_embeddings_tokens)
        print("uSIF matches:")
        for m in usif_matches[:10]:
            print(f"{m.score:.4f}: {m.fdc.description}")
        print()

    # Check if both BM25 and uSIF agree on the top result. If they do, return that and
    # avoid any further processing.
    if fdc := consistent_top_result(bm25_matches, usif_matches):
        logger.debug(f"BM25 and uSIF rankers agree on best match: {fdc.fdc_id=}")
        return FoundationFood(
            text=fdc.description,
            confidence=1.0,
            fdc_id=fdc.fdc_id,
            category=fdc.category,
            data_type=fdc.data_type,
            name_index=name_idx,
        )

    fuzzy_matches = []
    agreement = bm25_usif_agreement(bm25_matches, usif_matches)
    if has_tokens_in_embeddings and agreement < 0.25:
        # Get all FDC IDs for BM25 and uSIF matches
        # We'll only use the fuzzy ranker on these, instead of the whole FDC set.
        candidate_fdc_ids = {m.fdc.fdc_id for m in usif_matches[:TOP_K]} | {
            m.fdc.fdc_id for m in bm25_matches[:TOP_K]
        }
        logger.debug(f"BM25 and uSIF ranker alignment is < 0.25 ({agreement:.4f}).")
        logger.debug(
            (
                f"Using FuzzyMatcher on {TOP_K} matches from "
                "BM25 and uSIF to help arbitrate."
            )
        )

        fuzzy = get_fuzzy_ranker()
        fuzzy_matches = fuzzy.rank_matches(
            normalised_embeddings_tokens, candidate_fdc_ids
        )
        print("Fuzzy matches:")
        for m in fuzzy_matches[:10]:
            print(f"{m.score:.4f}: {m.fdc.description}")
        print()

    fused_matches = fuse_results(bm25_matches, fuzzy_matches, usif_matches, top_n=TOP_K)
    best_match = fused_matches[0]
    print("Fused matches:")
    for m in fused_matches[:10]:
        print(f"{m.score:.4f}: {m.fdc.description} ({m.fdc.data_type})")
    print()

    # If the there is less than 1% difference in score between the best two fused
    # matches, then assume we can't identify a suitable match.
    # Only do this if the best fused score is less than 0.95 so we don't discard good
    # matches.
    # However, if there is a 0% difference in score (i.e. same score), then we just
    # select the first because fused_matches are already sorted in order of preferred
    # dataset.
    top_pc_diff = percent_difference(fused_matches[0].score, fused_matches[1].score)
    if best_match.score < 0.95 and 0 < top_pc_diff <= 0.01:
        logger.debug("No FDC ingredients found with good enough match.")
        return None

    if top_pc_diff == 0:
        # Check how many results have the same top score. If it's more than 3 (i.e. more
        # than one from each data set) then we have no idea.
        matches_with_top_score = sum(
            1 for m in fused_matches if m.score == best_match.score
        )
        if matches_with_top_score > len(DATASET_PREFERENCE):
            logger.debug(
                (
                    f"Top score shared by {matches_with_top_score} FDC entries "
                    "therefore cannot determine suitable match."
                )
            )
            return None

    return FoundationFood(
        text=best_match.fdc.description,
        confidence=best_match.score,  # Note: already rounded by fuse_results
        fdc_id=best_match.fdc.fdc_id,
        category=best_match.fdc.category,
        data_type=best_match.fdc.data_type,
        name_index=name_idx,
    )


def consistent_top_result(
    bm25_matches: list[FDCIngredientMatch], usif_matches: list[FDCIngredientMatch]
) -> FDCIngredient | None:
    """If the BM25 and uSIF matches have a single consistent best match, return it.
    Otherwise return None.

    It is possible (particularly for BM25) for there to be more than one best match with
    the same score, so this function accounts for that.

    Parameters
    ----------
    bm25_matches : list[FDCIngredientMatch]
        List of FDCIngredientMatch from the BM25 ranker.
    usif_matches : list[FDCIngredientMatch]
        List of FDCIngredientMatch from the uSIF ranker.

    Returns
    -------
    FDCIngredient | None
    """
    best_matches = set()

    # Because bm25_matches and usif_matches are ordered, we want to stop iterating over
    # them as soon as we encounter a score that is different from the best score.
    best_matches.add(bm25_matches[0].fdc)
    best_score = bm25_matches[0].score
    for m in bm25_matches[1:]:
        if m.score == best_score:
            best_matches.add(m.fdc)
        else:
            break

    best_matches.add(usif_matches[0].fdc)
    best_score = usif_matches[0].score
    for m in usif_matches[1:]:
        if m.score == best_score:
            best_matches.add(m.fdc)
        else:
            break

    if len(best_matches) == 1:
        # If there is exactly one FDC Ingredient in the intersection, return it.
        return best_matches.pop()

    # If there are no items in the intersection, or more than one, return None.
    return None


def percent_difference(score1: float, score2: float) -> float:
    """Calculate the percentage difference between two scores.

    Parameters
    ----------
    score1 : float
        First score.
    score2 : float
        Second score

    Returns
    -------
    float
        Percentage difference score, [0 1].
    """
    if score1 == score2:
        return 0

    max_score = max(score1, score2)
    min_score = min(score1, score2)
    delta = max_score - min_score
    return delta / max_score


def bm25_usif_agreement(
    bm25_matches: list[FDCIngredientMatch],
    usif_matches: list[FDCIngredientMatch],
    p: float = 0.95,
) -> float:
    """Calculate the agreement between the BM25 and uSIF matches.

    Rank Biased Overlap [1]_ is used to calculate a metric quantifying the overlap as a
    score between 0 and 1.

    The parameter p determines how steep the decline in weights is: the smaller p, the
    more top-weighted the metric is. In the limit, when p = 0, only the top-ranked item
    is considered, and the RBO score is either zero or one. On the other hand, as p
    approaches arbitrarily close to 1, the weights become arbitrarily flat, and the
    evaluation becomes arbitrarily deep.

    This implementation assumes that both input lists are the same length. If they
    aren't then this function isn't appropriate and RBO_EXT should be considered.

    References
    ----------
    .. [1] W. Webber, A. Moffat, and J. Zobel, ‘A similarity measure for indefinite
           rankings’, ACM Trans. Inf. Syst., vol. 28, no. 4, pp. 1–38, Nov. 2010,
           doi: 10.1145/1852102.1852106.

    Parameters
    ----------
    bm25_matches : list[FDCIngredientMatch]
        List of ordered matches from BM25 ranker.
    usif_matches : list[FDCIngredientMatch]
        List of ordered matches from uSIF ranker.
    p : float
        Persistence parameter (0 < p < 1).
        The expected depth is given by 1/(1 - p).
        Default is 0.95 -> expected depth ~20.

    Returns
    -------
    float
        Agreement score, between 0 and 1, where 1 is exact agreement.
    """
    if p < 0 or p > 1:
        raise ValueError(f"p should be between 0 and 1. Provided value is {p}.")

    bm25_ids = [m.fdc.fdc_id for m in bm25_matches[:TOP_K]]
    usif_ids = [m.fdc.fdc_id for m in usif_matches[:TOP_K]]

    bm25_set = set()
    usif_set = set()
    rbo_sum = 0
    for depth in range(1, len(bm25_ids) + 1):
        bm25_set.add(bm25_ids[depth - 1])
        usif_set.add(usif_ids[depth - 1])

        # Calculate overlap at current depth.
        overlap = len(bm25_set & usif_set)

        agreement = overlap / depth
        rbo_sum += agreement * (p**depth)

    # This provides the base RBO for the common length
    return (1 - p) * rbo_sum


def estimate_ranker_confidence(scores: list[float]) -> float:
    """Calculate confidence of a ranker function from the spread of scores.

    A larger gap between the best two scores indicates higher confidence. Because the
    difference between the best two scores is considered relative to the best score,
    this approach will work for scores that have an arbitrary scale.

    .. note::

      We use the top two *different* scores, not the top two scores.
      If there is more than one result with the same top score, we shouldn't take that
      to mean low confidence because that will result in down-weighting potentially good
      matches.

    Additionally, lower variance in the non-top scores also indicates higher confidence.

    The two metrics are combined to estimate the ranker confidence.

    Parameters
    ----------
    scores : list[float]
        List of ranker scores.

    Returns
    -------
    float
        Description
    """
    if len(scores) < 2:
        return 0

    sorted_scores = sorted(scores, reverse=True)
    max_score = sorted_scores[0]
    second_max = 0
    for score in scores:
        if score != max_score:
            second_max = score

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


def fuse_results(
    bm25_matches: list[FDCIngredientMatch],
    fuzzy_matches: list[FDCIngredientMatch],
    usif_matches: list[FDCIngredientMatch],
    top_n: int = 100,
) -> list[FDCIngredientMatch]:
    """Distribution-based score fusion of BM25 and uSIF match results.

    Fuse the matches from BM25 ranker and uSIF ranker by normalising their scores
    based on the score distribution statistics and summing the normalised scores for
    each match.

    The provided `bm25_matches` and `usif_matches` lists contain the raw scores for all
    possible FDC ingredients. We only consider the `top_n` of these to avoid the
    distribution statistics being skewed by the poor matches. This is because there are
    far more poor matches than there are good matches.

    The fusing of the normalised scores for a match is weighted by the confidence of
    each ranker. If a ranker has one score significantly higher than all others, then
    it is more confidence and we account for that be increasing the confidence in that
    ranker.

    References
    ----------
    .. [1] D. Kim, B. Kim, D. Han, and M. Eibich, ‘AutoRAG: Automated Framework for
    optimization of Retrieval Augmented Generation Pipeline’, Oct. 28, 2024,
    arXiv: arXiv:2410.20878. doi: 10.48550/arXiv.2410.20878.

    Parameters
    ----------
    bm25_matches : list[FDCIngredientMatch]
        List of FDCIngredientMatch from the BM25 ranker.
    fuzzy_matches : list[FDCIngredientMatch]
        List of FDCIngredientMatch from the Fuzzy ranker.
    usif_matches : list[FDCIngredientMatch]
        List of FDCIngredientMatch from the uSIF ranker.
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
    fuzzy_matches = fuzzy_matches[:top_n]

    # Normalize both score distributions
    bm25_normalized = normalize_scores([m.score for m in bm25_matches])
    usif_normalized = normalize_scores([m.score for m in usif_matches])
    fuzzy_normalized = normalize_scores([m.score for m in fuzzy_matches])

    # Create dict mapping fdc_id to normalized score
    usif_dict = {
        match.fdc.fdc_id: norm_score
        for match, norm_score in zip(usif_matches, usif_normalized)
    }
    fuzzy_dict = {
        match.fdc.fdc_id: norm_score
        for match, norm_score in zip(fuzzy_matches, fuzzy_normalized)
    }
    bm25_dict = {
        match.fdc.fdc_id: norm_score
        for match, norm_score in zip(bm25_matches, bm25_normalized)
    }

    # Estimate ranker confidences based on spread of normalised scores.
    bm25_conf = estimate_ranker_confidence(bm25_normalized)
    fuzzy_conf = estimate_ranker_confidence(fuzzy_normalized)
    usif_conf = estimate_ranker_confidence(usif_normalized)
    total_conf = bm25_conf + usif_conf + fuzzy_conf
    bm25_conf = bm25_conf / total_conf * 3
    fuzzy_conf = fuzzy_conf / total_conf * 3
    usif_conf = usif_conf / total_conf * 3
    logger.debug(
        (
            f"Ranker confidences: "
            f"BM25={bm25_conf:.4f}, "
            f"uSIF={usif_conf:.4f}, "
            f"Fuzzy={fuzzy_conf:.4f}."
        )
    )

    fused_matches = []
    fdc_entries = set(m.fdc for m in bm25_matches) | set(m.fdc for m in usif_matches)
    for fdc in fdc_entries:
        bm25_norm_score = bm25_dict.get(fdc.fdc_id, 0)
        # uSIF and Fuzzy scores are inverted (i.e. smaller = better). Therefore, after
        # normalisation, subtract from one to make bigger = better.
        usif_norm_score = 1 - usif_dict.get(fdc.fdc_id, 1)
        fuzzy_norm_score = 1 - fuzzy_dict.get(fdc.fdc_id, 1)

        fused_score = (
            bm25_conf * bm25_norm_score
            + usif_conf * usif_norm_score
            + fuzzy_conf * fuzzy_norm_score
        )
        fused_matches.append(
            FDCIngredientMatch(fdc=fdc, score=float(round(fused_score / 3, 6)))
        )

    # When resolving identical scores, use the preferred dataset.
    return sorted(
        fused_matches,
        key=lambda x: (x.score, DATASET_PREFERENCE.index(x.fdc.data_type)),
        reverse=True,
    )

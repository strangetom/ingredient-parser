#!/usr/bin/env python3

from importlib.resources import as_file, files

import pycrfsuite

from .._common import group_consecutive_idx
from ..dataclasses import ParsedIngredient, ParserDebugInfo
from ._foundationfoods import extract_foundation_foods
from ._utils import pluralise_units
from .postprocess import PostProcessor
from .preprocess import PreProcessor

# Create TAGGER object that can be reused between function calls.
# We only want to load the model into TAGGER once, but only do it
# when we need to (from parse_ingredient() or inspect_parser()) and
# not whenever anything from ingredient_parser is imported.
TAGGER = pycrfsuite.Tagger()  # type: ignore


def load_model_if_not_loaded():
    """Load model into TAGGER variable if not loaded.

    There isn't a simple way to check if the model if loaded or not, so
    we try to call TAGGER.labels() which will raise a ValueError if the
    model is not loaded yet.
    """
    try:
        TAGGER.labels()
    except ValueError:
        with as_file(files(__package__) / "model.en.crfsuite") as p:
            TAGGER.open(str(p))


def parse_ingredient_en(
    sentence: str,
    discard_isolated_stop_words: bool = True,
    expect_name_in_output: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
    quantity_fractions: bool = False,
    foundation_foods: bool = False,
) -> ParsedIngredient:
    """Parse an English language ingredient sentence to return structured data.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse
    discard_isolated_stop_words : bool, optional
        If True, any isolated stop words in the name, preparation, or comment fields
        are discarded.
        Default is True.
    expect_name_in_output : bool, optional
        If True, if the model doesn't label any words in the sentence as the name,
        fallback to selecting the most likely name from all tokens even though the
        model gives it a different label. Note that this does guarantee the output
        contains a name.
        Default is True.
    string_units : bool, optional
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Default is False.
    imperial_units : bool, optional
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.
    quantity_fractions: bool, optional
        If True, IngredientAmount quantities are returned as fractions.Fraction objects.
        Default is False, where quantities are returned as floats rounded to 3 decimal
        places.
    foundation_foods : bool, optional
        If True, extract foundation foods from ingredient name. Foundation foods are
        the fundamental foods without any descriptive terms, e.g. 'cucumber' instead
        of 'organic cucumber'.
        Default is False.

    Returns
    -------
    ParsedIngredient
        ParsedIngredient object of structured data parsed from input string
    """
    load_model_if_not_loaded()

    processed_sentence = PreProcessor(sentence)
    tokens = processed_sentence.tokenized_sentence
    features = processed_sentence.sentence_features()
    labels = TAGGER.tag(features)
    scores = [TAGGER.marginal(label, i) for i, label in enumerate(labels)]

    # Re-pluralise tokens that were singularised if the label isn't UNIT
    # For tokens with UNIT label, we'll deal with them below
    for idx in processed_sentence.singularised_indices:
        token = tokens[idx]
        label = labels[idx]
        if label != "UNIT":
            tokens[idx] = pluralise_units(token)

    if expect_name_in_output and all(label != "NAME" for label in labels):
        # No tokens were assigned the NAME label, so guess if there's a name
        labels, scores = guess_ingredient_name(labels, scores)

    postprocessed_sentence = PostProcessor(
        sentence,
        tokens,
        labels,
        scores,
        discard_isolated_stop_words=discard_isolated_stop_words,
        string_units=string_units,
        imperial_units=imperial_units,
        quantity_fractions=quantity_fractions,
    )
    parsed = postprocessed_sentence.parsed

    if foundation_foods and parsed.name:
        parsed.foundation_foods = extract_foundation_foods(tokens, labels, features)

    return parsed


def inspect_parser_en(
    sentence: str,
    discard_isolated_stop_words: bool = True,
    expect_name_in_output: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
    quantity_fractions: bool = False,
    foundation_foods: bool = False,
) -> ParserDebugInfo:
    """Return intermediate objects generated during parsing for inspection.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse
    discard_isolated_stop_words : bool, optional
        If True, any isolated stop words in the name, preparation, or comment fields
        are discarded.
        Default is True.
    expect_name_in_output : bool, optional
        If True, if the model doesn't label any words in the sentence as the name,
        fallback to selecting the most likely name from all tokens even though the
        model gives it a different label. Note that this does guarantee the output
        contains a name.
        Default is True.
    string_units : bool, optional
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Default is False.
    imperial_units : bool, optional
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.
    quantity_fractions: bool, optional
        If True, IngredientAmount quantities are returned as fractions.Fraction objects.
        Default is False, where quantities are returned as floats rounded to 3 decimal
        places.
    foundation_foods : bool, optional
        If True, extract foundation foods from ingredient name. Foundation foods are
        the fundamental foods without any descriptive terms, e.g. 'cucumber' instead
        of 'organic cucumber'.
        Default is False.

    Returns
    -------
    ParserDebugInfo
        ParserDebugInfo object containing the PreProcessor object, PostProcessor
        object and Tagger.
    """
    load_model_if_not_loaded()

    processed_sentence = PreProcessor(sentence)
    tokens = processed_sentence.tokenized_sentence
    features = processed_sentence.sentence_features()
    labels = TAGGER.tag(features)
    scores = [TAGGER.marginal(label, i) for i, label in enumerate(labels)]

    # Re-plurise tokens that were singularised if the label isn't UNIT
    # For tokens with UNIT label, we'll deal with them below
    for idx in processed_sentence.singularised_indices:
        token = tokens[idx]
        label = labels[idx]
        if label != "UNIT":
            tokens[idx] = pluralise_units(token)

    if expect_name_in_output and all(label != "NAME" for label in labels):
        # No tokens were assigned the NAME label, so guess if there's a name
        labels, scores = guess_ingredient_name(labels, scores)

    postprocessed_sentence = PostProcessor(
        sentence,
        tokens,
        labels,
        scores,
        discard_isolated_stop_words=discard_isolated_stop_words,
        string_units=string_units,
        imperial_units=imperial_units,
        quantity_fractions=quantity_fractions,
    )

    parsed = postprocessed_sentence.parsed
    if foundation_foods and parsed.name:
        foundation = extract_foundation_foods(tokens, labels, features)
    else:
        foundation = []

    return ParserDebugInfo(
        sentence=sentence,
        PreProcessor=processed_sentence,
        PostProcessor=postprocessed_sentence,
        foundation_foods=foundation,
        tagger=TAGGER,
    )


def guess_ingredient_name(
    labels: list[str], scores: list[float], min_score: float = 0.2
) -> tuple[list[str], list[float]]:
    """Guess ingredient name from list of labels and scores.

    This only applies if the token labeling resulted in no tokens being assigned the
    NAME label. When this happens, calculate the confidence of each token being NAME,
    and select the most likely value where the confidence is greater than min_score.
    If there are consecutive tokens that meet that criteria, give them all the NAME
    label.

    Parameters
    ----------
    labels : list[str]
        List of labels
    scores : list[float]
        List of scores
    min_score : float
        Minimum score to consider as candidate name

    Returns
    -------
    list[str], list[float]
        Labels and scores, modified to assign a name if possible.
    """
    # Calculate confidence of each token being labelled NAME and get indices where that
    # confidence is greater than min_score.
    name_scores = [TAGGER.marginal("NAME", i) for i, _ in enumerate(labels)]
    candidate_indices = [i for i, score in enumerate(name_scores) if score >= min_score]

    if len(candidate_indices) == 0:
        return labels, scores

    # Group candidate indices into groups of consecutive indices and order by longest
    groups = [list(group) for group in group_consecutive_idx(candidate_indices)]

    # Take longest group
    indices = sorted(groups, key=len)[0]
    for i in indices:
        labels[i] = "NAME"
        scores[i] = name_scores[i]

    return labels, scores

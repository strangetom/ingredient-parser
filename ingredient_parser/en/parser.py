#!/usr/bin/env python3

from .._common import group_consecutive_idx
from ..dataclasses import ParsedIngredient, ParserDebugInfo
from ._loaders import load_parser_model
from ._utils import pluralise_units
from .postprocess import PostProcessor
from .preprocess import PreProcessor


def parse_ingredient_en(
    sentence: str,
    separate_names: bool = True,
    discard_isolated_stop_words: bool = True,
    expect_name_in_output: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
    foundation_foods: bool = False,
) -> ParsedIngredient:
    """Parse an English language ingredient sentence to return structured data.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse.
    separate_names : bool, optional
        If True and the sentence contains multiple alternative ingredients, return an
        IngredientText object for each ingredient name, otherwise return a single
        IngredientText object.
        Default is True.
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
    TAGGER = load_parser_model()

    processed_sentence = PreProcessor(sentence)
    tokens = [t.text for t in processed_sentence.tokenized_sentence]
    pos_tags = [t.pos_tag for t in processed_sentence.tokenized_sentence]
    features = processed_sentence.sentence_features()
    labels = TAGGER.tag(features)
    scores = [TAGGER.marginal(label, i) for i, label in enumerate(labels)]

    if expect_name_in_output and all("NAME" not in label for label in labels):
        # No tokens were assigned the NAME label, so guess if there's a name
        labels, scores = guess_ingredient_name(TAGGER, labels, scores)

    # Re-pluralise tokens that were singularised if the label isn't UNIT
    # For tokens with UNIT label, we'll deal with them below
    for idx in processed_sentence.singularised_indices:
        token = tokens[idx]
        label = labels[idx]
        if label != "UNIT":
            tokens[idx] = pluralise_units(token)

    postprocessed_sentence = PostProcessor(
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        separate_names=separate_names,
        discard_isolated_stop_words=discard_isolated_stop_words,
        string_units=string_units,
        imperial_units=imperial_units,
        foundation_foods=foundation_foods,
    )
    parsed = postprocessed_sentence.parsed

    return parsed


def inspect_parser_en(
    sentence: str,
    separate_names: bool = True,
    discard_isolated_stop_words: bool = True,
    expect_name_in_output: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
    foundation_foods: bool = False,
) -> ParserDebugInfo:
    """Return intermediate objects generated during parsing for inspection.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse.
    separate_names : bool, optional
        If True and the sentence contains multiple alternative ingredients, return an
        IngredientText object for each ingredient name, otherwise return a single
        IngredientText object.
        Default is True.
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
    TAGGER = load_parser_model()

    processed_sentence = PreProcessor(sentence)
    tokens = [t.text for t in processed_sentence.tokenized_sentence]
    pos_tags = [t.pos_tag for t in processed_sentence.tokenized_sentence]
    features = processed_sentence.sentence_features()
    labels = TAGGER.tag(features)
    scores = [TAGGER.marginal(label, i) for i, label in enumerate(labels)]

    if expect_name_in_output and all("NAME" not in label for label in labels):
        # No tokens were assigned the NAME label, so guess if there's a name
        labels, scores = guess_ingredient_name(TAGGER, labels, scores)

    # Re-plurise tokens that were singularised if the label isn't UNIT
    # For tokens with UNIT label, we'll deal with them below
    for idx in processed_sentence.singularised_indices:
        token = tokens[idx]
        label = labels[idx]
        if label != "UNIT":
            tokens[idx] = pluralise_units(token)

    postprocessed_sentence = PostProcessor(
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        separate_names=separate_names,
        discard_isolated_stop_words=discard_isolated_stop_words,
        string_units=string_units,
        imperial_units=imperial_units,
        foundation_foods=foundation_foods,
    )

    return ParserDebugInfo(
        sentence=sentence,
        PreProcessor=processed_sentence,
        PostProcessor=postprocessed_sentence,
        tagger=TAGGER,
    )


def guess_ingredient_name(
    TAGGER, labels: list[str], scores: list[float], min_score: float = 0.2
) -> tuple[list[str], list[float]]:
    """Guess ingredient name from list of labels and scores.

    This only applies if the token labeling resulted in no tokens being assigned the
    NAME label. When this happens, calculate the confidence of each token being NAME,
    and select the most likely value where the confidence is greater than min_score.
    If there are consecutive tokens that meet that criteria, give them all the NAME
    label.

    Parameters
    ----------
    TAGGER : pycrfsuite.Tagger
        Tagger object for parser model.
    labels : list[str]
        List of token labels.
    scores : list[float]
        List of scores.
    min_score : float
        Minimum score to consider as candidate name.

    Returns
    -------
    list[str], list[float]
        Labels and scores, modified to assign a name if possible.
    """
    NAME_LABELS = [
        "B_NAME_TOK",
        "I_NAME_TOK",
        "NAME_VAR",
        "NAME_MOD",
        "NAME_SEP",
    ]

    # Calculate the most likely *NAME* label get store the indices where the score is
    # greater than min_score.
    candidate_indices = []
    candidate_score_labels = []  # List of (score, label) tuples
    for i, _ in enumerate(labels):
        alt_label_scores = [(TAGGER.marginal(label, i), label) for label in NAME_LABELS]
        max_score = max(alt_label_scores, key=lambda x: x[0])
        if max_score[0] > min_score:
            candidate_indices.append(i)
            candidate_score_labels.append(max_score)

    if len(candidate_indices) == 0:
        return labels, scores

    # Group candidate indices into groups of consecutive indices and order by longest
    groups = [list(group) for group in group_consecutive_idx(candidate_indices)]

    # Take longest group
    indices = sorted(groups, key=len)[0]
    for list_index, token_index in enumerate(indices):
        score, label = candidate_score_labels[list_index]
        labels[token_index] = label
        scores[token_index] = score

    return labels, scores

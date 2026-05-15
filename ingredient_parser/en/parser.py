#!/usr/bin/env python3

import logging

from .._common import group_consecutive_idx
from ..dataclasses import LabelledToken, ParsedIngredient, ParserDebugInfo
from ._loaders import load_parser_model
from .postprocess import PostProcessor
from .preprocess import PreProcessor

logger = logging.getLogger("ingredient-parser")


def parse_ingredient_en(
    sentence: str,
    separate_names: bool = True,
    discard_isolated_stop_words: bool = True,
    expect_name_in_output: bool = True,
    string_units: bool = False,
    volumetric_units_system: str = "us_customary",
    foundation_foods: bool = False,
    custom_units: dict[str, str] | None = None,
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
    volumetric_units_system : str, optional
        Sets the units system for volumetric measurements, like "cup" or "tablespoon".
        Available options are "us_customary" (default), "imperial", "metric",
        "australian", "japanese".
        This has no effect if string_units=True.
    foundation_foods : bool, optional
        If True, extract foundation foods from ingredient name. Foundation foods are
        the fundamental foods without any descriptive terms, e.g. 'cucumber' instead
        of 'organic cucumber'.
        Default is False.
    custom_units : dict[str, str] | None, optional
        Provide custom units to aid the parser in identifying units.
        The custom units should be provided as a dict of plural: singular pairs.
        If a unit does not have a plural form, provide the singular form as the key.
        The units should not start with a capital letter, but may contain capital
        letters at other positions.

    Returns
    -------
    ParsedIngredient
        ParsedIngredient object of structured data parsed from input string.
    """
    logger.debug(f'Parsing sentence "{sentence}" using "en" parser.')
    TAGGER = load_parser_model()

    if custom_units is None:
        custom_units = {}

    # Generate capitalized version of each entry in the custom units dictionary
    _capitalized_units = {}
    for plural, singular in custom_units.items():
        _capitalized_units[plural.capitalize()] = singular.capitalize()
    custom_units = custom_units | _capitalized_units

    processed_sentence = PreProcessor(sentence, custom_units=custom_units)
    features = processed_sentence.sentence_features()
    labels, scores = zip(*TAGGER.tag_from_features(features))
    labels = list(labels)
    scores = list(scores)
    logger.debug(f"Sentence token labels: {labels}.")

    if expect_name_in_output and all("NAME" not in label for label in labels):
        # No tokens were assigned the NAME label, so guess if there's a name
        logger.debug("No tokens found where name is most probable label.")
        labels, scores = guess_ingredient_name(TAGGER, labels, scores)

    labelled_tokens = [
        LabelledToken(
            index=token.index,
            text=token.text,
            pos_tag=token.pos_tag,
            label=label,
            score=score,
            plural=token.index in processed_sentence.singularised_indices,
        )
        for token, label, score in zip(
            processed_sentence.tokenized_sentence, labels, scores
        )
    ]

    postprocessed_sentence = PostProcessor(
        sentence,
        labelled_tokens,
        custom_units=custom_units,
        separate_names=separate_names,
        discard_isolated_stop_words=discard_isolated_stop_words,
        string_units=string_units,
        volumetric_units_system=volumetric_units_system,
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
    volumetric_units_system: str = "us_customary",
    foundation_foods: bool = False,
    custom_units: dict[str, str] | None = None,
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
    volumetric_units_system : str, optional
        Sets the units system for volumetric measurements, like "cup" or "tablespoon".
        Available options are "us_customary" (default), "imperial", "metric",
        "australian", "japanese".
        This has no effect if string_units=True.
    foundation_foods : bool, optional
        If True, extract foundation foods from ingredient name. Foundation foods are
        the fundamental foods without any descriptive terms, e.g. 'cucumber' instead
        of 'organic cucumber'.
        Default is False.
    custom_units : dict[str, str] | None, optional
        Provide custom units to aid the parser in identifying units.
        The custom units should be provided as a dict of plural: singular pairs.
        If a unit does not have a plural form, provide the singular form as the key.
        The units should not start with a capital letter, but may contain capital
        letters at other positions.

    Returns
    -------
    ParserDebugInfo
        ParserDebugInfo object containing the PreProcessor object, PostProcessor
        object and Tagger.
    """
    logger.debug(f'Parsing sentence "{sentence}" using "en" parser.')
    TAGGER = load_parser_model()

    if custom_units is None:
        custom_units = {}

    # Generate capitalized version of each entry in the custom units dictionary
    _capitalized_units = {}
    for plural, singular in custom_units.items():
        _capitalized_units[plural.capitalize()] = singular.capitalize()
    custom_units = custom_units | _capitalized_units

    processed_sentence = PreProcessor(sentence, custom_units=custom_units)
    features = processed_sentence.sentence_features()
    labels, scores = zip(*TAGGER.tag_from_features(features))
    labels = list(labels)
    scores = list(scores)
    logger.debug(f"Sentence token labels: {labels}.")

    if expect_name_in_output and all("NAME" not in label for label in labels):
        # No tokens were assigned the NAME label, so guess if there's a name
        logger.debug("No tokens found where name is most likely label.")
        labels, scores = guess_ingredient_name(TAGGER, labels, scores)

    labelled_tokens = [
        LabelledToken(
            index=token.index,
            text=token.text,
            pos_tag=token.pos_tag,
            label=label,
            score=score,
            plural=token.index in processed_sentence.singularised_indices,
        )
        for token, label, score in zip(
            processed_sentence.tokenized_sentence, labels, scores
        )
    ]

    postprocessed_sentence = PostProcessor(
        sentence,
        labelled_tokens,
        custom_units=custom_units,
        separate_names=separate_names,
        discard_isolated_stop_words=discard_isolated_stop_words,
        string_units=string_units,
        volumetric_units_system=volumetric_units_system,
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
    logger.debug(
        "Attempting to guess name from tokens where name label is not most probable."
    )
    NAME_LABELS = [
        "B_NAME_TOK",
        "I_NAME_TOK",
        "NAME_VAR",
        "NAME_MOD",
        "NAME_SEP",
    ]

    # For each element of the sequence, determine the most likely *NAME label whose
    # score exceeds the minimum threshold.
    # Store in a dict -> {element_index: (score, label)}
    candidate_score_labels: dict[int, tuple[float, str]] = {}
    for i, _ in enumerate(labels):
        alt_label_scores = [(TAGGER.marginal(label, i), label) for label in NAME_LABELS]
        max_score = max(alt_label_scores, key=lambda x: x[0])
        if max_score[0] > min_score:
            candidate_score_labels[i] = max_score

    if len(candidate_score_labels) == 0:
        logger.debug("No viable name tokens identified.")
        return labels, scores

    # Group element indices into groups of consecutive indices.
    groups = [
        list(group)
        for group in group_consecutive_idx(list(candidate_score_labels.keys()))
    ]

    # Take longest group of consecutive indices and replace the labels and scores at
    # these indices with the most likely *NAME labels and their score.
    indices = sorted(groups, key=len, reverse=True)[0]
    for token_index in indices:
        new_score, new_label = candidate_score_labels[token_index]
        labels[token_index] = new_label
        scores[token_index] = new_score

    logger.debug(f"Found alternative name at token indices: {indices}")
    return labels, scores

#!/usr/bin/env python3

import logging

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
    logger.debug("Parsing sentence '%s' using 'en' parser.", sentence)
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
    labels, scores = zip(*TAGGER.tag_from_features(features, expect_name_in_output))
    labels = list(labels)
    scores = list(scores)
    logger.debug("Sentence token labels: %s.", labels)

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
    logger.debug("Parsing sentence '%s' using 'en' parser.", sentence)
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
    labels, scores = zip(*TAGGER.tag_from_features(features, expect_name_in_output))
    labels = list(labels)
    scores = list(scores)
    logger.debug("Sentence token labels: %s.", labels)

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

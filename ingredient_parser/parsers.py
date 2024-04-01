#!/usr/bin/env python3

from dataclasses import dataclass
from importlib.resources import as_file, files

import pycrfsuite

from ._utils import pluralise_units
from .postprocess import ParsedIngredient, PostProcessor
from .preprocess import PreProcessor

# Create TAGGER object that can be reused between function calls
# We only want to load the model into TAGGER once, but only do it
# when we need to (from parse_ingredient() or inspect_parser()) and
# not whenever anything from ingredient_parser is imported.
TAGGER = pycrfsuite.Tagger()


def load_model_if_not_loaded():
    """Load model into TAGGER variable if not loaded.

    There isn't a simple way to check if the model if loaded or not, so
    we try to call TAGGER.info() which will raise a RuntimeError if the
    model is not loaded yet.
    """
    try:
        TAGGER.info()
    except RuntimeError:
        with as_file(files(__package__) / "model.en.crfsuite") as p:
            TAGGER.open(str(p))


def parse_ingredient(
    sentence: str,
    discard_isolated_stop_words: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
) -> ParsedIngredient:
    """Parse an ingredient sentence using CRF model to return structured data

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse
    discard_isolated_stop_words : bool, optional
        If True, any isolated stop words in the name, preparation, or comment fields
        are discarded.
        Default is True.
    string_units : bool
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Dfault is False.
    imperial_units : bool
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.

    Returns
    -------
    ParsedIngredient
        ParsedIngredient object of structured data parsed from input string
    """
    load_model_if_not_loaded()

    processed_sentence = PreProcessor(sentence)
    tokens = processed_sentence.tokenized_sentence
    labels = TAGGER.tag(processed_sentence.sentence_features())
    scores = [TAGGER.marginal(label, i) for i, label in enumerate(labels)]

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
        labels,
        scores,
        discard_isolated_stop_words=discard_isolated_stop_words,
        string_units=string_units,
        imperial_units=imperial_units,
    )
    return postprocessed_sentence.parsed


def parse_multiple_ingredients(
    sentences: list[str],
    discard_isolated_stop_words: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
) -> list[ParsedIngredient]:
    """Parse multiple ingredient sentences in one go.

    This function accepts a list of sentences, with element of the list representing
    one ingredient sentence.
    A list of dictionaries is returned, with optional confidence values.
    This function is a simple for-loop that iterates through each element of the
    input list.

    Parameters
    ----------
    sentences : list[str]
        List of sentences to parse
    discard_isolated_stop_words : bool, optional
        If True, any isolated stop words in the name, preparation, or comment fields
        are discarded.
        Default is True.
    string_units : bool
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Dfault is False.
    imperial_units : bool
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.

    Returns
    -------
    list[ParsedIngredient]
        List of ParsedIngredient objects of structured data parsed
        from input sentences
    """
    return [
        parse_ingredient(
            sentence,
            discard_isolated_stop_words=discard_isolated_stop_words,
            string_units=string_units,
            imperial_units=imperial_units,
        )
        for sentence in sentences
    ]


@dataclass
class ParserDebugInfo:
    """Dataclass for holding intermediate objects generated during
    ingredient sentence parsing.

    Attributes
    ----------
    sentence : str
        Input ingredient sentence.
    PreProcessor : PreProcessor
        PreProcessor object created using input sentence.
    PostProcessor : PostProcessor
        PostProcessor object created using tokens, labels and scores from
        input sentence.
    Tagger : pycrfsuite.Tagger
        CRF model tagger object.
    """

    sentence: str
    PreProcessor: PreProcessor
    PostProcessor: PostProcessor
    Tagger = TAGGER


def inspect_parser(
    sentence: str,
    discard_isolated_stop_words: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
) -> ParserDebugInfo:
    """Return object containing all intermediate objects used in the parsing of
    a sentence.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse
    discard_isolated_stop_words : bool, optional
        If True, any isolated stop words in the name, preparation, or comment fields
        are discarded.
        Default is True.
    string_units : bool
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Dfault is False.
    imperial_units : bool
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.

    Returns
    -------
    ParserDebugInfo
        ParserDebugInfo object containing the PreProcessor object, PostProcessor
        object and Tagger.
    """
    load_model_if_not_loaded()

    processed_sentence = PreProcessor(sentence)
    tokens = processed_sentence.tokenized_sentence
    labels = TAGGER.tag(processed_sentence.sentence_features())
    scores = [TAGGER.marginal(label, i) for i, label in enumerate(labels)]

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
        labels,
        scores,
        discard_isolated_stop_words=discard_isolated_stop_words,
        string_units=string_units,
        imperial_units=imperial_units,
    )

    return ParserDebugInfo(
        sentence=sentence,
        PreProcessor=processed_sentence,
        PostProcessor=postprocessed_sentence,
    )

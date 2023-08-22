#!/usr/bin/env python3

from importlib.resources import as_file, files

import pycrfsuite

from ._utils import pluralise_units
from .postprocess import ParsedIngredient, PostProcessor
from .preprocess import PreProcessor

# Create TAGGER object
TAGGER = pycrfsuite.Tagger()
with as_file(files(__package__) / "model.crfsuite") as p:
    TAGGER.open(str(p))


def parse_ingredient(sentence: str) -> ParsedIngredient:
    """Parse an ingredient sentence using CRF model to return structured data

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse

    Returns
    -------
    ParsedIngredient
        ParsedIngredient object of structured data parsed from input string
    """

    processed_sentence = PreProcessor(sentence)
    tokens = processed_sentence.tokenized_sentence
    labels = TAGGER.tag(processed_sentence.sentence_features())
    scores = [TAGGER.marginal(label, i) for i, label in enumerate(labels)]

    # Replurise tokens that were singularised if the label isn't UNIT
    # For tokens with UNIT label, we'll deal with them below
    for idx in processed_sentence.singularised_indices:
        token = tokens[idx]
        label = labels[idx]
        if label != "UNIT":
            tokens[idx] = pluralise_units(token)

    postprocessed_sentence = PostProcessor(sentence, tokens, labels, scores)
    return postprocessed_sentence.parsed()


def parse_multiple_ingredients(sentences: list[str]) -> list[ParsedIngredient]:
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

    Returns
    -------
    list[ParsedIngredient]
        List of ParsedIngredient objects of structured data parsed
        from input sentences
    """
    return [parse_ingredient(sent) for sent in sentences]

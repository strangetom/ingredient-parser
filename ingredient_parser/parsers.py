#!/usr/bin/env python3

from dataclasses import dataclass
from importlib.resources import as_file, files

import pycrfsuite

from ._utils import pluralise_units
from .postprocess import (
    IngredientAmount,
    IngredientText,
    postprocess,
    postprocess_amounts,
)
from .preprocess import PreProcessor


@dataclass
class ParsedIngredient:
    """Dataclass for holding the parsed values for an input sentence.

    * Sentence: The original input sentence
    * Quantity: The parsed quantities from the input sentence
    * Unit: The parsed units from the input sentence
    * Name: The parsed name from the input sentence
    * Comment: The parsed comment from the input sentence
    * Other: Any tokens in the input sentence that were not labelled
    """

    name: IngredientText | None
    amount: list[IngredientAmount]
    comment: IngredientText | None
    other: IngredientText | None
    sentence: str


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

    amounts = postprocess_amounts(tokens, labels, scores)
    name = postprocess(tokens, labels, scores, "NAME")
    comment = postprocess(tokens, labels, scores, "COMMENT")
    other = postprocess(tokens, labels, scores, "OTHER")

    return ParsedIngredient(
        sentence=sentence,
        amount=amounts,
        name=name,
        comment=comment,
        other=other,
    )


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

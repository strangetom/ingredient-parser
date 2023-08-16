#!/usr/bin/env python3

import argparse
import json
from dataclasses import dataclass
from importlib.resources import as_file, files

import pycrfsuite

from .preprocess import PreProcessor
from .utils import average, find_idx, fix_punctuation, join_adjacent, pluralise_units


@dataclass
class ParsedIngredientConfidence:
    """Dataclass for holding the confidence values for each of the parsed values.

    The confidence is a value between 0 (no confidence) and 1 (complete confidence).
    """

    quantity: float
    unit: float
    name: float
    comment: float
    other: float


@dataclass
class ParsedIngredient:
    """Dataclass for holding the parsed values for an input sentence.

    * Sentence: The original input sentence
    * Quantity: The parsed quantity from the input sentence, or an empty string
    * Unit: The parsed unit from the input sentence, or an empty string
    * Name: The parsed name from the input sentence, or an empty string
    * Comment: The parsed comment from the input sentence, or an empty string
    * Other: Any tokens in the input sentence that were not labelled
    * Confidence: A ParsedIngredientConfidence object, or None
    """

    sentence: str
    quantity: str
    unit: str
    name: str
    comment: str
    other: str
    confidence: ParsedIngredientConfidence | None


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

    quantity = " ".join([tokens[idx] for idx in find_idx(labels, "QTY")])
    unit = " ".join([tokens[idx] for idx in find_idx(labels, "UNIT")])

    if quantity != "1" and quantity != "":
        unit = pluralise_units(unit)

    name = " ".join([tokens[idx] for idx in find_idx(labels, "NAME")])
    comment = join_adjacent(tokens, find_idx(labels, "COMMENT"))

    other = join_adjacent(tokens, find_idx(labels, "OTHER"))

    if isinstance(comment, list):
        comment = ", ".join([fix_punctuation(item) for item in comment])
    else:
        comment = fix_punctuation(comment)

    if isinstance(other, list):
        other = ", ".join([fix_punctuation(item) for item in other])
    else:
        other = fix_punctuation(other)

    confidence = ParsedIngredientConfidence(
        quantity=average(labels, scores, "QTY"),
        unit=average(labels, scores, "UNIT"),
        name=average(labels, scores, "NAME"),
        comment=average(labels, scores, "COMMENT"),
        other=average(labels, scores, "OTHER"),
    )

    return ParsedIngredient(
        sentence=sentence,
        quantity=quantity,
        unit=unit,
        name=fix_punctuation(name),
        comment=comment,
        other=other,
        confidence=confidence,
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

    Examples
    ------
    >>> parse_multiple_ingredients(sentences)
    >>> sentences = [
        "3 tablespoons fresh lime juice, plus lime wedges for serving",
        "2 tablespoons extra-virgin olive oil",
        "2 large garlic cloves, finely grated",
    ]
    [{'sentence': '3 tablespoons fresh lime juice, plus lime wedges for serving',\
'quantity': '3', 'unit': 'tablespoon', 'name': 'lime juice',\
'comment': ['fresh', 'plus lime wedges for serving'], 'other': ''},\
{'sentence': '2 tablespoons extra-virgin olive oil', 'quantity': '2',\
'unit': 'tablespoon', 'name': 'extra-virgin olive oil', 'comment': '',\
'other': ''},\
{'sentence': '2 large garlic cloves, finely grated', 'quantity': '2',\
'unit': 'clove', 'name': 'garlic', 'comment': 'finely grated', 'other': 'large'}]
    """
    parsed = []
    for sent in sentences:
        parsed.append(parse_ingredient(sent))

    return parsed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse ingredient into structured data"
    )
    parser.add_argument("-s", "--string", help="Ingredient string to parse")
    args = parser.parse_args()

    if args.string is not None:
        parsed = parse_ingredient(args.string)
        print(json.dumps(parsed.__dict__, indent=2))

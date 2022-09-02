#!/usr/bin/env python3

import argparse
import importlib.resources as pkg_resources
import json
import os
from typing import Dict, List, Union

import pycrfsuite
from typing_extensions import NotRequired, TypedDict

from .preprocess import PreProcessor
from .utils import average, find_idx, fix_punctuation, join_adjacent


class ParsedIngredient(TypedDict):
    sentence: str
    quantity: str
    unit: str
    name: str
    comment: Union[List[str], str]
    other: Union[List[str], str]
    confidence: NotRequired[Dict[str, float]]


# Create TAGGER object
TAGGER = pycrfsuite.Tagger()
model_path = pkg_resources.path(__package__, "model.crfsuite")
with model_path as p:
    TAGGER.open(str(p))


def parse_ingredient(sentence: str, confidence: bool = False) -> ParsedIngredient:
    """Parse ingredient senetence using CRF model to return structured data

    Return dictionary has the following types
    {
        "sentence": str,
        "quantity": str,
        "unit": str,
        "name": str,
        "comment": Union[List[str], str],
        "other": Union[List[str], str],
        "confidence": Dict[str, float] <- Optional
    }

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse
    confidence : bool, optional
        Return confidence scores for labels

    Returns
    -------
    ParsedIngredient
        Dictionary of structured data parsed from input string
    """

    processed_sentence = PreProcessor(sentence)
    tokens = processed_sentence.tokenized_sentence
    labels = TAGGER.tag(processed_sentence.sentence_features())
    scores = [TAGGER.marginal(label, i) for i, label in enumerate(labels)]

    quantity = " ".join([tokens[idx] for idx in find_idx(labels, "QTY")])
    unit = " ".join([tokens[idx] for idx in find_idx(labels, "UNIT")])
    name = " ".join([tokens[idx] for idx in find_idx(labels, "NAME")])
    comment = join_adjacent(tokens, find_idx(labels, "COMMENT"))
    if isinstance(comment, list):
        comment = [fix_punctuation(item) for item in comment]
    else:
        comment = fix_punctuation(comment)

    other = join_adjacent(tokens, find_idx(labels, "OTHER"))
    if isinstance(other, list):
        other = [fix_punctuation(item) for item in other]
    else:
        other = fix_punctuation(other)

    parsed: ParsedIngredient = {
        "sentence": sentence,
        "quantity": quantity,
        "unit": unit,
        "name": fix_punctuation(name),
        "comment": comment,
        "other": other,
    }

    if confidence:
        parsed["confidence"] = {
            "quantity": average(labels, scores, "QTY"),
            "unit": average(labels, scores, "UNIT"),
            "name": average(labels, scores, "NAME"),
            "comment": average(labels, scores, "COMMENT"),
            "other": average(labels, scores, "OTHER"),
        }
        return parsed

    else:
        return parsed


def parse_multiple_ingredients(
    sentences: List[str], confidence: bool = False
) -> List[ParsedIngredient]:
    """Parse multiple ingredients from text file.
    Each line of the file is one ingredient sentence

    Parameters
    ----------
    sentences : List[str]
        List of sentences to parse
    confidence : bool, optional
        Return confidence scores for labels

    Returns
    -------
    List[ParsedIngredient]
        List of dictionaries of structured data parsed from input sentences
    """
    parsed = []
    for sent in sentences:
        parsed.append(parse_ingredient(sent, confidence))

    return parsed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse ingredient into structured data"
    )
    parser.add_argument("-s", "--string", help="Ingredient string to parse")
    parser.add_argument(
        "-c",
        "--confidence",
        action="store_true",
        help="Return confidence scores for labels",
    )
    args = parser.parse_args()

    if args.string is not None:
        parsed = parse_ingredient(args.string, args.confidence)
        print(json.dumps(parsed, indent=2))

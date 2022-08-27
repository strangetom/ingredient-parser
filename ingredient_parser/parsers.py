#!/usr/bin/env python3

import argparse
import json
import os
import pickle
from itertools import groupby
from operator import itemgetter
from typing import Any, Dict, List, Union

import pycrfsuite

from .preprocess import PreProcessor
from .utils import average, find_idx, join_adjacent, fix_punctuation

# Create TAGGER object
pkg_dir, _ = os.path.split(__file__)
model_path = os.path.join(pkg_dir, "model.crfsuite")
TAGGER = pycrfsuite.Tagger()
TAGGER.open(model_path)


def parse_ingredient(sentence: str, confidence: bool = False) -> Dict[str, Any]:
    """Parse ingredient senetence using CRF model to return structured data

    Return dictionary has the following types
    {
        "sentence": str,
        "quantity": str,
        "unit": str,
        "name": str,
        "comment": Union[List[str], str],
        "other": Union[List[str], str]
    }

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse
    confidence : bool, optional
        Return confidence scores for labels

    Returns
    -------
    Dict[str, Any]
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

    parsed: Dict[str, Any] = {
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
) -> List[Dict[str, Any]]:
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
    List[Dict[str, Any]]
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
    parser.add_argument(
        "-f", "--file", help="Path to file of ingredient strings to parse"
    )
    args = parser.parse_args()

    if args.string is not None:
        parsed = parse_ingredient(args.string, args.confidence)
        print(json.dumps(parsed, indent=2))
    elif args.file is not None:
        parsed_multiple = parse_multiple_ingredients(args.file, args.confidence)
        print(json.dumps(parsed_multiple, indent=2))

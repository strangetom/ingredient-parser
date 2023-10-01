#!/usr/bin/env python3

import argparse

from ingredient_parser import PreProcessor

from .training_utils import load_csv, match_labels


def find_missing_labels(args: argparse.Namespace) -> None:
    """Find sentences in dataset(s) where tokens are given OTHER label.

    Parameters
    ----------
    args : argparse.Namespace
        Cleaning utility configuration

    Raises
    ------
    ValueError
        When multiple datasets are passed to the function at the same time.
    """

    if len(args.datasets) != 1:
        raise ValueError("This utility can only handle one dataset at a time")

    print("[INFO] Loading datasets.")
    sentences, sentence_labels = load_csv(args.datasets[0], args.number)

    matches = []
    for i, (sentence, labels) in enumerate(zip(sentences, sentence_labels)):
        p = PreProcessor(sentence)
        token_labels = match_labels(p.tokenized_sentence, labels)

        if "OTHER" in token_labels:
            matches.append(f"{i+2}: {sentence}")

            print(f"{i+2}: {sentence}")
            print(p.tokenized_sentence)
            print(token_labels)
            print("")

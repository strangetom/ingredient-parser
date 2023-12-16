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

            # Highlight tokens and labels with OTHER label in red text
            output_tokens, output_labels = [], []
            for tok, lab in zip(p.tokenized_sentence, token_labels):
                padding = max(len(tok), len(lab))

                if lab == "OTHER":
                    output_labels.append(f"\033[91m{lab.ljust(padding)}\033[0m")
                    output_tokens.append(f"\033[91m{tok.ljust(padding)}\033[0m")
                else:
                    output_labels.append(lab.ljust(padding))
                    output_tokens.append(tok.ljust(padding))

            print(" | ".join(output_tokens))
            print(" | ".join(output_labels))
            print("")

    print(f"Found {len(matches)} sentences with missing token labels.")

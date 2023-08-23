#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_utils import load_csv, match_labels

from ingredient_parser import PreProcessor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Data cleaning helper function.\n
        Find tokens in input sentences that don't appear in any of the labels."""
    )
    parser.add_argument("--dataset", help="Path to input csv file to check")
    parser.add_argument(
        "-n",
        "--number",
        default=30000,
        type=int,
        help="Number of entries in dataset to check",
    )
    parser.add_argument(
        "-p", "--print", action="store_true", help="Print results to terminal"
    )
    args = parser.parse_args()

    print("[INFO] Loading dataset.")
    sentences, sentence_labels = load_csv(args.dataset, args.number)

    matches = []
    for i, (sentence, labels) in enumerate(zip(sentences, sentence_labels)):
        p = PreProcessor(sentence)
        token_labels = match_labels(p.tokenized_sentence, labels)

        if "OTHER" in token_labels:
            matches.append(f"{i+2}: {sentence}")

            if args.print:
                print(f"{i+2}: {sentence}")
                print(p.tokenized_sentence)
                print(token_labels)
                print("")

    with open("clean__find_missing_label.txt", "w") as f:
        f.write("\n".join(matches))

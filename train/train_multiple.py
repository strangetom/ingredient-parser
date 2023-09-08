#!/usr/bin/env python3

import argparse
import json

from training_utils import load_datasets

from train import train

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train a CRF model to parse structured data from recipe \
                     ingredient sentences."
    )
    parser.add_argument(
        "--datasets",
        "-d",
        help="Datasets in csv format",
        action="extend",
        dest="datasets",
        nargs="+",
    )
    parser.add_argument(
        "-s",
        "--split",
        default=0.25,
        type=float,
        help="Fraction of data to be used for testing",
    )
    parser.add_argument(
        "-n",
        "--number",
        default=30000,
        type=int,
        help="Maximum of entries from a dataset to use (train+test)",
    )
    parser.add_argument(
        "-m",
        "--save-model",
        default="ingredient_parser/model.crfsuite",
        help="Path to save model to",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Output a markdown file containing detailed results.",
    )
    parser.add_argument(
        "-r",
        "--runs",
        default=10,
        type=int,
        help="Number of times to run the training and evaluation of the model.",
    )
    args = parser.parse_args()

    with open("aggregate.txt", "w") as f:
        f.write("")

    vectors = load_datasets(args.datasets, args.number)
    for i in range(args.runs):
        print(f"[INFO] Training run: {i+1:02}")
        stats = train(vectors, args.split, args.save_model, args.html)

        with open("aggregate.txt", "a") as f:
            json_string = json.dumps(stats.__dict__)
            f.write(json_string + "\n")

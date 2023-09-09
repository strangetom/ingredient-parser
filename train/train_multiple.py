#!/usr/bin/env python3

import argparse
import time
from statistics import mean, stdev

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

    vectors = load_datasets(args.datasets, args.number)

    eval_results = []
    for i in range(args.runs):
        print(f"[INFO] Training run: {i+1:02}")
        start_time = time.time()
        stats = train(vectors, args.split, args.save_model, args.html)
        eval_results.append(stats)
        print(f"[INFO] Model trained in {time.time()-start_time:.1f} seconds")

    word_accuracies, sentence_accuracies = [], []
    for result in eval_results:
        sentence_accuracies.append(result.correct_sentences / result.total_sentences)
        word_accuracies.append(result.correct_words / result.total_words)

    sentence_mean = 100 * mean(sentence_accuracies)
    sentence_uncertainty = 3 * 100 * stdev(sentence_accuracies)
    print()
    print("Average sentence-level accuracy:")
    print(f"\t-> {sentence_mean:.2f}% ± {sentence_uncertainty:.2f}%")

    word_mean = 100 * mean(word_accuracies)
    word_uncertainty = 3 * 100 * stdev(word_accuracies)
    print()
    print("Average word-level accuracy:")
    print(f"\t-> {word_mean:.2f}% ± {word_uncertainty:.2f}%")

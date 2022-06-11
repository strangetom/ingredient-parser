#!/usr/bin/env python3

import argparse
from dataclasses import dataclass


@dataclass
class Stats:
    """Dataclass to store statistics on model performance"""

    total_sentences: int
    correct_sentences: int
    total_words: int
    correct_words: int


def evaluate_results(file: str) -> Stats:
    """Parse and gather statistics on CRF model output

    Parameters
    ----------
    file : str
        File containing model output

    Returns
    -------
    NamedTuple
        Stats tuple containing sentence and word level statistics
    """
    with open(file, "r") as f:
        sentences = f.read().split("\n\n")

    total_sentences = 0
    correct_sentences = 0
    total_words = 0
    correct_words = 0

    for sent in sentences:
        correct_words_per_sentence = 0
        total_words_per_sentence = 0
        tokens = sent.splitlines()

        for token in tokens:
            total_words_per_sentence += 1
            total_words += 1
            parts = token.strip().split("\t")

            if parts[-2] == parts[-1]:
                correct_words_per_sentence += 1
                correct_words += 1

        total_sentences += 1
        if correct_words_per_sentence == total_words_per_sentence:
            correct_sentences += 1

    return Stats(total_sentences, correct_sentences, total_words, correct_words)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate recipe ingredient parser results from testing data"
    )
    parser.add_argument("-r", "--results", help="Output file from testing data")
    args = parser.parse_args()

    stats = evaluate_results(args.results)

    print("Sentence-level results:")
    print(f"\tTotal: {stats.total_sentences}")
    print(f"\tCorrect: {stats.correct_sentences}")
    print(f"\t-> {100*stats.correct_sentences/stats.total_sentences:.2f}%")

    print()
    print("Word-level results:")
    print(f"\tTotal: {stats.total_words}")
    print(f"\tCorrect: {stats.correct_words}")
    print(f"\t-> {100*stats.correct_words/stats.total_words:.2f}%")

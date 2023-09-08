#!/usr/bin/env python3

import argparse
from collections import Counter
from dataclasses import dataclass
from itertools import chain

import pycrfsuite
from sklearn.model_selection import train_test_split
from test_results_to_html import test_results_to_html
from training_utils import DataVectors, load_datasets


@dataclass
class Stats:
    """Dataclass to store statistics on model performance"""

    total_sentences: int
    correct_sentences: int
    total_words: int
    correct_words: int


def evaluate(predictions: list[list[str]], truths: list[list[str]]) -> Stats:
    """Calculate statistics on the predicted labels for the test data.

    Parameters
    ----------
    predictions : list[list[str]]
        Predicted labels for each test sentence
    truths : list[list[str]]
        True labels for each test sentence

    Returns
    -------
    Stats
        Dataclass holding the following statistics:
            total sentences,
            correctly labelled sentences,
            total words,
            correctly labelled words
    """
    total_sentences = 0
    correct_sentences = 0
    total_words = 0
    correct_words = 0

    for prediction, truth in zip(predictions, truths):
        correct_words_per_sentence = 0
        total_words_per_sentence = 0

        for p, t in zip(prediction, truth):
            total_words += 1
            total_words_per_sentence += 1

            # Count as match if guess matches actual
            if p == t:
                correct_words_per_sentence += 1
                correct_words += 1

        total_sentences += 1
        if correct_words_per_sentence == total_words_per_sentence:
            correct_sentences += 1

    return Stats(total_sentences, correct_sentences, total_words, correct_words)


def train(vectors: DataVectors, split: float, save_model: str, html: bool) -> Stats:
    """Train model using vectors, splitting the vectors into a train and evaluation
    set based on <split>. The trained model is saved to <save_model>.

    Parameters
    ----------
    vectors : DataVectors
        Vectors loaded from training csv files
    split : float
        Fraction of vectors to use for evaluation.
    save_model : str
        Path to save trained model to.
    html : bool
        If True, write html file of incorrect evaluation sentences
        and print out detals about OTHER labels

    Returns
    -------
    Stats
        Statistics evaluating the model
    """
    # Split data into train and test sets
    (
        sentences_train,
        sentences_test,
        features_train,
        features_test,
        truth_train,
        truth_test,
        source_train,
        source_test,
    ) = train_test_split(
        vectors.sentences,
        vectors.features,
        vectors.labels,
        vectors.source,
        test_size=split,
    )
    print(f"[INFO] {len(features_train):,} training vectors.")
    print(f"[INFO] {len(features_test):,} testing vectors.")

    print("[INFO] Training model with training data.")
    trainer = pycrfsuite.Trainer(verbose=False)
    trainer.set_params(
        {
            "feature.possible_states": True,
            "feature.possible_transitions": True,
            "c1": 0.2,
            "c2": 1,
        }
    )
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)
    trainer.train(save_model)

    print("[INFO] Evaluating model with test data.")
    tagger = pycrfsuite.Tagger()
    tagger.open(save_model)
    labels_pred = [tagger.tag(X) for X in features_test]

    if html:
        test_results_to_html(
            sentences_test,
            truth_test,
            labels_pred,
            source_test,
            minimum_mismatches=1,
        )

        # Calculate some starts about the OTHER label
        train_label_count = Counter(chain.from_iterable(truth_train))
        train_other_pc = 100 * train_label_count["OTHER"] / train_label_count.total()
        test_label_count = Counter(chain.from_iterable(truth_test))
        test_other_pc = 100 * test_label_count["OTHER"] / test_label_count.total()
        pred_label_count = Counter(chain.from_iterable(labels_pred))
        pred_other_pc = 100 * pred_label_count["OTHER"] / pred_label_count.total()
        print("OTHER labels:")
        print(
            f"\tIn training data: {train_label_count['OTHER']} ({train_other_pc:.2f}%)"
        )
        print(f"\tIn test data: {test_label_count['OTHER']} ({test_other_pc:.2f}%)")
        print(
            f"\tPredicted in test data: {pred_label_count['OTHER']} ({pred_other_pc:.2f}%)"
        )
        print()

    stats = evaluate(labels_pred, truth_test)
    return stats


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
    args = parser.parse_args()

    vectors = load_datasets(args.datasets, args.number)
    stats = train(vectors, args.split, args.save_model, args.html)

    print("Sentence-level results:")
    print(f"\tTotal: {stats.total_sentences}")
    print(f"\tCorrect: {stats.correct_sentences}")
    print(f"\tIncorrect: {stats.total_sentences - stats.correct_sentences}")
    print(f"\t-> {100*stats.correct_sentences/stats.total_sentences:.2f}% correct")

    print()
    print("Word-level results:")
    print(f"\tTotal: {stats.total_words}")
    print(f"\tCorrect: {stats.correct_words}")
    print(f"\tIncorrect: {stats.total_words - stats.correct_words}")
    print(f"\t-> {100*stats.correct_words/stats.total_words:.2f}% correct")

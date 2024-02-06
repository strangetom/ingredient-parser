#!/usr/bin/env python3

import argparse
import time
from dataclasses import dataclass
from statistics import mean, stdev

import pycrfsuite
from sklearn.model_selection import train_test_split

from .test_results_to_html import test_results_to_html
from .test_results_to_detailed_results import test_results_to_detailed_results
from .training_utils import DataVectors, load_datasets


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
        correct = [p == t for p, t in zip(prediction, truth)]

        total_words += len(truth)
        correct_words += correct.count(True)

        total_sentences += 1
        if all(correct):
            correct_sentences += 1

    return Stats(total_sentences, correct_sentences, total_words, correct_words)


def train_model(
    vectors: DataVectors,
    split: float,
    save_model: str,
    html: bool,
    detailed_results: bool,
) -> Stats:
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
        and print out details about OTHER labels.
    detailed_results: bool
        If True, write output files with details about how labeling performed on
        the test set.

    Returns
    -------
    Stats
        Statistics evaluating the model
    """
    # Split data into train and test sets
    # The stratify argument means that each dataset is represented proprtionally
    # in the train and tests sets, avoiding the possibility that train or tests sets
    # contain data from one dataset disproportionally.
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
        stratify=vectors.source,
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

    labels_pred, scores_pred = [], []
    for X in features_test:
        labels = tagger.tag(X)
        labels_pred.append(labels)
        scores_pred.append(
            [tagger.marginal(label, i) for i, label in enumerate(labels)]
        )

    if html:
        test_results_to_html(
            sentences_test,
            truth_test,
            labels_pred,
            scores_pred,
            source_test,
            lambda x: x >= 1,
        )

    if detailed_results:
        test_results_to_detailed_results(
            sentences_test,
            truth_test,
            labels_pred,
            scores_pred,
            source_test,
        )

    stats = evaluate(labels_pred, truth_test)
    return stats


def train_single(args: argparse.Namespace) -> None:
    """Train CRF model once.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    vectors = load_datasets(args.database, args.datasets)
    stats = train_model(
        vectors, args.split, args.save_model, args.html, args.detailed_results
    )

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


def train_multiple(args: argparse.Namespace) -> None:
    """Train model multiple times and calculate average performance
    and performance uncertainty.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    vectors = load_datasets(args.database, args.datasets)

    eval_results = []
    for i in range(args.runs):
        print(f"[INFO] Training run: {i+1:02}")
        start_time = time.time()
        stats = train_model(vectors, args.split, args.save_model, args.html)
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

#!/usr/bin/env python3

import argparse
import os
from dataclasses import dataclass
from itertools import chain
from multiprocessing import Pool
from statistics import mean, stdev

import numpy as np
import pycrfsuite
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from .test_results_to_detailed_results import test_results_to_detailed_results
from .test_results_to_html import test_results_to_html
from .training_utils import DataVectors, load_datasets


@dataclass
class Metrics:
    """Metrics returned by sklearn.metrics.classification_report for each label"""

    precision: float
    recall: float
    f1_score: float
    support: int


@dataclass
class TokenStats:
    """Statistics for token classification performance"""

    NAME: Metrics
    QTY: Metrics
    UNIT: Metrics
    COMMENT: Metrics
    PREP: Metrics
    PUNC: Metrics
    macro_avg: Metrics
    weighted_avg: Metrics
    accuracy: float


@dataclass
class SentenceStats:
    """Statistics for sentence classification performance"""

    accuracy: float


@dataclass
class Stats:
    """Statistics for token and sentence classification performance"""

    token: TokenStats
    sentence: SentenceStats


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
        Dataclass holding token and sentence statistics:
    """
    # Generate token statistics
    # Flatten prediction and truth lists
    flat_predictions = list(chain.from_iterable(predictions))
    flat_truths = list(chain.from_iterable(truths))
    labels = list(set(flat_predictions))

    report = classification_report(
        flat_truths,
        flat_predictions,
        labels=labels,
        output_dict=True,
    )

    # Convert report to TokenStats dataclass
    token_stats = {}
    for k, v in report.items():
        # Convert dict to Metrics
        if k in labels + ["macro avg", "weighted avg"]:
            k = k.replace(" ", "_")
            token_stats[k] = Metrics(
                v["precision"], v["recall"], v["f1-score"], int(v["support"])
            )
        else:
            token_stats[k] = v

    token_stats = TokenStats(**token_stats)

    # Generate sentence statistics
    # The only statistics that makes sense here is accuracy because there are only
    # true-positive results (i.e. correct) and false-negative results (i.e. incorrect)
    correct_sentences = len([p for p, t in zip(predictions, truths) if p == t])
    sentence_stats = SentenceStats(correct_sentences / len(predictions))

    return Stats(token_stats, sentence_stats)


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
    # When using multiprocessing each process seems to start the RNG with the same
    # seed, and because train_test_split uses np.random to randomise the data, each
    # process ends up with the identical split.
    # Reseed the RNG to make each split different.
    np.random.seed(int.from_bytes(os.urandom(4), byteorder="little"))

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
    stats = train_model(vectors, args.split, args.save_model, args.html, args.detailed)

    print("Sentence-level results:")
    print(f"\tAccuracy: {100*stats.sentence.accuracy:.2f}%")

    print()
    print("Word-level results:")
    print(f"\tAccuracy {100*stats.token.accuracy:.2f}%")
    print(f"\tPrecision (micro) {100*stats.token.weighted_avg.precision:.2f}%")
    print(f"\tRecall (micro) {100*stats.token.weighted_avg.recall:.2f}%")
    print(f"\tF1 score (micro) {100*stats.token.weighted_avg.f1_score:.2f}%")


def train_multiple(args: argparse.Namespace) -> None:
    """Train model multiple times and calculate average performance
    and performance uncertainty.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    vectors = load_datasets(args.database, args.datasets)

    arguments = [
        (vectors, args.split, args.save_model, args.html, args.detailed)
    ] * args.runs
    with Pool(processes=args.processes) as pool:
        print("[INFO] Created multiprocessing pool for training models in parallel.")
        eval_results = pool.starmap(train_model, arguments)

    word_accuracies, sentence_accuracies = [], []
    for result in eval_results:
        sentence_accuracies.append(result.sentence.accuracy)
        word_accuracies.append(result.token.accuracy)

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

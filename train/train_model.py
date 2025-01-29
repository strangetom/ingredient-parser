#!/usr/bin/env python3

import argparse
import concurrent.futures as cf
import contextlib
from random import randint
from statistics import mean, stdev

import pycrfsuite
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from .test_results_to_detailed_results import test_results_to_detailed_results
from .test_results_to_html import test_results_to_html
from .training_utils import (
    DEFAULT_MODEL_LOCATION,
    DataVectors,
    ModelType,
    Stats,
    confusion_matrix,
    evaluate,
    load_datasets,
)


def get_model_type(cmd_arg: str) -> ModelType:
    """Convert command line argument for model type into enum

    Parameters
    ----------
    cmd_arg : str
        Command line argument for model

    Returns
    -------
    ModelType
    """
    types = {
        "parser": ModelType.PARSER,
        "foundationfoods": ModelType.FOUNDATION_FOODS,
    }
    return types[cmd_arg]


def train_parser_model(
    vectors: DataVectors,
    split: float,
    save_model: str,
    seed: int | None,
    html: bool,
    detailed_results: bool,
    plot_confusion_matrix: bool,
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
    seed : int | None
        Integer used as seed for splitting the vectors between the training and
        testing sets. If None, a random seed is generated within this function.
    html : bool
        If True, write html file of incorrect evaluation sentences
        and print out details about OTHER labels.
    detailed_results : bool
        If True, write output files with details about how labeling performed on
        the test set.
    plot_confusion_matrix : bool
        If True, plot a confusion matrix of the token labels.

    Returns
    -------
    Stats
        Statistics evaluating the model
    """
    # Generate random seed for the train/test split if none provided.
    if seed is None:
        seed = randint(0, 1_000_000_000)

    print(f"[INFO] {seed} is the random seed used for the train/test split.")

    # Split data into train and test sets
    # The stratify argument means that each dataset is represented proprtionally
    # in the train and tests sets, avoiding the possibility that train or tests sets
    # contain data from one dataset disproportionally.
    (
        _,
        sentences_test,
        features_train,
        features_test,
        truth_train,
        truth_test,
        _,
        source_test,
        _,
        tokens_test,
    ) = train_test_split(
        vectors.sentences,
        vectors.features,
        vectors.labels,
        vectors.source,
        vectors.tokens,
        test_size=split,
        stratify=vectors.source,
        random_state=seed,
    )
    print(f"[INFO] {len(features_train):,} training vectors.")
    print(f"[INFO] {len(features_test):,} testing vectors.")

    print("[INFO] Training model with training data.")
    trainer = pycrfsuite.Trainer(verbose=False)  # type: ignore
    trainer.set_params(
        {
            "feature.minfreq": 0,
            "feature.possible_states": True,
            "feature.possible_transitions": True,
            "c1": 0.6,
            "c2": 0.35,
            "max_linesearch": 5,
            "num_memories": 3,
            "period": 10,
        }
    )
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)
    trainer.train(save_model)

    print("[INFO] Evaluating model with test data.")
    tagger = pycrfsuite.Tagger()  # type: ignore
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
            tokens_test,
            truth_test,
            labels_pred,
            scores_pred,
            source_test,
        )

    if detailed_results:
        test_results_to_detailed_results(
            sentences_test,
            tokens_test,
            truth_test,
            labels_pred,
            scores_pred,
        )

    if plot_confusion_matrix:
        confusion_matrix(labels_pred, truth_test)

    stats = evaluate(labels_pred, truth_test, seed, ModelType.PARSER)
    return stats


def train_ff_model(
    vectors: DataVectors,
    split: float,
    save_model: str,
    seed: int | None,
    html: bool,
    detailed_results: bool,
    plot_confusion_matrix: bool,
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
    seed : int | None
        Integer used as seed for splitting the vectors between the training and
        testing sets. If None, a random seed is generated within this function.
    html : bool
        If True, write html file of incorrect evaluation sentences
        and print out details about OTHER labels.
    detailed_results : bool
        If True, write output files with details about how labeling performed on
        the test set.
    plot_confusion_matrix : bool
        If True, plot a confusion matrix of the token labels.

    Returns
    -------
    Stats
        Statistics evaluating the model
    """
    # Generate random seed for the train/test split if none provided.
    if seed is None:
        seed = randint(0, 1_000_000_000)

    print(f"[INFO] {seed} is the random seed used for the train/test split.")

    # Split data into train and test sets
    # The stratify argument means that each dataset is represented proprtionally
    # in the train and tests sets, avoiding the possibility that train or tests sets
    # contain data from one dataset disproportionally.
    (
        _,
        sentences_test,
        features_train,
        features_test,
        truth_train,
        truth_test,
        _,
        source_test,
        _,
        tokens_test,
    ) = train_test_split(
        vectors.sentences,
        vectors.features,
        vectors.labels,
        vectors.source,
        vectors.tokens,
        test_size=split,
        stratify=vectors.source,
        random_state=seed,
    )
    print(f"[INFO] {len(features_train):,} training vectors.")
    print(f"[INFO] {len(features_test):,} testing vectors.")

    print("[INFO] Training model with training data.")
    trainer = pycrfsuite.Trainer(verbose=False)  # type: ignore
    trainer.set_params(
        {
            "feature.minfreq": 1,
            "feature.possible_states": True,
            "feature.possible_transitions": True,
            "c1": 0.3,
            "c2": 0.1,
            "max_linesearch": 5,
            "num_memories": 3,
            "period": 10,
        }
    )
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)
    trainer.train(save_model)

    print("[INFO] Evaluating model with test data.")
    tagger = pycrfsuite.Tagger()  # type: ignore
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
            tokens_test,
            truth_test,
            labels_pred,
            scores_pred,
            source_test,
        )

    if detailed_results:
        test_results_to_detailed_results(
            sentences_test,
            tokens_test,
            truth_test,
            labels_pred,
            scores_pred,
        )

    if plot_confusion_matrix:
        confusion_matrix(labels_pred, truth_test)

    stats = evaluate(labels_pred, truth_test, seed, ModelType.FOUNDATION_FOODS)
    return stats


MODEL_FCNS = {
    "parser": train_parser_model,
    "foundationfoods": train_ff_model,
}


def train_single(args: argparse.Namespace) -> None:
    """Train CRF model once.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    vectors = load_datasets(
        args.database, args.table, args.datasets, get_model_type(args.model)
    )

    if args.save_model is None:
        save_model = DEFAULT_MODEL_LOCATION[args.model]
    else:
        save_model = args.save_model

    model_fcn = MODEL_FCNS[args.model]
    stats = model_fcn(
        vectors,
        args.split,
        save_model,
        args.seed,
        args.html,
        args.detailed,
        args.confusion,
    )

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
    vectors = load_datasets(
        args.database, args.table, args.datasets, get_model_type(args.model)
    )

    model_fcn = MODEL_FCNS[args.model]

    if args.save_model is None:
        save_model = DEFAULT_MODEL_LOCATION[args.model]
    else:
        save_model = args.save_model

    # The first None argument is for the seed. This is set to None so each
    # iteration of the training function uses a different random seed.
    arguments = [
        (
            vectors,
            args.split,
            save_model,
            None,
            args.html,
            args.detailed,
            args.confusion,
        )
    ] * args.runs

    eval_results = []
    with contextlib.redirect_stdout(None):  # Suppress print output
        with cf.ProcessPoolExecutor(max_workers=args.processes) as executor:
            futures = [executor.submit(model_fcn, *a) for a in arguments]
            for future in tqdm(cf.as_completed(futures), total=len(futures)):
                eval_results.append(future.result())

    word_accuracies, sentence_accuracies, seeds = [], [], []
    for result in eval_results:
        sentence_accuracies.append(result.sentence.accuracy)
        word_accuracies.append(result.token.accuracy)
        seeds.append(result.seed)

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

    index_best = max(
        range(len(sentence_accuracies)), key=sentence_accuracies.__getitem__
    )
    max_sent = 100 * sentence_accuracies[index_best]
    max_word = 100 * word_accuracies[index_best]
    max_seed = seeds[index_best]
    index_worst = min(
        range(len(sentence_accuracies)), key=sentence_accuracies.__getitem__
    )
    min_sent = 100 * sentence_accuracies[index_worst]
    min_word = 100 * word_accuracies[index_worst]
    min_seed = seeds[index_worst]
    print()
    print(f"Best:  Sentence {max_sent:.2f}% / Word {max_word:.2f}% (Seed: {max_seed})")
    print(f"Worst: Sentence {min_sent:.2f}% / Word {min_word:.2f}% (Seed: {min_seed})")

#!/usr/bin/env python3

import argparse
import concurrent.futures as cf
import logging
from contextlib import contextmanager
from pathlib import Path
from random import randint
from statistics import mean, stdev
from typing import Generator
from uuid import uuid4

import pycrfsuite
from sklearn.model_selection import train_test_split
from tabulate import tabulate

from .test_results_to_detailed_results import test_results_to_detailed_results
from .test_results_to_html import test_results_to_html
from .training_utils import (
    DEFAULT_MODEL_LOCATION,
    DataVectors,
    Stats,
    confusion_matrix,
    convert_num_ordinal,
    evaluate,
    load_datasets,
)

logger = logging.getLogger(__name__)


@contextmanager
def change_log_level(level: int) -> Generator[None, None, None]:
    """Context manager to temporarily change logging level within the context.

    On exiting the context, the original level is restored.

    Parameters
    ----------
    level : int
        Logging level to use within context manager.

    Yields
    ------
    Generator[None, None, None]
        Generator, yielding None
    """
    original_level = logger.getEffectiveLevel()
    logger.setLevel(level)
    yield
    logger.setLevel(original_level)


def train_parser_model(
    vectors: DataVectors,
    split: float,
    save_model: Path,
    seed: int | None,
    html: bool,
    detailed_results: bool,
    plot_confusion_matrix: bool,
    keep_model: bool = True,
    combine_name_labels: bool = False,
) -> Stats:
    """Train model using vectors, splitting the vectors into a train and evaluation
    set based on <split>. The trained model is saved to <save_model>.

    Parameters
    ----------
    vectors : DataVectors
        Vectors loaded from training csv files
    split : float
        Fraction of vectors to use for evaluation.
    save_model : Path
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
    keep_model : bool, optional
        If False, delete model from disk after evaluating it's performance.
        Default is True.
    combine_name_labels : bool, optional
        If True, combine all NAME labels into a single NAME label.
        Default is False

    Returns
    -------
    Stats
        Statistics evaluating the model
    """
    # Generate random seed for the train/test split if none provided.
    if seed is None:
        seed = randint(0, 1_000_000_000)

    logger.info(f"{seed} is the random seed used for the train/test split.")

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
    logger.info(f"{len(features_train):,} training vectors.")
    logger.info(f"{len(features_test):,} testing vectors.")

    logger.info("Training model with training data.")
    trainer = pycrfsuite.Trainer(verbose=False)  # type: ignore
    trainer.set_params(
        {
            "feature.minfreq": 0,
            "feature.possible_states": True,
            "feature.possible_transitions": True,
            "c1": 0.6,
            "c2": 0.5,
            "max_linesearch": 5,
            "num_memories": 3,
            "period": 10,
        }
    )
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)
    trainer.train(str(save_model))

    logger.info("Evaluating model with test data.")
    tagger = pycrfsuite.Tagger()  # type: ignore
    tagger.open(str(save_model))

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

    stats = evaluate(labels_pred, truth_test, seed, combine_name_labels)

    if not keep_model:
        save_model.unlink(missing_ok=True)

    return stats

def train_parser_model_bypass_logging(*kargs) -> Stats:
    stats = None
    with change_log_level(logging.WARNING):  # Temporarily stop logging below WARNING for multi-processing
        stats = train_parser_model(*kargs)
    return stats

def train_single(args: argparse.Namespace) -> None:
    """Train CRF model once.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    vectors = load_datasets(
        args.database,
        args.table,
        args.datasets,
        discard_other=True,
        combine_name_labels=args.combine_name_labels,
    )

    if args.save_model is None:
        save_model = DEFAULT_MODEL_LOCATION
    else:
        save_model = args.save_model

    stats = train_parser_model(
        vectors,
        args.split,
        Path(save_model),
        args.seed,
        args.html,
        args.detailed,
        args.confusion,
        keep_model=True,
        combine_name_labels=args.combine_name_labels,
    )

    headers = [
        "Sentence-level results",
        "Word-level results"
    ]
    table = []

    table.append([
        f"Accuracy: {100 * stats.sentence.accuracy:.2f}%",
        f"Accuracy: {100 * stats.token.accuracy:.2f}%\nPrecision (micro) {100 * stats.token.weighted_avg.precision:.2f}%\nRecall (micro) {100 * stats.token.weighted_avg.recall:.2f}%\nF1 score (micro) {100 * stats.token.weighted_avg.f1_score:.2f}%"
    ])

    print(
        '\n' +
        tabulate(
            table,
            headers=headers,
            tablefmt="pretty",
            maxcolwidths=[None, None],
            stralign="left",
            numalign="right"
        )
        + '\n'
    )


def train_multiple(args: argparse.Namespace) -> None:
    """Train model multiple times and calculate average performance
    and performance uncertainty.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    vectors = load_datasets(
        args.database,
        args.table,
        args.datasets,
        discard_other=True,
        combine_name_labels=args.combine_name_labels,
    )

    if args.save_model is None:
        save_model = DEFAULT_MODEL_LOCATION
    else:
        save_model = args.save_model

    # The first None argument is for the seed. This is set to None so each
    # iteration of the training function uses a different random seed.
    arguments = [
        (
            vectors,
            args.split,
            Path(save_model).with_stem("model-" + str(uuid4())),
            None,  # Seed
            args.html,
            args.detailed,
            args.confusion,
            False,  # keep_model
            args.combine_name_labels,
        )
        for _ in range(args.runs)
    ]

    word_accuracies, sentence_accuracies, seeds, eval_results = [], [], [], []
    with cf.ProcessPoolExecutor(max_workers=args.processes) as executor:
        futures = [executor.submit(train_parser_model_bypass_logging, *a) for a in arguments]
        logger.info(f"Queued for {args.runs} separate runs. This may take some time.")
        for idx, future in enumerate(cf.as_completed(futures)):
            logger.info(f"{convert_num_ordinal(idx + 1)} run completed")
            eval_results.append(future.result())

    word_accuracies, sentence_accuracies, seeds = [], [], []
    for result in eval_results:
        sentence_accuracies.append(result.sentence.accuracy)
        word_accuracies.append(result.token.accuracy)
        seeds.append(result.seed)

    sentence_mean = 100 * mean(sentence_accuracies)
    sentence_uncertainty = 3 * 100 * stdev(sentence_accuracies)

    word_mean = 100 * mean(word_accuracies)
    word_uncertainty = 3 * 100 * stdev(word_accuracies)

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


    headers = [
        "Run",
        "Word/Token accuracy",
        "Sentence accuracy",
        "Seed"
    ]

    table = []
    for idx, result in enumerate(eval_results):
        table.append(
            [
                convert_num_ordinal(idx + 1),
                f"{100 * result.token.accuracy:.2f}%",
                f"{100 * result.sentence.accuracy:.2f}%",
                f"{result.seed}",
            ]
        )

    table.append(['-'] * len(headers))
    table.append([
        "Average",
        f"{word_mean:.2f}% ± {word_uncertainty:.2f}%",
        f"{sentence_mean:.2f}% ± {sentence_uncertainty:.2f}%",
        f"{max_seed}"
    ])
    table.append(['-'] * len(headers))
    table.append([
        "Best",
        f"{max_word:.2f}%",
        f"{max_sent:.2f}%",
        f"{max_seed}"
    ])
    table.append([
        "Worst",
        f"{min_word:.2f}%",
        f"{min_sent:.2f}%",
        f"{min_seed}"
    ])

    print(
        '\n' +
        tabulate(
            table,
            headers=headers,
            tablefmt="pretty",
            maxcolwidths=[None, None, None, None],
            stralign="left",
            numalign="right"
        )
        + '\n'
    )

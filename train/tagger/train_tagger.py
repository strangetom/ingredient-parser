#!/usr/bin/env python3

import argparse
import concurrent.futures as cf
import logging
import random
import time
import warnings
from datetime import timedelta
from itertools import chain
from pathlib import Path
from random import randint
from statistics import mean, stdev
from typing import cast
from uuid import uuid4

from sklearn.model_selection import train_test_split
from tabulate import tabulate

from ingredient_parser.perceptron import PerceptronTagger

from ..test_results_to_html import test_results_to_html
from ..training_utils import (
    convert_num_ordinal,
    create_confusion_matrix,
    train_model_bypass_logging,
)
from .tagger_eval import (
    Stats,
    evaluate_model_only,
)
from .tagger_utils import (
    DEFAULT_MODEL_LOCATION,
    DataVectors,
    load_datasets,
)

logger = logging.getLogger(__name__)


def train_tagger_model(
    vectors: DataVectors,
    split: float,
    save_model: Path,
    seed: int | None,
    html: bool,
    detailed_results: bool,
    plot_confusion_matrix: bool,
    keep_model: bool = True,
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
        If True, write output files with details about how labelling performed on
        the test set.
    plot_confusion_matrix : bool
        If True, plot a confusion matrix of the token labels.
    keep_model : bool, optional
        If False, delete model from disk after evaluating it's performance.
        Default is True.

    Returns
    -------
    Stats
        Statistics evaluating the model
    """
    # Generate random seed for the train/test split if none provided.
    if seed is None:
        seed = randint(0, 1_000_000_000)

    logger.info("%d is the random seed used for the train/test split.", seed)
    random.seed(seed)

    # Split data into train and test sets
    # The stratify argument means that each dataset is represented proportionally
    # in the train and tests sets, avoiding the possibility that train or tests sets
    # contain data from one dataset disproportionally.
    # We use typing.cast to stop pyright (and other checkers) from crying about the
    # unknown types of the output.
    (
        _,
        sentences_test,
        tokens_train,
        tokens_test,
        tags_train,
        tags_test,
    ) = cast(
        tuple[
            list[str],
            list[str],
            list[list[str]],
            list[list[str]],
            list[list[str]],
            list[list[str]],
        ],
        train_test_split(
            vectors.sentences,
            vectors.tokens,
            vectors.tags,
            test_size=split,
            random_state=seed,
        ),
    )

    logger.info("%d training vectors.", len(tokens_train))
    logger.info("%d testing vectors.", len(tokens_test))

    trainer = PerceptronTagger()
    trainer.train(
        tokenised_sentences=tokens_train,
        truth=tags_train,
        n_iter=5,
        min_feat_updates=5,
        min_abs_weight=0,
        quantize_bits=8,
        make_tag_dict=True,
    )
    trainer.save(save_model)

    # Create PerceptronTagger object for evaluation.
    tagger = PerceptronTagger(save_model)

    with warnings.catch_warnings(record=True) as caught:
        # Instead of catching the warning here, we should just check if the training
        # and testing sets have the same tags in them.
        warnings.simplefilter("always")
        stats, labels_pred, scores_pred = evaluate_model_only(
            tagger, tokens_test, tags_test, seed
        )
    if caught:
        missing = set(chain.from_iterable(labels_pred)) - set(
            chain.from_iterable(tags_test)
        )
        logger.warning(
            "Seed %d: labels predicted but not in test truth: %s", seed, missing
        )

    if html:
        test_results_to_html(
            sentences_test,
            tokens_test,
            tags_test,
            labels_pred,
            scores_pred,
            ["-"] * len(sentences_test),
        )

    if plot_confusion_matrix:
        create_confusion_matrix(labels_pred, tags_test)

    if not keep_model:
        save_model.unlink(missing_ok=True)
        # config_file.unlink(missing_ok=True)

    return stats


def train_single_tagger(args: argparse.Namespace) -> None:
    """Train part of speech tagger model once.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    vectors = load_datasets(args.database, args.table)

    if args.save_model is None:
        save_model = DEFAULT_MODEL_LOCATION
    else:
        save_model = args.save_model

    _ = train_tagger_model(
        vectors,
        args.split,
        Path(save_model),
        args.seed,
        args.html,
        args.detailed,
        args.confusion,
        keep_model=True,
    )


def train_multiple_tagger(args: argparse.Namespace) -> None:
    """Train part of speech tagger multiple times and calculate average performance
    and performance uncertainty.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    vectors = load_datasets(args.database, args.table)

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
            Path(save_model).with_stem("model-" + str(uuid4()) + ".json"),
            None,  # Seed
            args.html,
            args.detailed,
            args.confusion,
            False,  # keep_model
        )
        for _ in range(args.runs)
    ]

    word_accuracies, sentence_accuracies, seeds, eval_results = [], [], [], []
    with cf.ProcessPoolExecutor(max_workers=args.processes) as executor:
        futures = [
            executor.submit(train_model_bypass_logging, train_tagger_model, *a)
            for a in arguments
        ]
        logger.info("Multiple runs started at %s.", time.strftime("%H:%M:%S"))
        logger.info("Queued for %d separate runs.", args.runs)
        for idx, future in enumerate(cf.as_completed(futures)):
            if exception := future.exception():
                logger.error(
                    "%s algorithm failed with exception:",
                    convert_num_ordinal(idx + 1),
                    exc_info=exception,
                )
            else:
                elapsed_time, stats = future.result()
                eval_results.append(stats)
                logger.info(
                    "%s run completed at %s (%s elapsed).",
                    convert_num_ordinal(idx + 1),
                    time.strftime("%H:%M"),
                    timedelta(seconds=int(elapsed_time)),
                )

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

    headers = ["Run", "Word/Token accuracy", "Sentence accuracy", "Seed"]

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

    table.append(["-"] * len(headers))
    table.append(
        [
            "Average",
            f"{word_mean:.2f}% ± {word_uncertainty:.2f}%",
            f"{sentence_mean:.2f}% ± {sentence_uncertainty:.2f}%",
            f"{max_seed}",
        ]
    )
    table.append(["-"] * len(headers))
    table.append(["Best", f"{max_word:.2f}%", f"{max_sent:.2f}%", f"{max_seed}"])
    table.append(["Worst", f"{min_word:.2f}%", f"{min_sent:.2f}%", f"{min_seed}"])

    formatted_table = "\n" + tabulate(
        table,
        headers=headers,
        tablefmt="fancy_grid",
        maxcolwidths=[None, None, None, None],
        stralign="left",
        numalign="right",
    )
    logger.info(formatted_table)

#!/usr/bin/env python3

import argparse
import time
from datetime import timedelta
from itertools import product
from multiprocessing import Pool
from random import randint

import pycrfsuite
from sklearn.model_selection import train_test_split
from tabulate import tabulate

from .training_utils import (
    DataVectors,
    Stats,
    evaluate,
    load_datasets,
)


def train_model_gridsearch_lbfgs(
    vectors: DataVectors,
    split: float,
    save_model: str,
    seed: int,
    c1: float,
    c2: float,
    memories: int,
    max_linesearch: int,
    stop: int,
) -> Stats:
    """Train model using lbfgs algorithm with vectors for performing grid search over
    specified hyperparameters.
    A seed value is provided to train_test_split, so that all models in the gridsearch
    are trained on the same split of data.

    Parameters
    ----------
    vectors : DataVectors
        Vectors loaded from training csv files
    split : float
        Fraction of vectors to use for evaluation.
    save_model : str
        Path to save trained model to.
    seed : int
        Integer used as seed for splitting the vectors between the training and
        testing sets.
    c1 : list[float]
        The coefficient for L1 regularization.
    c2 : list[float]
        he coefficient for L2 regularization.

    No Longer Returned
    ------------------
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
        random_state=seed,
    )
    param_string = f"{c1=}; {c2=}; {memories=}; {max_linesearch=}; {stop=}"
    print(f"[INFO] Training model with {param_string}.")
    start_time = time.monotonic()

    trainer = pycrfsuite.Trainer(verbose=False)
    trainer.set_params(
        {
            "feature.possible_states": True,
            "feature.possible_transitions": True,
            "c1": c1,
            "c2": c2,
            "num_memories": memories,
            "max_linesearch": max_linesearch,
            "period": stop,
        }
    )
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)
    trainer.train(save_model)

    print("[INFO] Evaluating model with test data.")
    tagger = pycrfsuite.Tagger()
    tagger.open(save_model)
    labels_pred = [tagger.tag(X) for X in features_test]

    stats = evaluate(labels_pred, truth_test)
    return {
        "params": param_string,
        "stats": stats,
        "time": time.monotonic() - start_time,
    }


def grid_search(args: argparse.Namespace):
    """Perform a grid search over the specified hyperparameters and return the model
    performance statistics for each combination of parameters.

    Parameters
    ----------
    args : argparse.Namespace
        Grid search configuration
    """
    vectors = load_datasets(args.database, args.datasets)
    shuffle_seed = randint(0, 1_000_000_000)

    hyperparameters = product(
        args.c1, args.c2, args.memories, args.max_linesearch, args.stop
    )
    arguments = []
    for c1, c2, memories, max_linesearch, stop in hyperparameters:
        iteration_args = [
            vectors,
            args.split,
            args.save_model,
            shuffle_seed,
            float(c1),
            float(c2),
            int(memories),
            int(max_linesearch),
            int(stop),
        ]
        arguments.append(iteration_args)

    print(f"[INFO] Grid search over {len(arguments)} hyperparameters combinations.")
    with Pool(processes=args.processes) as pool:
        print("[INFO] Created multiprocessing pool for training models in parallel.")
        eval_results = pool.starmap(train_model_gridsearch_lbfgs, arguments)

    headers = ["Parameters", "Token accuracy", "Sentence accuracy", "Time"]
    table = []
    for result in eval_results:
        params = result["params"]
        stats = result["stats"]
        time = timedelta(seconds=int(result["time"]))
        table.append(
            [
                params,
                f"{100 * stats.token.accuracy:.2f}%",
                f"{100 * stats.sentence.accuracy:.2f}%",
                str(time),
            ]
        )

    print(tabulate(table, headers=headers, tablefmt="simple_outline"))

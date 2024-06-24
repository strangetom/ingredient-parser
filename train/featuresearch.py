#!/usr/bin/env python3

import argparse
import concurrent.futures as cf
import os
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pycrfsuite
from sklearn.model_selection import train_test_split
from tabulate import tabulate
from tqdm import tqdm

from .training_utils import (
    DataVectors,
    evaluate,
    load_datasets,
)

DISCARDED_FEATURES = {
    0: [],
    1: [
        "is_ambiguous",
        "next_is_ambiguous",
        "next_is_ambiguous2",
        "prev_is_ambiguous",
        "prev_is_ambiguous2",
    ],
}


def select_features(
    features_all: list[list[dict]], discard_features: list[str]
) -> list[dict]:
    """Select specific features from full feature set.

    Parameters
    ----------
    features_all : list[list[dict]]
        List of sentence feature dicts containing all features.
    discard_features : list[str]
        List of feature names to discard.

    Returns
    -------
    list[dict]
        List of feature dicts, containing selected features.
    """
    features_selected = []
    for sentence in features_all:
        sentence_features = []
        for token in sentence:
            token_features = {}
            for key in token:
                if key not in discard_features:
                    token_features[key] = token[key]
            sentence_features.append(token_features)

        features_selected.append(sentence_features)

    return features_selected


def train_model_feature_search(
    feature_set: int,
    vectors: DataVectors,
    split: float,
    save_model: str,
    seed: int,
    keep_model: bool,
) -> dict:
    """Train model using selected features returning model performance statistics,
    model parameters and elapsed training time.

    Parameters
    ----------
    feature_set : int
        ID of feature set to use
    vectors : DataVectors
        Vectors loaded from training csv files
    split : float
        Fraction of vectors to use for evaluation.
    save_model : str
        Path to save trained model to.
    seed : int
        Integer used as seed for splitting the vectors between the training and
        testing sets.
    keep_model : bool
        If True, keep model after evaluation, otherwise delete it.

    Returns
    -------
    dict
        Statistics from evaluating the model
    """
    start_time = time.monotonic()

    # Split data into train and test sets
    # The stratify argument means that each dataset is represented proprtionally
    # in the train and tests sets, avoiding the possibility that train or tests sets
    # contain data from one dataset disproportionally.
    (
        _,
        _,
        features_train,
        features_test,
        truth_train,
        truth_test,
        _,
        _,
    ) = train_test_split(
        vectors.sentences,
        vectors.features,
        vectors.labels,
        vectors.source,
        test_size=split,
        stratify=vectors.source,
        random_state=seed,
    )

    # Remove features not in selected feature set
    discard_features = DISCARDED_FEATURES.get(feature_set, [])
    features_train = select_features(features_train, discard_features)
    features_test = select_features(features_test, discard_features)

    # Make model name unique
    save_model_path = Path(save_model).with_stem("model-" + str(uuid4()))

    # Train model
    trainer = pycrfsuite.Trainer(verbose=False)
    # Set parameters
    trainer.set_params(
        {
            "feature.minfreq": 0,
            "feature.possible_states": True,
            "feature.possible_transitions": True,
            "c1": 0.1,
            "c2": 0.7,
            "max_linesearch": 5,
            "num_memories": 3,
            "period": 10,
        }
    )
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)
    trainer.train(str(save_model_path))
    # Get model size, in MB
    model_size = os.path.getsize(save_model_path) / 1024**2

    # Evaluate model
    tagger = pycrfsuite.Tagger()
    tagger.open(str(save_model_path))
    labels_pred = [tagger.tag(X) for X in features_test]
    stats = evaluate(labels_pred, truth_test)

    if not keep_model:
        save_model_path.unlink(missing_ok=True)

    return {
        "feature_set": feature_set,
        "model_size": model_size,
        "stats": stats,
        "time": time.monotonic() - start_time,
    }


def feature_search(args: argparse.Namespace):
    """Perform a grid search over the selected feature combinations and return the model
    performance statistics for each combination of features.

    Parameters
    ----------
    args : argparse.Namespace
        Feature search configuration
    """
    vectors = load_datasets(args.database, args.table, args.datasets)

    argument_sets = []
    for feature_set in DISCARDED_FEATURES.keys():
        arguments = [
            feature_set,
            vectors,
            args.split,
            args.save_model,
            args.seed,
            args.keep_models,
        ]
        argument_sets.append(arguments)

    print(f"[INFO] Grid search over {len(argument_sets)} feature sets.")
    print(f"[INFO] {args.seed} is the random seed used for the train/test split.")

    eval_results = []
    with cf.ProcessPoolExecutor(max_workers=args.processes) as executor:
        futures = [
            executor.submit(train_model_feature_search, *a) for a in argument_sets
        ]
        for future in tqdm(cf.as_completed(futures), total=len(futures)):
            eval_results.append(future.result())

    # Sort with highest sentence accuracy first
    eval_results = sorted(
        eval_results, key=lambda x: x["stats"].sentence.accuracy, reverse=True
    )

    headers = [
        "Feature set",
        "Token accuracy",
        "Sentence accuracy",
        "Time",
        "Size (MB)",
    ]
    table = []
    for result in eval_results:
        feature_set = result["feature_set"]
        stats = result["stats"]
        size = result["model_size"]
        time = timedelta(seconds=int(result["time"]))
        table.append(
            [
                feature_set,
                f"{100 * stats.token.accuracy:.2f}%",
                f"{100 * stats.sentence.accuracy:.2f}%",
                str(time),
                f"{size:.2f}",
            ]
        )

    print(tabulate(table, headers=headers, tablefmt="simple_outline"))

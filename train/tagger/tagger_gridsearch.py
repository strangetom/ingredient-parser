#!/usr/bin/env python3

import argparse
import concurrent.futures as cf
import json
import logging
import os
import time
from datetime import timedelta
from itertools import product
from pathlib import Path
from typing import cast
from uuid import uuid4

from sklearn.model_selection import train_test_split
from tabulate import tabulate

from ingredient_parser.perceptron import PerceptronTagger

from ..training_utils import convert_num_ordinal
from .tagger_eval import evaluate
from .tagger_utils import (
    DataVectors,
    load_datasets,
)
from .train_tagger import DEFAULT_MODEL_LOCATION

logger = logging.getLogger(__name__)

HyperparameterGridDict = dict[str, list[int] | list[float] | list[str] | list[bool]]
HyperparameterDict = dict[str, int | float | str | bool]

VALID_HYPERPARAMS = {
    "n_iter": (int,),
    "min_feat_updates": (int,),
    "min_abs_weight": (float, int, type(None)),
    "quantize_bits": (int, type(None)),
    "make_tag_dict": (bool,),
    "tag_dict_frequency_threshold": (int, type(None)),
    "tag_dict_ambiguity_threshold": (float, type(None)),
}


def validate_hyperparams(hyper_params: dict) -> None:
    """Validate training hyperparameters.

    Check that the parameter names are valid.
    Check that the parameter value types are valid.

    Parameters
    ----------
    hyper_params : dict
        dict of parameters and their values.

    Raises
    ------
    ValueError
        Exception indicating invalid parameter.
    """
    for key, value in hyper_params.items():
        if key not in VALID_HYPERPARAMS.keys():
            raise ValueError(f"Unknown hyperparameter: {key}")

        type_ = VALID_HYPERPARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")


def param_combos(params: HyperparameterGridDict) -> list[HyperparameterDict]:
    """Generate list of dictionaries covering all possible combinations of parameters
    and their values given in the params input.

    Parameters
    ----------
    params : dict
        dict of parameters with list of values for each parameter

    Returns
    -------
    list[dict]
        list of dicts, where each dict has a single value for each parameter.
        The dicts in the list cover all possible combinations of the input parameters.
    """
    combinations = []
    for combo in product(*params.values()):
        iteration = dict(zip(params.keys(), combo))
        combinations.append(iteration)

    return combinations


def generate_argument_sets(args: argparse.Namespace) -> list[list]:
    """Generate list of lists, where each sublist is the arguments required by the
    train_model_grid_search function:
        algorithm
        parameters
        vectors
        split
        save_model
        seed
        delete_model

    Parameters
    ----------
    args : argparse.Namespace
        Arguments parsed from command line

    Returns
    -------
    list[list]
        list of lists, where each sublist is the arguments for training a model with
        one of the combinations of algorithms and parameters
    """
    vectors = load_datasets(args.database, args.table)

    # Generate list of arguments for all combinations parameters for each algorithm
    argument_sets = []
    if args.save_model is None:
        save_model = DEFAULT_MODEL_LOCATION
    else:
        save_model = args.save_model

    # Generate all combinations of parameters
    for parameter_set in param_combos(args.params):
        arguments = [
            parameter_set,
            vectors,
            args.split,
            save_model,
            args.seed,
            args.keep_models,
        ]
        argument_sets.append(arguments)

    return argument_sets


def train_model_grid_search(
    parameters: dict,
    vectors: DataVectors,
    split: float,
    save_model: str,
    seed: int,
    keep_model: bool,
) -> dict:
    """Train model using given training algorithm and parameters,
    returning model performance statistics, model parameters and elapsed training time.

    Parameters
    ----------
    parameters : dict
        Dict of hyperparameters
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
    combine_name_labels : bool, optional
        If True, combine all NAME labels into a single NAME label.

    Returns
    -------
    dict
        Statistics from evaluating the model
    """
    start_time = time.monotonic()

    # Split data into train and test sets
    # The stratify argument means that each dataset is represented proportionally
    # in the train and tests sets, avoiding the possibility that train or tests sets
    # contain data from one dataset disproportionally.
    # We use typing.cast to stop pyright (and other checkers) from crying about the
    # unknown types of the output.
    (
        _,
        _,
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

    # Make model name unique
    save_model_path = Path(save_model).with_stem("model-" + str(uuid4()) + ".json")

    # Train model
    trainer = PerceptronTagger()
    trainer.train(
        tokenised_sentences=tokens_train,
        truth=tags_train,
        n_iter=parameters["n_iter"],
        min_feat_updates=parameters["min_feat_updates"],
        min_abs_weight=parameters["min_abs_weight"],
        quantize_bits=parameters["quantize_bits"],
        make_tag_dict=parameters["make_tag_dict"],
        tag_dict_frequency_threshold=parameters["tag_dict_frequency_threshold"],
        tag_dict_ambiguity_threshold=parameters["tag_dict_ambiguity_threshold"],
    )
    trainer.save(save_model_path)

    # Get model size, in MB
    model_size = os.path.getsize(save_model_path) / 1024**2

    # Evaluate model
    # Create NumpyCRFInference object for evaluation.
    logger.info("Evaluating model with test data.")
    # Create PerceptronTagger object for evaluation.
    tagger = PerceptronTagger(save_model_path)
    tags_pred, scores_pred = [], []
    for tokens in tokens_test:
        _, tags = zip(*tagger.tag(tokens))
        tags_pred.append(list(tags))
        scores_pred.append([1.0] * len(tokens))

    stats = evaluate(tags_pred, tags_test, seed)

    if not keep_model:
        save_model_path.unlink(missing_ok=True)

    return {
        "model_size": model_size,
        "params": parameters,
        "stats": stats,
        "time": time.monotonic() - start_time,
    }


def grid_search_tagger(args: argparse.Namespace):
    """Perform a grid search over the specified hyperparameters and return the model
    performance statistics for each combination of parameters.

    Parameters
    ----------
    args : argparse.Namespace
        Grid search configuration
    """
    if args.generate_param_json:
        generate_parameter_json(args)
        return

    validate_hyperparams(args.params)
    arguments = generate_argument_sets(args)

    logger.info("Grid search started at %s", time.strftime("%H:%M:%S"))
    logger.info("Grid search over %d hyperparameters combinations.", len(arguments))
    logger.info("%d is the random seed used for the train/test split.", args.seed)

    eval_results = []
    with cf.ProcessPoolExecutor(max_workers=args.processes) as executor:
        futures = [executor.submit(train_model_grid_search, *a) for a in arguments]
        logger.info("Queued for separate runs against %d algorithms.", len(args.algos))
        for idx, future in enumerate(cf.as_completed(futures)):
            if exception := future.exception():
                logger.error(
                    "%s algorithm failed with exception:",
                    convert_num_ordinal(idx + 1),
                    exc_info=exception,
                )
            else:
                result = future.result()
                eval_results.append(result)

                completed_at = time.strftime("%H:%M")
                elapsed = timedelta(seconds=int(result["time"]))
                logger.info(
                    "%s algorithm completed at %s (%s elapsed).",
                    convert_num_ordinal(idx + 1),
                    completed_at,
                    elapsed,
                )

    # Sort with highest sentence accuracy first, then highest token accuracy
    eval_results = sorted(
        eval_results,
        key=lambda x: (x["stats"].sentence.accuracy, x["stats"].token.accuracy),
        reverse=True,
    )

    headers = [
        "Parameters",
        "Token accuracy",
        "Sentence accuracy",
        "Time",
        "Size (MB)",
    ]
    table = []
    for result in eval_results:
        params = result["params"]
        stats = result["stats"]
        size = result["model_size"]
        elapsed = timedelta(seconds=int(result["time"]))
        table.append(
            [
                ", ".join([f"{k}={v}" for k, v in params.items()]),
                f"{100 * stats.token.accuracy:.2f}%",
                f"{100 * stats.sentence.accuracy:.2f}%",
                str(elapsed),
                f"{size:.2f}",
            ]
        )

    print(
        "\n"
        + tabulate(
            table,
            headers=headers,
            tablefmt="fancy_grid",
            maxcolwidths=[130, None, None, None, None],
            stralign="left",
            numalign="right",
        )
        + "\n"
    )


def generate_parameter_json(args: argparse.Namespace) -> None:
    """Write a template json file for gridsearch containing the possible parameters for
    the given algorithms for use with the --parameters-from-json command line argument
    for gridsearch.

    Parameters
    ----------
    args : argparse.Namespace
        Grid search configuration
    """
    parameter_json = {"params": {}}
    for param in VALID_HYPERPARAMS.keys():
        parameter_json["params"][param] = []

    print('Generated "gridsearch_params_tagger.json".')
    with open("gridsearch_params_tagger.json", "w") as f:
        json.dump(parameter_json, f, indent=2)

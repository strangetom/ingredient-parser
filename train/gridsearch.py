#!/usr/bin/env python3

import argparse
import concurrent.futures as cf
import logging
import os
import time
from datetime import timedelta
from itertools import product
from pathlib import Path
from uuid import uuid4

from sklearn.model_selection import train_test_split
from tabulate import tabulate

from ingredient_parser.inference import NumpyCRFInference

from .train_model import DEFAULT_MODEL_LOCATION
from .trainers import CRFHyperParameters, NumpyCRFTrainer
from .training_utils import (
    DataVectors,
    convert_num_ordinal,
    evaluate,
    load_datasets,
)

logger = logging.getLogger(__name__)

# Valid parameter options for trainer and expected types
VALID_HYPER_PARAMS = {
    "optimizer": (str,),
    "l2": (float, int),
    "maxiter": (int,),
    "maxls": (int,),
    "maxcor": (int,),
    "ftol": (float, int),
    "quantize_bits": (int, type(None)),
    "min_abs_weight": (float, int),
}
VALID_OPTIMIZERS_CHOICES = ["L-BFGS-B"]

VALID_POST_TRAINING_PARAMS = {
    "constrain_transitions": (bool,),
    "expect_name_in_output": (bool,),
}


def validate_hyper_params(hyper_params: dict) -> None:
    """Validate training algorithm parameters.

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
        if key not in VALID_HYPER_PARAMS.keys():
            raise ValueError(f"Unknown parameter for LBFGS algorithm: {key}")

        type_ = VALID_HYPER_PARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")

        if key == "optimizer":
            for v in value:
                if v not in VALID_OPTIMIZERS_CHOICES:
                    raise ValueError(
                        f"Optimizer value must be one of {VALID_OPTIMIZERS_CHOICES}"
                    )


def validate_post_training_params(post_training_params: dict) -> None:
    """Validate post training algorithm parameters, applicable to all algorithms

    Check that the parameter names are valid.
    Check that the parameter value types are valid.

    Parameters
    ----------
    post_training_params : dict
        dict of parameters and their values.

    Raises
    ------
    ValueError
        Exception indicating invalid parameter.
    """
    for key, value in post_training_params.items():
        if key not in VALID_POST_TRAINING_PARAMS.keys():
            raise ValueError(f"Unknown post training parameter: {key}")

        type_ = VALID_POST_TRAINING_PARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")


def param_combos(hyper_params: dict) -> list[dict]:
    """Generate list of dictionaries covering all possible combinations of parameters
    and their values given in the params input.

    Parameters
    ----------
    hyper_params : dict
        dict of parameters with list of values for each parameter

    Returns
    -------
    list[dict]
        list of dicts, where each dict has a single value for each parameter.
        The dicts in the list cover all possible combinations of the input parameters.
    """
    combinations = []
    for combo in product(*hyper_params.values()):
        iteration = dict(zip(hyper_params.keys(), combo))
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
    vectors = load_datasets(
        args.database,
        args.table,
        args.datasets,
        discard_other=True,
        combine_name_labels=args.combine_name_labels,
    )

    # Generate list of arguments for all combinations parameters for each algorithm
    argument_sets = []
    hyper_params = args.hyper_params | args.pt_params

    if args.save_model is None:
        save_model = Path(DEFAULT_MODEL_LOCATION)
    else:
        save_model = Path(args.save_model)

    # Generate all combinations of parameters
    for parameter_set in param_combos(hyper_params):
        arguments = [
            parameter_set,
            vectors,
            args.split,
            save_model,
            args.seed,
            args.keep_models,
            args.combine_name_labels,
        ]
        argument_sets.append(arguments)

    return argument_sets


def train_model_grid_search(
    parameters: dict,
    vectors: DataVectors,
    split: float,
    save_model: Path,
    seed: int,
    keep_model: bool,
    combine_name_labels: bool,
) -> dict:
    """Train model using given training algorithm and parameters,
    returning model performance statistics, model parameters and elapsed training time.

    Parameters
    ----------
    parameters : dict
        Dict of global and training algorithm specific hyperparameters
    vectors : DataVectors
        Vectors loaded from training csv files
    split : float
        Fraction of vectors to use for evaluation.
    save_model : Path
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

    # Make model name unique
    save_model_path = Path(save_model).with_stem("model-" + str(uuid4()) + ".json")

    # Remove post training parameters from parameters dict
    post_training_parameters = {
        "constrain_transitions": parameters["constrain_transitions"],
        "expect_name_in_output": parameters["expect_name_in_output"],
    }
    del parameters["constrain_transitions"]
    del parameters["expect_name_in_output"]

    # Train model
    trainer = NumpyCRFTrainer(features_train, truth_train)
    # Set parameters
    trainer.hyperparameters = CRFHyperParameters(**parameters)
    trainer.train(save_model_path)
    config_file = trainer.write_model_config(
        save_model_path, extra_parameters=post_training_parameters
    )
    # Get model size, in MB
    model_size = os.path.getsize(save_model_path) / 1024**2

    # Evaluate model
    # Create NumpyCRFInference object for evaluation.
    logger.info("Evaluating model with test data.")
    tagger = NumpyCRFInference(save_model, combine_name_labels)

    labels_pred = []
    for X in features_test:
        labels, _ = zip(
            *tagger.tag_from_features(
                X,
                expect_name_in_output=post_training_parameters["expect_name_in_output"],
                constrain_transitions=post_training_parameters["constrain_transitions"],
            )
        )
        labels_pred.append(list(labels))
    stats = evaluate(labels_pred, truth_test, seed, combine_name_labels)

    # We don't need to keep the crfsuite model.
    if not keep_model:
        save_model_path.unlink(missing_ok=True)
        config_file.unlink(missing_ok=True)

    return {
        "algo": parameters["optimizer"],
        "model_size": model_size,
        "params": parameters | post_training_parameters,
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
    if args.hyper_params is not None:
        validate_hyper_params(args.hyper_params)

    if args.pt_params != dict():
        validate_post_training_params(args.pt_params)

    arguments = generate_argument_sets(args)

    logger.info(f"Grid search over {len(arguments)} hyperparameters combinations.")
    logger.info(f"{args.seed} is the random seed used for the train/test split.")

    eval_results = []
    with cf.ProcessPoolExecutor(max_workers=args.processes) as executor:
        futures = [executor.submit(train_model_grid_search, *a) for a in arguments]
        for idx, future in enumerate(cf.as_completed(futures)):
            logger.info(f"{convert_num_ordinal(idx + 1)} algorithm completed")
            eval_results.append(future.result())

    # Sort with highest sentence accuracy first, then highest token accuracy
    eval_results = sorted(
        eval_results,
        key=lambda x: (x["stats"].sentence.accuracy, x["stats"].token.accuracy),
        reverse=True,
    )

    headers = [
        "Algorithm",
        "Parameters",
        "Token accuracy",
        "Sentence accuracy",
        "Time",
        "Size (MB)",
    ]
    table = []
    for result in eval_results:
        algo = result["algo"]
        params = result["params"]
        stats = result["stats"]
        size = result["model_size"]
        time = timedelta(seconds=int(result["time"]))
        table.append(
            [
                algo,
                ", ".join([f"{k}={v}" for k, v in params.items()]),
                f"{100 * stats.token.accuracy:.2f}%",
                f"{100 * stats.sentence.accuracy:.2f}%",
                str(time),
                f"{size:.2f}",
            ]
        )

    print(
        "\n"
        + tabulate(
            table,
            headers=headers,
            tablefmt="fancy_grid",
            maxcolwidths=[None, 130, None, None, None, None],
            stralign="left",
            numalign="right",
        )
        + "\n"
    )

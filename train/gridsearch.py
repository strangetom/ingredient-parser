#!/usr/bin/env python3

import argparse
import concurrent.futures as cf
import os
import time
from datetime import timedelta
from itertools import product
from pathlib import Path
from uuid import uuid4

import pycrfsuite
from sklearn.model_selection import train_test_split
from tabulate import tabulate
from tqdm import tqdm

from .train_model import DEFAULT_MODEL_LOCATION, ModelType, get_model_type
from .training_utils import (
    DataVectors,
    evaluate,
    load_datasets,
)

# Valid parameter options for LBFGS training algorithm and expected types
VALID_LBFGS_PARAMS = {
    "c1": (float, int),
    "c2": (float, int),
    "max_iterations": (int,),
    "num_memories": (int,),
    "period": (int,),  # stop in docs
    "delta": (float, int),
    "linesearch": (str,),
    "max_linesearch": (int,),
}
VALID_LINESEARCH_OPTS = ["MoreThuente", "Backtracking", "StrongBacktracking"]

# Valid parameter options for AP training algorithm and expected types
VALID_AP_PARAMS = {
    "max_iterations": (int,),
    "epsilon": (float, int),
}

# Valid parameter options for L2SGD training algorithm and expected types
VALID_L2SGD_PARAMS = {
    "c2": (float, int),
    "max_iterations": (int,),
    "period": (int,),
    "delta": (float,),
    "calibration.eta": (float, int),
    "calibration.rate": (float, int),
    "calibration.samples": (int,),
    "calibration.candidates": (int,),
    "calibration.max_trials": (int,),
}

# Valid parameter options for PA training algorithm and expected types
VALID_PA_PARAMS = {
    "type": (int,),
    "c": (float, int),
    "error_sensitive": (bool,),
    "averaging": (bool,),
    "max_iterations": (int,),
    "epsilon": (float, int),
}

# Valid parameter options for AROW training algorithm and expected types
VALID_AROW_PARAMS = {
    "variance": (float, int),
    "gamma": (float, int),
    "max_iterations": (int,),
    "epsilon": (float, int),
}

# Valid parameter options for all training algorithms and expected types
VALID_GLOBAL_PARAMS = {
    "feature.minfreq": (int,),
    "feature.possible_states": (bool,),
    "feature.possible_transitions": (bool,),
}


def validate_lbfgs_params(lbfgs_params: dict) -> None:
    """Validate LBFGS training algorithm parameters.

    Check that the parameter names are valid.
    Check that the parameter value types are valid.
    Check that the parameter values are valid for the linesearch parameter.

    Parameters
    ----------
    lbfgs_params : dict
        dict of parameters and their values.

    Raises
    ------
    ValueError
        Expection indicating invalid parameter.
    """
    for key, value in lbfgs_params.items():
        if key not in VALID_LBFGS_PARAMS.keys():
            raise ValueError(f"Unknown parameter for LBFGS algorithm: {key}")

        type_ = VALID_LBFGS_PARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")

        if key == "linesearch":
            for v in value:
                if v not in VALID_LINESEARCH_OPTS:
                    raise ValueError(
                        f"Linesearch values must be one of {VALID_LINESEARCH_OPTS}"
                    )


def validate_ap_params(ap_params: dict) -> None:
    """Validate AP training algorithm parameters.

    Check that the parameter names are valid.
    Check that the parameter value types are valid.

    Parameters
    ----------
    ap_params : dict
        dict of parameters and their values.

    Raises
    ------
    ValueError
        Expection indicating invalid parameter.
    """
    for key, value in ap_params.items():
        if key not in VALID_AP_PARAMS.keys():
            raise ValueError(f"Unknown parameter for AP algorithm: {key}")

        type_ = VALID_AP_PARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")


def validate_l2sgd_params(l2sgd_params: dict) -> None:
    """Validate L2SGD training algorithm parameters.

    Check that the parameter names are valid.
    Check that the parameter value types are valid.

    Parameters
    ----------
    l2sgd_params : dict
        dict of parameters and their values.

    Raises
    ------
    ValueError
        Expection indicating invalid parameter.
    """
    for key, value in l2sgd_params.items():
        if key not in VALID_L2SGD_PARAMS.keys():
            raise ValueError(f"Unknown parameter for AP algorithm: {key}")

        type_ = VALID_L2SGD_PARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")


def validate_pa_params(pa_params: dict) -> None:
    """Validate PA training algorithm parameters.

    Check that the parameter names are valid.
    Check that the parameter value types are valid.
    Check that the 'type' has a value in (0,1,2)

    Parameters
    ----------
    pa_params : dict
        dict of parameters and their values.

    Raises
    ------
    ValueError
        Expection indicating invalid parameter.
    """
    for key, value in pa_params.items():
        if key not in VALID_PA_PARAMS.keys():
            raise ValueError(f"Unknown parameter for AP algorithm: {key}")

        type_ = VALID_PA_PARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")

        if key == "type":
            for v in value:
                if v not in (0, 1, 2):
                    raise ValueError("Type value must be 0, 1 or 2")


def validate_arow_params(arow_params: dict) -> None:
    """Validate AROW training algorithm parameters.

    Check that the parameter names are valid.
    Check that the parameter value types are valid.

    Parameters
    ----------
    arow_params : dict
        dict of parameters and their values.

    Raises
    ------
    ValueError
        Expection indicating invalid parameter.
    """
    for key, value in arow_params.items():
        if key not in VALID_AROW_PARAMS.keys():
            raise ValueError(f"Unknown parameter for AP algorithm: {key}")

        type_ = VALID_AROW_PARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")


def validate_global_params(global_params: dict) -> None:
    """Validate global training algorithm parameters, applicable to all algorithms

    Check that the parameter names are valid.
    Check that the parameter value types are valid.

    Parameters
    ----------
    global_params : dict
        dict of parameters and their values.

    Raises
    ------
    ValueError
        Expection indicating invalid parameter.
    """
    for key, value in global_params.items():
        if key not in VALID_GLOBAL_PARAMS.keys():
            raise ValueError(f"Unknown global parameter: {key}")

        type_ = VALID_GLOBAL_PARAMS[key]
        type_str = f"list[{'|'.join(t.__name__ for t in type_)}]"
        if not isinstance(value, list):
            raise ValueError(f"Parameter values for {key} should be {type_str}")

        for v in value:
            if not isinstance(v, type_):
                raise ValueError(f"Parameter values for {key} should be {type_str}")


def param_combos(params: dict) -> list[dict]:
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
    vectors = load_datasets(
        args.database, args.table, args.datasets, get_model_type(args.model)
    )

    # Generate list of arguments for all combinations parameters for each algorithm
    argument_sets = []
    params = None
    for algo in args.algos:
        if algo == "lbfgs":
            params = args.lbfgs_params
        elif algo == "ap":
            params = args.ap_params
        elif algo == "l2sgd":
            params = args.l2sgd_params
        elif algo == "pa":
            params = args.pa_params
        elif algo == "arow":
            params = args.arow_params

        # Join alogithm specifc parameters with global parameters
        if params is None:
            # No algorithm specific parameters set
            params = args.global_params
        else:
            params = params | args.global_params

        if args.save_model is None:
            save_model = DEFAULT_MODEL_LOCATION[args.model]
        else:
            save_model = args.save_model

        # Generate all combinations of parameters
        for parameter_set in param_combos(params):
            arguments = [
                algo,
                parameter_set,
                vectors,
                args.split,
                save_model,
                args.seed,
                args.keep_models,
                get_model_type(args.model),
            ]
            argument_sets.append(arguments)

    return argument_sets


def train_model_grid_search(
    algo: str,
    parameters: dict,
    vectors: DataVectors,
    split: float,
    save_model: str,
    seed: int,
    keep_model: bool,
    model_type: ModelType,
) -> dict:
    """Train model using given training algorithm and parameters,
    returning model performance statistics, model parameters and elapsed training time.

    Parameters
    ----------
    algo : str
        Training algorithm
    parameters : dict
        Dict of global and training algorithm specific hyperparameters
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
    model_type : ModelType
        Type of model gridsearch is being performed on.

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

    # Make model name unique
    save_model_path = Path(save_model).with_stem("model-" + str(uuid4()))

    # Train model
    trainer = pycrfsuite.Trainer(algo, verbose=False)  # type: ignore
    # Set parameters
    trainer.set_params(parameters)
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)
    trainer.train(str(save_model_path))
    # Get model size, in MB
    model_size = os.path.getsize(save_model_path) / 1024**2

    # Evaluate model
    tagger = pycrfsuite.Tagger()  # type: ignore
    tagger.open(str(save_model_path))
    labels_pred = [tagger.tag(X) for X in features_test]
    stats = evaluate(labels_pred, truth_test, seed, model_type)

    if not keep_model:
        save_model_path.unlink(missing_ok=True)

    return {
        "algo": algo,
        "model_size": model_size,
        "params": parameters,
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
    if args.lbfgs_params is not None:
        validate_lbfgs_params(args.lbfgs_params)

    if args.ap_params is not None:
        validate_ap_params(args.ap_params)

    if args.l2sgd_params is not None:
        validate_l2sgd_params(args.l2sgd_params)

    if args.pa_params is not None:
        validate_pa_params(args.pa_params)

    if args.arow_params is not None:
        validate_arow_params(args.arow_params)

    if args.global_params != dict():
        validate_global_params(args.global_params)

    arguments = generate_argument_sets(args)

    print(f"[INFO] Grid search over {len(arguments)} hyperparameters combinations.")
    print(f"[INFO] {args.seed} is the random seed used for the train/test split.")

    eval_results = []
    with cf.ProcessPoolExecutor(max_workers=args.processes) as executor:
        futures = [executor.submit(train_model_grid_search, *a) for a in arguments]
        for future in tqdm(cf.as_completed(futures), total=len(futures)):
            eval_results.append(future.result())

    # Sort with highest sentence accuracy first
    eval_results = sorted(
        eval_results, key=lambda x: x["stats"].sentence.accuracy, reverse=True
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
        tabulate(
            table,
            headers=headers,
            tablefmt="fancy_grid",
            maxcolwidths=[None, 130, None, None, None, None],
        )
    )

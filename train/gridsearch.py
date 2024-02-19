#!/usr/bin/env python3

import argparse
import time
from datetime import timedelta
from itertools import product
from multiprocessing import Pool

import pycrfsuite
from sklearn.model_selection import train_test_split
from tabulate import tabulate

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
    "stop": (int,),
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
    """Validate LBFGS training algorithm parameters.

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
    vectors = load_datasets(args.database, args.datasets)

    # Generate list of arguments for all combinations parameters for each algorithm
    argument_sets = []
    for algo in args.algos:
        if algo == "lbfgs":
            params = args.lbfgs_params
        elif algo == "ap":
            params = args.ap_params

        # Generate all combinations of parameters
        for parameter_set in param_combos(params):
            arguments = [
                algo,
                parameter_set,
                vectors,
                args.split,
                args.save_model,
                args.seed,
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
) -> dict:
    """Train model using given training algorithm and parameters,
    returning model performance statistics, model parameters and elapsed training time.

    Parameters
    ----------
    algo : str
        Training algorithm
    parameters : dict
        Training algorithm specific hyperparameters
    vectors : DataVectors
        Vectors loaded from training csv files
    split : float
        Fraction of vectors to use for evaluation.
    save_model : str
        Path to save trained model to.
    seed : int
        Integer used as seed for splitting the vectors between the training and
        testing sets.

    Returns
    -------
    dict
        Statistics from evaluating the model
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
    print(f"[INFO] Training model using {algo} algorithm with {parameters}.")
    start_time = time.monotonic()

    trainer = pycrfsuite.Trainer(algo, verbose=False)
    # Join default parameters with algorithm specific combination
    trainer.set_params(
        {
            "feature.possible_states": True,
            "feature.possible_transitions": True,
        }
        | parameters
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
        "algo": algo,
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

    arguments = generate_argument_sets(args)

    print(f"[INFO] Grid search over {len(arguments)} hyperparameters combinations.")
    print(f"[INFO] {args.seed} is the random seed used for the train/test split.")
    with Pool(processes=args.processes) as pool:
        print("[INFO] Created multiprocessing pool for training models in parallel.")
        eval_results = pool.starmap(train_model_grid_search, arguments)

    headers = ["Algorithm", "Parameters", "Token accuracy", "Sentence accuracy", "Time"]
    table = []
    for result in eval_results:
        algo = result["algo"]
        params = result["params"]
        stats = result["stats"]
        time = timedelta(seconds=int(result["time"]))
        table.append(
            [
                algo,
                params,
                f"{100 * stats.token.accuracy:.2f}%",
                f"{100 * stats.sentence.accuracy:.2f}%",
                str(time),
            ]
        )

    print(tabulate(table, headers=headers, tablefmt="simple_outline"))

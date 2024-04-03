#!/usr/bin/env python3

import argparse
import json
import os
from random import randint

from train import (
    check_label_consistency,
    grid_search,
    train_multiple,
    train_single,
)


class ParseJsonArg(argparse.Action):
    """Custom argparse.Action to parse JSON argument into dict."""

    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_strings):
        setattr(namespace, self.dest, json.loads(values))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train a CRF model to parse label token from recipe \
                    ingredient sentences."
    )
    subparsers = parser.add_subparsers(dest="command", help="Training commands")

    train_parser = subparsers.add_parser("train", help="Train CRF model.")
    train_parser.add_argument(
        "--database",
        help="Path to database of training data",
        type=str,
        dest="database",
        required=True,
    )
    train_parser.add_argument(
        "--datasets",
        help="Datasets to use in training and evaluating the model",
        dest="datasets",
        nargs="*",
        default=["bbc", "cookstr", "nyt"],
    )
    train_parser.add_argument(
        "--split",
        default=0.20,
        type=float,
        help="Fraction of data to be used for testing",
    )
    train_parser.add_argument(
        "--save-model",
        default="ingredient_parser/model.en.crfsuite",
        help="Path to save model to",
    )
    train_parser.add_argument(
        "--seed",
        default=None,
        type=int,
        help="Seed value used for train/test split.",
    )
    train_parser.add_argument(
        "--html",
        action="store_true",
        help="Output a markdown file containing detailed results.",
    )
    train_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Output a file containing detailed results about accuracy.",
    )
    train_parser.add_argument(
        "--confusion",
        action="store_true",
        help="Plot confusion matrix of token labels.",
    )

    multiple_parser_help = "Average CRF performance across multiple training cycles."
    multiple_parser = subparsers.add_parser("multiple", help=multiple_parser_help)
    multiple_parser.add_argument(
        "--database",
        help="Path to database of training data",
        type=str,
        dest="database",
        required=True,
    )
    multiple_parser.add_argument(
        "--datasets",
        help="Datasets to use in training and evaluating the model",
        dest="datasets",
        nargs="*",
        default=["bbc", "cookstr", "nyt"],
    )
    multiple_parser.add_argument(
        "--split",
        default=0.20,
        type=float,
        help="Fraction of data to be used for testing",
    )
    multiple_parser.add_argument(
        "--save-model",
        default="ingredient_parser/model.en.crfsuite",
        help="Path to save model to",
    )
    multiple_parser.add_argument(
        "--html",
        action="store_true",
        help="Output a markdown file containing detailed results.",
    )
    multiple_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Output a file containing detailed results about accuracy.",
    )
    multiple_parser.add_argument(
        "--confusion",
        action="store_true",
        help="Plot confusion matrix of token labels.",
    )
    multiple_parser.add_argument(
        "-r",
        "--runs",
        default=10,
        type=int,
        help="Number of times to run the training and evaluation of the model.",
    )
    multiple_parser.add_argument(
        "-p",
        "--processes",
        default=os.cpu_count() - 1,
        type=int,
        help="Number of processes to spawn. Default to number of cpu cores.",
    )

    gridsearch_parser_help = (
        "Grid search over all combinations of model hyperparameters."
    )
    gridsearch_parser = subparsers.add_parser("gridsearch", help=multiple_parser_help)
    gridsearch_parser.add_argument(
        "--database",
        help="Path to database of training data",
        type=str,
        dest="database",
        required=True,
    )
    gridsearch_parser.add_argument(
        "--datasets",
        help="Datasets to use in training and evaluating the model",
        dest="datasets",
        nargs="*",
        default=["bbc", "cookstr", "nyt"],
    )
    gridsearch_parser.add_argument(
        "--split",
        default=0.20,
        type=float,
        help="Fraction of data to be used for testing",
    )
    gridsearch_parser.add_argument(
        "--save-model",
        default="ingredient_parser/model.en.crfsuite",
        help="Path to save model to",
    )
    gridsearch_parser.add_argument(
        "--keep-models",
        action="store_true",
        default=False,
        help="Keep models after evaluation instead of deleting.",
    )
    gridsearch_parser.add_argument(
        "-p",
        "--processes",
        default=os.cpu_count() - 1,
        type=int,
        help="Number of processes to spawn. Default to number of cpu cores.",
    )
    gridsearch_parser.add_argument(
        "--seed",
        default=randint(0, 1_000_000_000),
        type=int,
        help="Seed value used for train/test split.",
    )
    gridsearch_parser.add_argument(
        "--algos",
        default=["lbfgs"],
        choices=["lbfgs", "ap", "l2sgd", "pa", "arow"],
        nargs="+",
        help="CRF training algorithms to use.",
    )
    gridsearch_parser.add_argument(
        "--lbfgs-params",
        help="""LBFGS algorithm parameters as JSON. 
        The values for each parameter should be a list.
        Any parameters not given will take their default value.""",
        action=ParseJsonArg,
    )
    gridsearch_parser.add_argument(
        "--ap-params",
        help="""AP algorithm parameters as JSON. 
        The values for each parameter should be a list.
        Any parameters not given will take their default value.""",
        action=ParseJsonArg,
    )
    gridsearch_parser.add_argument(
        "--l2sgd-params",
        help="""L2GSD algorithm parameters as JSON. 
        The values for each parameter should be a list.
        Any parameters not given will take their default value.""",
        action=ParseJsonArg,
    )
    gridsearch_parser.add_argument(
        "--pa-params",
        help="""PA algorithm parameters as JSON. 
        The values for each parameter should be a list.
        Any parameters not given will take their default value.""",
        action=ParseJsonArg,
    )
    gridsearch_parser.add_argument(
        "--arow-params",
        help="""AROW algorithm parameters as JSON. 
        The values for each parameter should be a list.
        Any parameters not given will take their default value.""",
        action=ParseJsonArg,
    )
    gridsearch_parser.add_argument(
        "--global-params",
        help="""Global algorithm parameters, applicable to all algorithms, as JSON. 
        The values for each parameter should be a list.
        Any parameters not given will take their default value.""",
        action=ParseJsonArg,
        default=dict(),
    )

    utility_help = "Utilities to aid cleaning training data."
    utility_parser = subparsers.add_parser("utility", help=utility_help)
    utility_parser.add_argument(
        "utility",
        choices=["consistency"],
        help="Cleaning utility to execute",
    )
    utility_parser.add_argument(
        "--database",
        help="Path to database of training data",
        type=str,
        dest="database",
        required=True,
    )
    utility_parser.add_argument(
        "--datasets",
        help="Datasets to use in training and evaluating the model",
        dest="datasets",
        nargs="*",
        default=["bbc", "cookstr", "nyt"],
    )

    args = parser.parse_args()

    if args.command == "train":
        train_single(args)
    elif args.command == "multiple":
        train_multiple(args)
    elif args.command == "gridsearch":
        grid_search(args)
    elif args.command == "utility":
        if args.utility == "consistency":
            check_label_consistency(args)

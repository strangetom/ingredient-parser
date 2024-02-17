import argparse

from train import (
    check_label_consistency,
    train_multiple,
    train_single,
)

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
        default=0.25,
        type=float,
        help="Fraction of data to be used for testing",
    )
    train_parser.add_argument(
        "--save-model",
        default="ingredient_parser/model.crfsuite",
        help="Path to save model to",
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
        default=0.25,
        type=float,
        help="Fraction of data to be used for testing",
    )
    multiple_parser.add_argument(
        "--save-model",
        default="ingredient_parser/model.crfsuite",
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
        "-r",
        "--runs",
        default=10,
        type=int,
        help="Number of times to run the training and evaluation of the model.",
    )
    multiple_parser.add_argument(
        "-p",
        "--processes",
        default=None,
        type=int,
        help="Number of processes to spawn. Default to number of cpu cores.",
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
    elif args.command == "utility":
        if args.utility == "consistency":
            check_label_consistency(args)

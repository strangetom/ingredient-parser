import argparse

from train import (
    check_label_consistency,
    find_missing_labels,
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
        "--datasets",
        "-d",
        help="Datasets in csv format",
        action="extend",
        dest="datasets",
        nargs="+",
        required=True,
    )
    train_parser.add_argument(
        "-s",
        "--split",
        default=0.25,
        type=float,
        help="Fraction of data to be used for testing",
    )
    train_parser.add_argument(
        "-n",
        "--number",
        default=30000,
        type=int,
        help="Maximum of entries from a dataset to use (train+test)",
    )
    train_parser.add_argument(
        "-m",
        "--save-model",
        default="ingredient_parser/model.crfsuite",
        help="Path to save model to",
    )
    train_parser.add_argument(
        "--html",
        action="store_true",
        help="Output a markdown file containing detailed results.",
    )

    multiple_parser_help = "Average CRF performance across multiple training cycles."
    multiple_parser = subparsers.add_parser("multiple", help=multiple_parser_help)
    multiple_parser.add_argument(
        "--datasets",
        "-d",
        help="Datasets in csv format",
        action="extend",
        dest="datasets",
        nargs="+",
        required=True,
    )
    multiple_parser.add_argument(
        "-s",
        "--split",
        default=0.25,
        type=float,
        help="Fraction of data to be used for testing",
    )
    multiple_parser.add_argument(
        "-n",
        "--number",
        default=30000,
        type=int,
        help="Maximum of entries from a dataset to use (train+test)",
    )
    multiple_parser.add_argument(
        "-m",
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
        "-r",
        "--runs",
        default=10,
        type=int,
        help="Number of times to run the training and evaluation of the model.",
    )

    utility_help = "Utilities to aid cleaning training data."
    utility_parser = subparsers.add_parser("utility", help=utility_help)
    utility_parser.add_argument(
        "utility",
        choices=["missing", "consistency"],
        help="Cleaning utility to execute",
    )
    utility_parser.add_argument(
        "--datasets",
        "-d",
        help="Datasets in csv format",
        action="extend",
        dest="datasets",
        nargs="+",
        required=True,
    )
    utility_parser.add_argument(
        "-n",
        "--number",
        default=30000,
        type=int,
        help="Number of entries in dataset to check",
    )

    args = parser.parse_args()

    if args.command == "train":
        train_single(args)
    elif args.command == "multiple":
        train_multiple(args)
    elif args.command == "utility":
        if args.utility == "missing":
            find_missing_labels(args)
        elif args.utility == "consistency":
            check_label_consistency(args)

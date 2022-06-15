#!/usr/bin/env python3

import argparse
import csv
from dataclasses import dataclass
from typing import Dict, List

from sklearn.model_selection import train_test_split
from sklearn_crfsuite import CRF, metrics

from Preprocess import PreProcessor


@dataclass
class Stats:
    """Dataclass to store statistics on model performance"""

    total_sentences: int
    correct_sentences: int
    total_words: int
    correct_words: int


def load_csv(csv_filename: str) -> tuple[List[str], List[Dict[str, str]]]:
    """Load csv file generated py ```generate_training_testing_csv.py``` and parse contents into ingredients and labels lists

    Parameters
    ----------
    csv_filename : str
        Name of csv file

    Returns
    -------
    List[str]
        List of ingredient strings
    List[Dict[str, str]]
        List of dictionaries, each dictionary the ingredient labels
    """
    labels, ingredients = [], []
    with open(csv_filename, "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip first row
        for row in reader:
            ingredients.append(row[0])
            labels.append(
                {
                    "name": row[1].strip(),
                    "quantity": row[2].strip(),
                    "unit": row[3].strip(),
                    "comment": row[4].strip(),
                }
            )
    return ingredients, labels


def singlarise_unit(token: str) -> str:
    """Singularise units
    e.g. cups -> cup, tablespoons -> tablespoon

    Parameters
    ----------
    token : str
        Token to singularise

    Returns
    -------
    str
        Singularised token or original token
    """
    units = {
        "cups": "cup",
        "tablespoons": "tablespoon",
        "teaspoons": "teaspoon",
        "pounds": "pound",
        "ounces": "ounce",
        "cloves": "clove",
        "sprigs": "sprig",
        "pinches": "pinch",
        "bunches": "bunch",
        "slices": "slice",
        "grams": "gram",
        "heads": "head",
        "quarts": "quart",
        "stalks": "stalk",
        "pints": "pint",
        "pieces": "piece",
        "sticks": "stick",
        "dashes": "dash",
        "fillets": "fillet",
        "cans": "can",
        "ears": "ear",
        "packages": "package",
        "strips": "strip",
        "bulbs": "bulb",
        "bottles": "bottle",
    }
    if token in units.keys():
        return units[token]
    else:
        return token


def match_label(token: str, labels: Dict[str, str]) -> str:
    """Match a token to it's label
    This is naive in that it assumes a token can only have one label with the sentence

    Parameters
    ----------
    token : str
        Token to match

    Returns
    -------
    str
        Label for token, or None
    """

    # TODO:
    # 1. Handle ingredients that have both US and metric units (or remove them from training data...)
    # 2. Singularise all units so they match the label

    # Make lower case first, beccause all labels are lower case
    token = token.lower()
    token = singlarise_unit(token)

    if token in labels["quantity"]:
        return "QTY"
    elif token in labels["unit"]:
        return "UNIT"
    elif token in labels["name"]:
        return "NAME"
    elif token in labels["comment"]:
        return "COMMENT"
    else:
        return "OTHER"


def transform_to_dataset(
    sentences: List[str], labels: List[Dict[str, str]]
) -> tuple[List[Dict[str, str]], List[str]]:
    """Transform dataset into feature lists for each sentence

    Parameters
    ----------
    sentences : List[str]
        Sentences to transform
    labels : List[Dict[str, str]]
        Labels for tokens in each sentence

    Returns
    -------
    List[Dict[str, str]]
        List of transformed sentences
     List[str]
        List of transformed labels
    """
    X, y = [], []

    for sentence, labels in zip(sentences, labels):
        p = PreProcessor(sentence)
        X.append(p.sentence_features())
        y.append(
            [
                match_label(p.tokenized_sentence[index], labels)
                for index in range(len(p.tokenized_sentence))
            ]
        )

    return X, y


def evaluate(
    X: List[Dict[str, str]], predictions: List[List[str]], truths: List[List[str]]
) -> Stats:

    total_sentences = 0
    correct_sentences = 0
    total_words = 0
    correct_words = 0

    for sentence, prediction, truth in zip(X, predictions, truths):
        correct_words_per_sentence = 0
        total_words_per_sentence = 0

        for token, p, t in zip(sentence, prediction, truth):
            # Skip commas
            if token == ",":
                continue

            total_words += 1
            total_words_per_sentence += 1

            # Count as match if guess matches actual, ignoring the B- or I- part
            if p == t:
                correct_words_per_sentence += 1
                correct_words += 1

        total_sentences += 1
        if correct_words_per_sentence == total_words_per_sentence:
            correct_sentences += 1

    return Stats(total_sentences, correct_sentences, total_words, correct_words)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate CRF++ compatible training and testing data files from csv"
    )
    parser.add_argument("-i", "--input", help="Path to input csv file")
    parser.add_argument(
        "-s",
        "--split",
        default=0.25,
        type=float,
        help="Fraction of data to be used for testing",
    )
    parser.add_argument(
        "-n",
        "--number",
        default=20000,
        type=int,
        help="Number of entries from dataset to use (train+test)",
    )
    args = parser.parse_args()

    nyt_ingredients, nyt_labels = load_csv(args.input)
    sf_ingredients, sf_labels = load_csv("../data/strangerfoods/labelled_data.csv")

    (
        nyt_ingredients_train,
        nyt_ingredients_test,
        nyt_labels_train,
        nyt_labels_test,
    ) = train_test_split(
        nyt_ingredients[: args.number], nyt_labels[: args.number], test_size=args.split
    )
    (
        sf_ingredients_train,
        sf_ingredients_test,
        sf_labels_train,
        sf_labels_test,
    ) = train_test_split(sf_ingredients, sf_labels, test_size=args.split)

    ingredients_train = nyt_ingredients_train + sf_ingredients_train
    labels_train = nyt_labels_train + sf_labels_train
    ingredients_test = nyt_ingredients_test + sf_ingredients_test
    labels_test = nyt_labels_test + sf_labels_test

    X_train, y_train = transform_to_dataset(ingredients_train, labels_train)
    X_test, y_test = transform_to_dataset(ingredients_test, labels_test)

    model = CRF()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(metrics.flat_accuracy_score(y_test, y_pred))

    stats = evaluate(X_test, y_pred, y_test)
    print("Sentence-level results:")
    print(f"\tTotal: {stats.total_sentences}")
    print(f"\tCorrect: {stats.correct_sentences}")
    print(f"\t-> {100*stats.correct_sentences/stats.total_sentences:.2f}%")

    print()
    print("Word-level results:")
    print(f"\tTotal: {stats.total_words}")
    print(f"\tCorrect: {stats.correct_words}")
    print(f"\t-> {100*stats.correct_words/stats.total_words:.2f}%")

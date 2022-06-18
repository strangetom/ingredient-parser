#!/usr/bin/env python3

import argparse
import csv
import pickle
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
) -> tuple[List[List[Dict[str, str]]], List[List[str]]]:
    """Transform dataset into feature lists for each sentence

    Parameters
    ----------
    sentences : List[str]
        Sentences to transform
    labels : List[Dict[str, str]]
        Labels for tokens in each sentence

    Returns
    -------
    List[List[Dict[str, str]]]
        List of sentences transformed into features. Each sentence returns a list of dicts, with the dicts containing the features.
     List[str]
        List of labels transformed into QTY, UNIT, NAME, COMMENT, PUNCT or OTHER for each token
    """
    X, y = [], []

    for sentence, label in zip(sentences, labels):
        p = PreProcessor(sentence)
        X.append(p.sentence_features())
        y.append(
            [
                match_label(p.tokenized_sentence[index], label)
                for index in range(len(p.tokenized_sentence))
            ]
        )

    return X, y


def evaluate(
    X: List[List[Dict[str, str]]], predictions: List[List[str]], truths: List[List[str]]
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
            if token in [",", "(", ")"]:
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
    parser.add_argument("--nyt", help="Path to input csv file for NYTimes data")
    parser.add_argument("--sf", help="Path to input csv file for StrangerFoods data")
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
        default=30000,
        type=int,
        help="Number of entries from NYTimes dataset to use (train+test)",
    )
    parser.add_argument(
        "-m",
        "--save-model",
        default="../models/model.pickle",
        help="Path to save model to",
    )
    args = parser.parse_args()

    print("[INFO] Loading training data.")
    SF_ingredients, SF_labels = load_csv(args.sf)
    NYT_ingredients, NYT_labels = load_csv(args.nyt)

    (
        NYT_ingredients_train,
        NYT_ingredients_test,
        NYT_labels_train,
        NYT_labels_test,
    ) = train_test_split(
        NYT_ingredients[: args.number],
        NYT_labels[: args.number],
        test_size=args.split,
    )
    (
        SF_ingredients_train,
        SF_ingredients_test,
        SF_labels_train,
        SF_labels_test,
    ) = train_test_split(SF_ingredients, SF_labels, test_size=args.split)

    ingredients_train = NYT_ingredients_train + SF_ingredients_train
    labels_train = NYT_labels_train + SF_labels_train
    ingredients_test = NYT_ingredients_test + SF_ingredients_test
    labels_test = NYT_labels_test + SF_labels_test
    print(f"[INFO] {len(ingredients_train)} training vectors.")
    print(f"[INFO] {len(ingredients_test)} testing vectors.")

    X_train, y_train = transform_to_dataset(ingredients_train, labels_train)
    X_test, y_test = transform_to_dataset(ingredients_test, labels_test)

    print("[INFO] Training model with training data.")
    model = CRF()
    model.fit(X_train, y_train)

    print("[INFO] Evaluating model with test data.")
    y_pred = model.predict(X_test)

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

    # Save model
    with open(args.save_model, 'wb') as f:
        pickle.dump(model, f)

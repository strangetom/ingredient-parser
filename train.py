#!/usr/bin/env python3

import argparse
import csv
from dataclasses import dataclass
from typing import Dict, List

import pycrfsuite
from sklearn.model_selection import train_test_split

from ingredient_parser import PreProcessor
from test_results_to_html import test_results_to_html


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


def match_labels(tokenized_sentence: List[str], labels: Dict[str, str]) -> List[str]:
    """Match a label to each token in the tokenized sentence
    Possible labels are: QTY, UNIT, NAME, COMMENT, OTHER, COMMA

    This is made more complicated than it could because the labels for the training data are provided as string, which are a subset of the input sentnece.
    This means we have to try to match each token to one of the label strings.
    The main problems with this are:
        A token could appear multiple times and have different labels for each instance
        A token might not be in any of the label strings

    This function assumes that the first time we come across a particular token in a tokenized sentence, it's get the first associated label.
    Commas are treated specially with the label COMMA because they can legitimately appear anywhere in the sentence and often don't appear in the labelled strings
    Post processing will assign commas to one of the other labels based on it's location in the sentence.

    Parameters
    ----------
    tokenized_sentence : List[str]
        Tokenized ingredient sentence
    labels : Dict[str, str]
        Labels for sentence as a dict. The dict keys are the labels, the dict values are the strings that match each label

    Returns
    -------
    List[str]
        List of labels for each token.
    """

    token_labels = invert_labels_dict(labels)

    matched_labels = []
    for token in tokenized_sentence:

        # Make lower case first, because all labels are lower case
        token = token.lower()
        token = singlarise_unit(token)

        # Treat commas as special because they can appear all over the place in a sentence
        if token == ",":
            matched_labels.append("COMMA")

        # Check if the token is in the token_labels dict, or if we've already used all the assigned labels
        elif token in token_labels.keys() and token_labels[token] != []:
            # Assign the first label in the list to the current token
            # We then remove this from the list, so repeated tokens get the next label
            matched_labels.append(token_labels[token][0])
            del token_labels[token][0]

        else:
            # If the token is not anywhere in the labels, assign OTHER
            matched_labels.append("OTHER")

    return matched_labels


def invert_labels_dict(labels: Dict[str, str]) -> Dict[str, List[str]]:
    """Reverse the labels dictionary. Instead of having the labels as the key, tokenize the values and have each token as a key.
    If a token appears multiple times, the it has a list of labels

    Parameters
    ----------
    labels : Dict[str, str]
        Labels for an ingredient sentence as a dict, with labels as keys and sentences as values.

    Returns
    -------
    Dict[str, List[str]]
        Labels for an ingredient sentence as a dict, with tokens as keys and labels as values.
        The values are a list of labels, to account for a particular appearing multiple times in a ingredient sentence, possibly with different labels
    """
    labels_map = {
        "name": "NAME",
        "unit": "UNIT",
        "quantity": "QTY",
        "comment": "COMMENT",
    }

    token_dict = {}
    for label, sent in labels.items():
        # Map label to preferred label
        label = labels_map[label]

        tokenized_sent = PreProcessor(sent, defer_pos_tagging=True).tokenized_sentence
        for token in tokenized_sent:
            if token in token_dict.keys():
                token_dict[token].append(label)
            else:
                token_dict[token] = [label]

    return token_dict


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
        y.append(match_labels(p.tokenized_sentence, label))

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
        description="Train a CRF model to parse structured data from recipe ingredient sentences"
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
        default="ingredient_parser/model.crfsuite",
        help="Path to save model to",
    )
    parser.add_argument(
        "-d",
        "--detailed_results",
        action="store_true",
        help="Output a markdown file containing detailed results.",
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
    print(f"[INFO] {len(ingredients_train)+len(ingredients_test):,} total vectors")
    print(f"[INFO] {len(ingredients_train):,} training vectors.")
    print(f"[INFO] {len(ingredients_test):,} testing vectors.")

    print(f"[INFO] Transforming vectors")
    X_train, y_train = transform_to_dataset(ingredients_train, labels_train)
    X_test, y_test = transform_to_dataset(ingredients_test, labels_test)

    print("[INFO] Training model with training data.")
    trainer = pycrfsuite.Trainer(verbose=False)
    for X, y in zip(X_train, y_train):
        trainer.append(X, y)
    trainer.train(args.save_model)

    print("[INFO] Evaluating model with test data.")
    tagger = pycrfsuite.Tagger()
    tagger.open(args.save_model)
    y_pred = [tagger.tag(X) for X in X_test]

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

    if args.detailed_results:
        test_results_to_html(ingredients_test, y_test, y_pred)

#!/usr/bin/env python3

import argparse
import csv
import re

from fractions import Fraction
from typing import Dict, List

from nltk.tokenize import RegexpTokenizer
from nltk import pos_tag
from sklearn.model_selection import train_test_split
from sklearn_crfsuite import CRF, metrics

# Regex pattern for fraction parts.
# Matches 1+ numbers followed by 1+ whitespace charaters followed by a number then a forward slash then another number
FRACTION_PARTS_PATTERN = re.compile(r"(\d*\s*\d/\d)")

# Predefine tokenizer
# The regex pattern matches the tokens: any word character, including '.', or ( or ) or ,
REGEXP_TOKENIZER = RegexpTokenizer("[\w\.]+|\(|\)|,", gaps=False)


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


def replace_fractions(string: str) -> str:
    """Attempt to parse fractions from sentence and convert to decimal

    Parameters
    ----------
    string : str
        Ingredient sentence

    Returns
    -------
    str
        Ingredient sentence with fractions replaced with decimals
    """
    matches = FRACTION_PARTS_PATTERN.match(string)
    if matches is None:
        return string

    for match in matches.groups():
        split = match.split()
        summed = float(sum(Fraction(s) for s in split))
        rounded = round(summed, 2)
        string = string.replace(match, f"{rounded:g}")

    return string


def is_inside_parentheses(token: str, sentence: List[str]) -> bool:
    """Return True is token is inside parentheses within the sentence or is a parenthesis

    Parameters
    ----------
    token : str
        Token to check

    Returns
    -------
    bool
        True is token is inside parantheses or is parenthesis
    """
    # If token not sentence return False
    # This protects the final return from returning True is there are brackets but no token in the sentence
    if token not in sentence:
        return False

    # If it's "(" or ")", return True
    if token in ["(", ")"]:
        return True

    token_index = sentence.index(token)
    return (
        "(" in sentence[:token_index] and ")" in sentence[:token_index+1:]
    )


def follows_comma(token: str, sentence: List[str]) -> bool:
    """Return True if token follows a comma (by any amount) in sentence

    Parameters
    ----------
    token : str
        Token to check
    sentence : List[str]
        Sentence, split into tokens

    Returns
    -------
    bool
        True if token follows comma, else False
    """
    try:
        comma_index = sentence.index(",")
        token_index = sentence.index(token)
        if comma_index < token_index:
            return True
        else:
            return False
    except ValueError:
        return False


def is_numeric(token: str) -> bool:
    """Return True if token is numeric

    Parameters
    ----------
    token : str
        Token to check

    Returns
    -------
    bool
        True if token is numeric, else False
    """
    try:
        float(token)
        return True
    except ValueError:
        return False


def features(sentence, index):
    """sentence: [w1, w2, ...], index: the index of the word"""
    token = sentence[index]
    return {
        "word": token,
        "prev_word": "" if index == 0 else sentence[index - 1],
        "next_word": "" if index == len(sentence) - 1 else sentence[index + 1],
        "is_in_parens": is_inside_parentheses(token, sentence),
        "follows_comma": follows_comma(token, sentence),
        "is_first": index == 0,
        "is_capitalised": token[0] == token[0].upper(),
        "is_numeric": is_numeric(token),
        "pos_tag": pos_tag([token])[0][-1],
    }


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
        tokenized_sentence = REGEXP_TOKENIZER.tokenize(replace_fractions(sentence))
        X.append([features(tokenized_sentence, index) for index in range(len(tokenized_sentence))])
        y.append([match_label(tokenized_sentence[index], labels) for index in range(len(tokenized_sentence))])

    return X, y


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
    args = parser.parse_args()

    ingredients, labels = load_csv(args.input)
    ingredients_train, ingredients_test, labels_train, labels_test = train_test_split(
        ingredients, labels, test_size=args.split
    )

    X_train, y_train = transform_to_dataset(ingredients_train, labels_train)
    X_test, y_test = transform_to_dataset(ingredients_test, labels_test)

    model = CRF()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(metrics.flat_accuracy_score(y_test, y_pred))

#!/usr/bin/env python3

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingredient_parser import PreProcessor


@dataclass
class DataVectors:
    """Dataclass to store the loaded and transformed inputs"""

    sentences: list[str]
    features: list[list[dict[str, str]]]
    labels: list[list[str]]
    source: list[str]


def load_csv(
    csv_filename: str, max_rows: int
) -> tuple[list[str], list[dict[str, str]]]:
    """Load csv file generated py ```generate_training_testing_csv.py``` and parse
    contents into ingredients and labels lists

    Parameters
    ----------
    csv_filename : str
        Name of csv file
    max_rows : int
        Maximum number of rows to read

    Returns
    -------
    tuple[list[str], list[dict[str, str]]]
        List of ingredient strings
    list[dict[str, str]]
        List of dictionaries, each dictionary the ingredient labels
    """
    labels, sentences = [], []
    with open(csv_filename, "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            sentences.append(row["input"])
            labels.append(
                {
                    "name": row["name"].strip().lower(),
                    "quantity": row["quantity"].strip().lower(),
                    "unit": row["unit"].strip().lower(),
                    "preparation": row["preparation"].strip().lower(),
                    "comment": row["comment"].strip().lower(),
                }
            )

            if i == (max_rows - 1):
                break

    filename = Path(csv_filename).name
    print(f"[INFO] Loaded {i+1} vectors from {filename}.")

    return sentences, labels


def load_datasets(datasets: list[str], number: int) -> DataVectors:
    """Load raw data from csv files and transform into format required for training.

    Parameters
    ----------
    datasets : list[str]
        List of csv files to load raw data from
    number : int
        Maximum number of inputs to load from each csv file

    Returns
    -------
    DataVectors
        Dataclass holding:
            raw input sentences,
            features extracted from sentences,
            labels for sentences
            source dataset of sentences
    """
    print("[INFO] Loading and transforming training data.")
    sentences = []
    features = []
    labels = []
    source = []

    for dataset in datasets:
        dataset_id = Path(dataset).name.split("-")[0]
        dataset_sents, dataset_labels = load_csv(dataset, number)

        # Transform from csv format to training format
        print(f"[INFO] Transforming '{dataset_id}' vectors.")
        transformed_sents, transformed_labels = transform_to_dataset(
            dataset_sents, dataset_labels
        )

        sentences.extend(dataset_sents)
        features.extend(transformed_sents)
        labels.extend(transformed_labels)
        source.extend([dataset_id] * len(dataset_sents))

    print(f"[INFO] {len(sentences):,} total vectors")
    return DataVectors(sentences, features, labels, source)


def match_labels(tokenized_sentence: list[str], labels: dict[str, str]) -> list[str]:
    """Match a label to each token in the tokenized sentence
    Possible labels are: QTY, UNIT, NAME, COMMENT, OTHER, COMMA

    This is made more complicated than it could because the labels for the training
    data are provided as string, which are a subset of the input sentnece.
    This means we have to try to match each token to one of the label strings.
    The main problems with this are:
        A token could appear multiple times and have different labels for each instance
        A token might not be in any of the label strings

    This function assumes that the first time we come across a particular token in a
    tokenized sentence, it's get the first associated label.
    Commas are treated specially with the label COMMA because they can legitimately
    appear anywhere in the sentence and often don't appear in the labelled strings
    Post processing will assign commas to one of the other labels based on it's
    location in the sentence.

    Parameters
    ----------
    tokenized_sentence : list[str]
        Tokenized ingredient sentence
    labels : dict[str, str]
        Labels for sentence as a dict. The dict keys are the labels, the dict values
        are the strings that match each label

    Returns
    -------
    list[str]
        List of labels for each token.
    """

    token_labels = invert_labels_dict(labels)

    matched_labels = []
    for token in tokenized_sentence:
        # Convert to lower case because all labels are lower case
        # (see load_csv function)
        # Note that we couldn't do this earlier without losing information required for
        # feature extraction
        token = token.lower()

        # Treat commas as special because they can appear all over the
        # place in a sentence.
        if token == ",":
            matched_labels.append("COMMA")

        # Check if the token is in the token_labels dict, or if we've already used all
        # the assigned labels
        elif token in token_labels.keys() and token_labels[token] != []:
            # Assign the first label in the list to the current token
            # We then remove this from the list, so repeated tokens get the next label
            matched_labels.append(token_labels[token][0])
            del token_labels[token][0]

        else:
            # If the token is not anywhere in the labels, assign OTHER
            matched_labels.append("OTHER")

    return matched_labels


def invert_labels_dict(labels: dict[str, str]) -> dict[str, list[str]]:
    """Reverse the labels dictionary. Instead of having the labels as the key, tokenize
    the values and have each token as a key.
    If a token appears multiple times, the it has a list of labels

    Parameters
    ----------
    labels : dict[str, str]
        Labels for an ingredient sentence as a dict, with labels as keys and sentences
        as values.

    Returns
    -------
    dict[str, list[str]]
        Labels for an ingredient sentence as a dict, with tokens as keys and labels as
        values. The values are a list of labels, to account for a particular appearing
        multiple times in a ingredient sentence, possibly with different labels.
    """
    labels_map = {
        "name": "NAME",
        "unit": "UNIT",
        "quantity": "QTY",
        "comment": "COMMENT",
        "preparation": "PREP",
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
    sentences: list[str], labels: list[dict[str, str]]
) -> tuple[list[list[dict[str, str]]], list[list[str]]]:
    """Transform dataset into feature lists for each sentence

    Parameters
    ----------
    sentences : list[str]
        Sentences to transform
    labels : list[dict[str, str]]
        Labels for tokens in each sentence

    Returns
    -------
    list[list[dict[str, str]]]
        List of sentences transformed into features. Each sentence returns a list of
        dicts, with the dicts containing the features.
    list[str]
        List of labels transformed into QTY, UNIT, NAME, COMMENT, PUNCT or OTHER for
        each token
    """
    X, y = [], []

    for sentence, label in zip(sentences, labels):
        p = PreProcessor(sentence)
        X.append(p.sentence_features())
        y.append(match_labels(p.tokenized_sentence, label))

    return X, y

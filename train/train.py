#!/usr/bin/env python3

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from itertools import chain

import pycrfsuite
from sklearn.model_selection import train_test_split
from test_results_to_html import test_results_to_html

from ingredient_parser import PreProcessor


@dataclass
class Stats:
    """Dataclass to store statistics on model performance"""

    total_sentences: int
    correct_sentences: int
    total_words: int
    correct_words: int


def load_csv(csv_filename: str) -> tuple[list[str], list[dict[str, str]]]:
    """Load csv file generated py ```generate_training_testing_csv.py``` and parse
    contents into ingredients and labels lists

    Parameters
    ----------
    csv_filename : str
        Name of csv file

    Returns
    -------
    list[str]
        List of ingredient strings
    list[dict[str, str]]
        List of dictionaries, each dictionary the ingredient labels
    """
    labels, sentences = [], []
    with open(csv_filename, "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip first row
        for row in reader:
            sentences.append(row[0])
            labels.append(
                {
                    "name": row[1].strip().lower(),
                    "quantity": row[2].strip().lower(),
                    "unit": row[3].strip().lower(),
                    "comment": row[4].strip().lower(),
                }
            )
    return sentences, labels


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
        # Convert to lower case because all labels are lower case (see load_csv function)
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


def evaluate(
    X: list[str], predictions: list[list[str]], truths: list[list[str]]
) -> Stats:
    total_sentences = 0
    correct_sentences = 0
    total_words = 0
    correct_words = 0

    for sentence, prediction, truth in zip(X, predictions, truths):
        correct_words_per_sentence = 0
        total_words_per_sentence = 0

        for token, p, t in zip(sentence, prediction, truth):
            total_words += 1
            total_words_per_sentence += 1

            # Count as match if guess matches actual
            if p == t:
                correct_words_per_sentence += 1
                correct_words += 1

        total_sentences += 1
        if correct_words_per_sentence == total_words_per_sentence:
            correct_sentences += 1

    return Stats(total_sentences, correct_sentences, total_words, correct_words)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train a CRF model to parse structured data from recipe \
                     ingredient sentences."
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
    SF_sentences, SF_labels = load_csv(args.sf)
    NYT_sentences, NYT_labels = load_csv(args.nyt)

    (
        NYT_sentences_train,
        NYT_sentences_test,
        NYT_labels_train,
        NYT_labels_test,
    ) = train_test_split(
        NYT_sentences[: args.number],
        NYT_labels[: args.number],
        test_size=args.split,
    )
    (
        SF_sentences_train,
        SF_sentences_test,
        SF_labels_train,
        SF_labels_test,
    ) = train_test_split(SF_sentences, SF_labels, test_size=args.split)

    ingredients_train = NYT_sentences_train + SF_sentences_train
    labels_train = NYT_labels_train + SF_labels_train
    ingredients_test = NYT_sentences_test + SF_sentences_test
    ingredients_test_source = ["NYT"] * len(NYT_sentences_test) + ["SF"] * len(
        SF_sentences_test
    )
    labels_test = NYT_labels_test + SF_labels_test
    print(f"[INFO] {len(ingredients_train)+len(ingredients_test):,} total vectors")
    print(f"[INFO] {len(ingredients_train):,} training vectors.")
    print(f"[INFO] {len(ingredients_test):,} testing vectors.")

    print("[INFO] Transforming vectors")
    X_train, y_train = transform_to_dataset(ingredients_train, labels_train)
    X_test, y_test = transform_to_dataset(ingredients_test, labels_test)

    print("[INFO] Training model with training data.")
    trainer = pycrfsuite.Trainer(verbose=False)
    trainer.set_params(
        {
            "feature.possible_states": True,
            "feature.possible_transitions": True,
        }
    )
    for X, y in zip(X_train, y_train):
        trainer.append(X, y)
    trainer.train(args.save_model)

    print("[INFO] Evaluating model with test data.")
    tagger = pycrfsuite.Tagger()
    tagger.open(args.save_model)
    y_pred = [tagger.tag(X) for X in X_test]

    stats = evaluate(ingredients_test, y_pred, y_test)
    print("Sentence-level results:")
    print(f"\tTotal: {stats.total_sentences}")
    print(f"\tCorrect: {stats.correct_sentences}")
    print(f"\t-> {100*stats.correct_sentences/stats.total_sentences:.2f}%")

    print()
    print("Word-level results:")
    print(f"\tTotal: {stats.total_words}")
    print(f"\tCorrect: {stats.correct_words}")
    print(f"\t-> {100*stats.correct_words/stats.total_words:.2f}%")

    # Calculate some starts about the OTHER label
    train_label_count = Counter(chain.from_iterable(y_train))
    train_other_pc = 100 * train_label_count["OTHER"] / train_label_count.total()
    test_label_count = Counter(chain.from_iterable(y_test))
    test_other_pc = 100 * test_label_count["OTHER"] / test_label_count.total()
    pred_label_count = Counter(chain.from_iterable(y_pred))
    pred_other_pc = 100 * pred_label_count["OTHER"] / pred_label_count.total()
    print()
    print("OTHER labels:")
    print(f"\tIn training data: {train_label_count['OTHER']} ({train_other_pc:.2f}%)")
    print(f"\tIn test data: {test_label_count['OTHER']} ({test_other_pc:.2f}%)")
    print(
        f"\tPredicted in test data: {pred_label_count['OTHER']} ({pred_other_pc:.2f}%)"
    )

    if args.detailed_results:
        test_results_to_html(
            ingredients_test,
            y_test,
            y_pred,
            ingredients_test_source,
            minimum_mismatches=2,
        )

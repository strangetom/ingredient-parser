#!/usr/bin/env python3

import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingredient_parser.en import PreProcessor

sqlite3.register_converter("json", json.loads)

DATABASE = "train/data/training.sqlite3"


class DBRow(TypedDict):
    id: int
    source: str
    sentence: str
    tokens: list[str]
    labels: list[str]
    foundation_foods: list[int]
    snetence_split: list[int]


def load_from_db() -> list[DBRow]:
    """Get all training sentences from the database

    Returns
    -------
    list[DBRow]
        List of database rows as dicts
    """
    rows = []
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        data = c.execute("SELECT * FROM en")

    rows = [DBRow(d) for d in data]
    conn.close()

    return rows


def validate_tokens(calculated_tokens: list[str], row: DBRow) -> bool:
    """Validate that that tokens stored in the database are the same as the tokens
    obtained from the PreProcessor.

    Parameters
    ----------
    calculated_tokens : list[str]
        Tokens calculated using PreProcessor
    row : DBRow
        Database row as dict

    Returns
    -------
    bool
        True if no error, else False.
    """
    if calculated_tokens != row["tokens"]:
        print(f"[ERROR] ID: {row['id']} [{row['source']}]")
        print("Database tokens do not match PreProcessor output.")
        print(f"\t{calculated_tokens} (calc)")
        print(f"\t{row['tokens']} (db)")
        return False

    return True


def validate_token_label_length(calculated_tokens: list[str], row: DBRow) -> bool:
    """Validate that that number of tokens and number of labels are the same.

    Parameters
    ----------
    calculated_tokens : list[str]
        Tokens calculated using PreProcessor
    row : DBRow
        Database row as dict

    Returns
    -------
    bool
        True if no error, else False.
    """
    if len(calculated_tokens) != len(row["tokens"]):
        print(f"[ERROR] ID: {row['id']} [{row['source']}]")
        print("\tNumber of tokens and labels are different.")
        return False

    return True


def validate_duplicate_sentences(rows: list[DBRow]) -> int:
    """Validate the duplicate sentences have the same labels.

    Parameters
    ----------
    rows : list[DBRow]
        List of database rows

    Returns
    -------
    int
        Number of duplicate sentences with mismatching labels
    """
    labels_dict = defaultdict(set)
    uids_dict = defaultdict(set)
    for row in rows:
        uid = row["id"]
        sentence = row["sentence"]
        labels = "|".join(row["labels"])

        labels_dict[sentence].add(labels)
        uids_dict[sentence].add(uid)

    errors = 0
    for sentence, labels in labels_dict.items():
        if len(labels) > 1:
            uids = uids_dict[sentence]
            unpacked_labels = [labs.split("|") for labs in labels]

            print(f"[ERROR] ID: {','.join([str(uid) for uid in uids])}")
            print("\tDuplicate sentences have different labels")
            print(f"\t{unpacked_labels}")

            errors += 1

    return errors


def validate_BIO_labels(row: DBRow) -> bool:
    """Validate BIO labels are valid

    Parameters
    ----------
    row : DBRow
        Database row as dict

    Returns
    -------
    bool
        True if no error, else False.
    """
    prev_name_label = ""
    for label in row["labels"]:
        if not (label.startswith("B_") or label.startswith("I_")):
            continue

        label_type = label.split("_", 1)[-1]
        if label.startswith("I_"):
            # Check I label is preceded by same B or I label of same type.
            if not (prev_name_label == label or prev_name_label == "B_" + label_type):
                print(f"[ERROR] ID: {row['id']} [{row['source']}]")
                print("\tError in BIO labels")
                return False

        prev_name_label = label

    return True


if __name__ == "__main__":
    rows = load_from_db()

    token_errors = 0
    token_label_errors = 0
    bio_errors = 0

    for row in rows:
        p = PreProcessor(row["sentence"])
        if not validate_tokens([t.text for t in p.tokenized_sentence], row):
            token_errors += 1
        if not validate_token_label_length([t.text for t in p.tokenized_sentence], row):
            token_label_errors += 1
        if not validate_BIO_labels(row):
            bio_errors += 1

    duplicate_sentence_errors = validate_duplicate_sentences(rows)

    if token_errors > 0:
        print(f"{token_errors} token errors")

    if token_label_errors > 0:
        print(f"{token_label_errors} token-label length mismatch errors")

    if duplicate_sentence_errors > 0:
        print(f"{duplicate_sentence_errors} duplicate sentences with mismatched labels")

    if bio_errors > 0:
        print(f"{bio_errors} errors in BIO labels")

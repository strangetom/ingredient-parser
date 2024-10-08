#!/usr/bin/env python3

import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingredient_parser.en import PreProcessor

sqlite3.register_converter("json", json.loads)

DATABASE = "train/data/training.sqlite3"


def load_from_db() -> list[dict[str, str | list[str]]]:
    """Get all training sentences from the database

    Returns
    -------
    list[dict[str, str]]
        List of database rows as dicts
    """
    rows = []
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        data = c.execute("SELECT * FROM en")

    rows = [dict(d) for d in data]
    conn.close()

    return rows


def validate_tokens(calculated_tokens: list[str], stored_tokens: list[str]) -> bool:
    """Validate that that tokens stored in the database are the same as the tokens
    obtained from the PreProcessor.

    Parameters
    ----------
    calculated_tokens : list[str]
        Tokens calculated using PreProcessor
    stored_tokens : list[str]
        Token stored in database

    Returns
    -------
    bool
        True if no error, else False.
    """
    if calculated_tokens != stored_tokens:
        print(f"[ERROR] ID: {row['id']} [{row['source']}]")
        print("Database tokens do not match PreProcessor output.")
        print(f"\t{calculated_tokens} (calc)")
        print(f"\t{stored_tokens} (db)")
        return False

    return True


def validate_token_label_length(
    calculated_tokens: list[str], stored_labels: list[str]
) -> bool:
    """Validate that that number of tokens and number of labels are the same.

    Parameters
    ----------
    calculated_tokens : list[str]
        Tokens calculated using PreProcessor
    stored_labels : list[str]
        Labels stored in database

    Returns
    -------
    bool
        True if no error, else False.
    """
    if len(calculated_tokens) != len(stored_labels):
        print(f"[ERROR] ID: {row['id']} [{row['source']}]")
        print("\tNumber of tokens and labels are different.")
        return False

    return True


def validate_duplicate_sentences(rows: list[dict]) -> int:
    """Validate the duplicate sentences have the same labels.

    Parameters
    ----------
    rows : list[dict]
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


if __name__ == "__main__":
    rows = load_from_db()

    token_errors = 0
    token_label_errors = 0

    for row in rows:
        p = PreProcessor(row["sentence"], defer_pos_tagging=True)
        if not validate_tokens(p.tokenized_sentence, row["tokens"]):
            token_errors += 1
        if not validate_token_label_length(p.tokenized_sentence, row["labels"]):
            token_label_errors += 1

    duplicate_sentence_errors = validate_duplicate_sentences(rows)

    if token_errors > 0:
        print(f"{token_errors} token errors")

    if token_label_errors > 0:
        print(f"{token_label_errors} token-label length mismatch errors")

    if duplicate_sentence_errors > 0:
        print(f"{duplicate_sentence_errors} duplicate sentences with mismatched labels")

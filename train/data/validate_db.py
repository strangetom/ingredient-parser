#!/usr/bin/env python3

import json
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingredient_parser.en import PreProcessor

sqlite3.register_converter("json", json.loads)

DATABASE = "train/data/training.sqlite3"


@dataclass
class DBRow:
    id: int
    source: str
    sentence: str
    tokens: list[str]
    labels: list[str]
    sentence_split: list[int]
    fdc_mapping: int


def load_from_db() -> list[DBRow]:
    """Get all training sentences from the database

    Returns
    -------
    list[DBRow]
        List of database rows.
    """
    rows = []
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        data = c.execute("SELECT * FROM en")

    rows = [DBRow(**d) for d in data]
    conn.close()

    return rows


def validate_tokens(calculated_tokens: list[str], row: DBRow) -> bool:
    """Validate that that tokens stored in the database are the same as the tokens
    obtained from the PreProcessor.

    Parameters
    ----------
    calculated_tokens : list[str]
        Tokens calculated using PreProcessor.
    row : DBRow
        Database row.

    Returns
    -------
    bool
        True if no error, else False.
    """
    if calculated_tokens != row.tokens:
        print(f"[ERROR] ID: {row.id} [{row.source}]")
        print("Database tokens do not match PreProcessor output.")
        print(f"\t{calculated_tokens} (calc)")
        print(f"\t{row.tokens} (db)")
        return False

    return True


def validate_token_label_length(calculated_tokens: list[str], row: DBRow) -> bool:
    """Validate that that number of tokens and number of labels are the same.

    Parameters
    ----------
    calculated_tokens : list[str]
        Tokens calculated using PreProcessor.
    row : DBRow
        Database row.

    Returns
    -------
    bool
        True if no error, else False.
    """
    if len(calculated_tokens) != len(row.tokens):
        print(f"[ERROR] ID: {row.id} [{row.source}]")
        print("\tNumber of tokens and labels are different.")
        return False

    return True


def validate_duplicate_sentences(rows: list[DBRow]) -> int:
    """Validate the duplicate sentences have the same labels.

    Parameters
    ----------
    rows : list[DBRow]
        List of database rows.

    Returns
    -------
    int
        Number of duplicate sentences with mismatching labels.
    """
    labels_dict = defaultdict(set)
    uids_dict = defaultdict(set)
    for row in rows:
        uid = row.id
        sentence = row.sentence
        labels = "|".join(row.labels)

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


def validate_name_labels(row: DBRow) -> bool:
    """Validate name labels are valid.

    Name labels

    Parameters
    ----------
    row : DBRow
        Database row.

    Returns
    -------
    bool
        True if no error, else False.
    """
    I_NAME_TOK_valid = validate_I_NAME_TOK(row)
    NAME_VAR_valid = validiate_NAME_VAR(row)
    NAME_MOD_valid = validiate_NAME_MOD(row)

    return I_NAME_TOK_valid and NAME_VAR_valid and NAME_MOD_valid


def validate_I_NAME_TOK(row: DBRow) -> bool:
    """Validate that I_NAME_TOK always appears after a B_NAME_TOK.

    I_NAME_TOK does not have to be adjacent to B_NAME_TOK.

    If the sentence contains NAME_SEP, check there is a B_NAME_TOK after the NAME_SEP
    before any I_NAME_TOK.

    Parameters
    ----------
    row : DBRow
        Database row.

    Returns
    -------
    bool
        True if valid, else False.
    """
    if "I_NAME_TOK" not in row.labels:
        return True

    for i, label in enumerate(row.labels):
        if label != "I_NAME_TOK":
            continue

        if "NAME_SEP" in row.labels[:i]:
            # If NAME_SEP prior to current I_NAME_TOK, check there is a B_NAME_TOK after
            # NAME_SEP and before current label.
            name_sep_idx = max(
                i for i, v in enumerate(row.labels[:i]) if v == "NAME_SEP"
            )
            if "B_NAME_TOK" not in row.labels[name_sep_idx:i]:
                print(f"[ERROR] ID: {row.id} [{row.source}]")
                print("\tError in NAME labels: I_NAME_TOK")
                return False
        else:
            if "B_NAME_TOK" not in row.labels[:i]:
                print(f"[ERROR] ID: {row.id} [{row.source}]")
                print("\tError in NAME labels: I_NAME_TOK")
                return False

    return True


def validiate_NAME_VAR(row: DBRow) -> bool:
    """Validate if the sentence contains NAME_VAR, there is more than one.

    Parameters
    ----------
    row : DBRow
        Database row.

    Returns
    -------
    bool
        True if valid, else False.
    """
    if "NAME_VAR" not in row.labels:
        return True

    name_var_count = sum(1 for label in row.labels if label == "NAME_VAR")
    if name_var_count == 1:
        print(f"[ERROR] ID: {row.id} [{row.source}]")
        print("\tError in NAME labels: NAME_VAR")
        return False

    return True


def validiate_NAME_MOD(row: DBRow) -> bool:
    """Validate if the sentence contains NAME_MOD, there are at least 2 B_NAME_TOK or
    at least 2 NAME_VAR after the NAME_MOD.

    Parameters
    ----------
    row : DBRow
        Database row.

    Returns
    -------
    bool
        True if valid, else False.
    """
    if "NAME_MOD" not in row.labels:
        return True

    name_mod_idx = max(i for i, v in enumerate(row.labels) if v == "NAME_MOD")

    name_var_count = sum(
        1 for label in row.labels[name_mod_idx:] if label == "NAME_VAR"
    )
    b_name_tok_count = sum(
        1 for label in row.labels[name_mod_idx:] if label == "B_NAME_TOK"
    )
    if not (name_var_count > 1 or b_name_tok_count > 1):
        print(f"[ERROR] ID: {row.id} [{row.source}]")
        print("\tError in NAME labels: NAME_MOD")
        return False

    return True


if __name__ == "__main__":
    rows = load_from_db()

    token_errors = 0
    token_label_errors = 0
    name_errors = 0

    for row in rows:
        p = PreProcessor(row.sentence, {})
        if not validate_tokens([t.text for t in p.tokenized_sentence], row):
            token_errors += 1
        if not validate_token_label_length([t.text for t in p.tokenized_sentence], row):
            token_label_errors += 1
        if not validate_name_labels(row):
            name_errors += 1

    duplicate_sentence_errors = validate_duplicate_sentences(rows)

    if token_errors > 0:
        print(f"{token_errors} token errors")

    if token_label_errors > 0:
        print(f"{token_label_errors} token-label length mismatch errors")

    if duplicate_sentence_errors > 0:
        print(f"{duplicate_sentence_errors} duplicate sentences with mismatched labels")

    if name_errors > 0:
        print(f"{name_errors} errors in name labels")

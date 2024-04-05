#!/usr/bin/env python3

import json
import sqlite3
import sys
from pathlib import Path

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingredient_parser import PreProcessor

sqlite3.register_converter("json", json.loads)

DATABASE = "train/data/training.sqlite3"


def load_from_db() -> list[dict[str, str]]:
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


def validate_tokens(calculated_tokens: list[str], stored_tokens: list[str]) -> None:
    """Validate that that tokens stored in the database are the same as the tokens
    obtained from the PreProcessor.

    Parameters
    ----------
    calculated_tokens : list[str]
        Tokens calculated using PreProcessor
    stored_tokens : list[str]
        Token stored in database
    """
    if calculated_tokens != stored_tokens:
        print(
            f"""[ERROR] ID:{row['id']} [{row['source']}] 
            Database tokens do not match PreProcessor output."""
        )


def validate_token_label_length(
    calculated_tokens: list[str], stored_labels: list[str]
) -> None:
    """Validate that that number of tokens and number of labels are the same.

    Parameters
    ----------
    calculated_tokens : list[str]
        Tokens calculated using PreProcessor
    stored_labels : list[str]
        Labels stored in database
    """
    if len(calculated_tokens) != len(stored_labels):
        print(f"""[ERROR] ID:{row['id']} [{row['source']}] 
            Number of tokens and labels are different.""")


if __name__ == "__main__":
    rows = load_from_db()
    for row in rows:
        p = PreProcessor(row["sentence"], defer_pos_tagging=True)
        validate_tokens(p.tokenized_sentence, row["tokens"])
        validate_token_label_length(p.tokenized_sentence, row["labels"])

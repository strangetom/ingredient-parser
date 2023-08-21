#!/usr/bin/env python3

import csv
from pathlib import Path


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
                    "comment": row["comment"].strip().lower(),
                }
            )

            if i == (max_rows - 1):
                break

    filename = Path(csv_filename).name
    print(f"[INFO] Loaded {i+1} vectors from {filename}.")

    return sentences, labels

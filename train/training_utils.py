#!/usr/bin/env python3

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingredient_parser import PreProcessor

sqlite3.register_converter("json", json.loads)


@dataclass
class DataVectors:
    """Dataclass to store the loaded and transformed inputs"""

    sentences: list[str]
    features: list[list[dict[str, str]]]
    tokens: list[list[str]]
    labels: list[list[str]]
    source: list[str]


def load_datasets(
    database: str, datasets: list[str], discard_other: bool = True
) -> DataVectors:
    """Load raw data from csv files and transform into format required for training.

    Parameters
    ----------
    database : str
        Path to database of training data
    datasets : list[str]
        List of data source to include.
        Valid options are: nyt, cookstr, bbc
    discard_other : bool, optional
        If True, discard sentences containing tokens with OTHER label

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

    with sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            f"SELECT * FROM training WHERE source IN ({','.join(['?']*len(datasets))})",
            datasets,
        )
        data = c.fetchall()
    conn.close()

    source, sentences, features, tokens, labels = [], [], [], [], []
    discarded = 0
    for entry in data:
        if discard_other and "OTHER" in entry["labels"]:
            discarded += 1
            continue

        source.append(entry["source"])
        sentences.append(entry["sentence"])
        p = PreProcessor(entry["sentence"])
        features.append(p.sentence_features())
        labels.append(entry["labels"])
        tokens.append(entry["tokens"])

    print(f"[INFO] {len(sentences):,} usable vectors")
    print(f"[INFO] {discarded:,} discarded due to OTHER labels")
    return DataVectors(sentences, features, tokens, labels, source)

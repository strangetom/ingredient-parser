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
    labels: list[list[str]]
    source: list[str]


def load_datasets(database: str) -> DataVectors:
    """Load raw data from csv files and transform into format required for training.

    Parameters
    ----------
    database : str
        Path to database of training data

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
        c.execute("SELECT * FROM training")
        data = c.fetchall()
    conn.close()

    source = [entry["source"] for entry in data]
    sentences = [entry["sentence"] for entry in data]
    features = extract_features(sentences)
    labels = [entry["labels"] for entry in data]

    print(f"[INFO] {len(sentences):,} total vectors")
    return DataVectors(sentences, features, labels, source)


def extract_features(sentences: list[str]) -> list[list[dict[str, str]]]:
    """Transform dataset into feature lists for each sentence

    Parameters
    ----------
    sentences : list[str]
        Sentences to transform

    Returns
    -------
    list[list[dict[str, str]]]
        List of sentences transformed into features. Each sentence returns a list of
        dicts, with the dicts containing the features.
    """
    X = []

    for sentence in sentences:
        p = PreProcessor(sentence)
        X.append(p.sentence_features())

    return X

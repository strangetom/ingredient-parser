#!/usr/bin/env python3

import json
import sqlite3
import sys
from dataclasses import dataclass
from itertools import chain
from pathlib import Path

from sklearn.metrics import classification_report

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


@dataclass
class Metrics:
    """Metrics returned by sklearn.metrics.classification_report for each label"""

    precision: float
    recall: float
    f1_score: float
    support: int


@dataclass
class TokenStats:
    """Statistics for token classification performance"""

    NAME: Metrics
    QTY: Metrics
    UNIT: Metrics
    SIZE: Metrics
    COMMENT: Metrics
    PREP: Metrics
    PUNC: Metrics
    macro_avg: Metrics
    weighted_avg: Metrics
    accuracy: float


@dataclass
class SentenceStats:
    """Statistics for sentence classification performance"""

    accuracy: float


@dataclass
class Stats:
    """Statistics for token and sentence classification performance"""

    token: TokenStats
    sentence: SentenceStats


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
            f"SELECT * FROM en WHERE source IN ({','.join(['?']*len(datasets))})",
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

    print(f"[INFO] {len(sentences):,} usable vectors.")
    print(f"[INFO] {discarded:,} discarded due to OTHER labels.")
    return DataVectors(sentences, features, tokens, labels, source)


def evaluate(predictions: list[list[str]], truths: list[list[str]]) -> Stats:
    """Calculate statistics on the predicted labels for the test data.

    Parameters
    ----------
    predictions : list[list[str]]
        Predicted labels for each test sentence
    truths : list[list[str]]
        True labels for each test sentence

    Returns
    -------
    Stats
        Dataclass holding token and sentence statistics:
    """
    # Generate token statistics
    # Flatten prediction and truth lists
    flat_predictions = list(chain.from_iterable(predictions))
    flat_truths = list(chain.from_iterable(truths))
    labels = list(set(flat_predictions))

    report = classification_report(
        flat_truths,
        flat_predictions,
        labels=labels,
        output_dict=True,
    )

    # Convert report to TokenStats dataclass
    token_stats = {}
    for k, v in report.items():
        # Convert dict to Metrics
        if k in labels + ["macro avg", "weighted avg"]:
            k = k.replace(" ", "_")
            token_stats[k] = Metrics(
                v["precision"], v["recall"], v["f1-score"], int(v["support"])
            )
        else:
            token_stats[k] = v

    token_stats = TokenStats(**token_stats)

    # Generate sentence statistics
    # The only statistics that makes sense here is accuracy because there are only
    # true-positive results (i.e. correct) and false-negative results (i.e. incorrect)
    correct_sentences = len([p for p, t in zip(predictions, truths) if p == t])
    sentence_stats = SentenceStats(correct_sentences / len(predictions))

    return Stats(token_stats, sentence_stats)

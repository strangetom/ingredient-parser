#!/usr/bin/env python3

import json
import logging
import sqlite3
from contextlib import closing
from dataclasses import dataclass

logger = logging.getLogger(__name__)

sqlite3.register_converter("json", json.loads)

DEFAULT_MODEL_LOCATION = "ingredient_parser/en/data/pos_tagger.en.json.gz"


@dataclass
class DataVectors:
    """Dataclass to store the loaded and transformed inputs."""

    sentences: list[str]
    tokens: list[list[str]]
    tags: list[list[str]]
    uids: list[int]


def load_datasets(
    database: str,
    table: str,
) -> DataVectors:
    """Load raw data from csv files and transform into format required for training.

    Parameters
    ----------
    database : str
        Path to database of training data.
    table : str
        Name of database table containing training data.

    Returns
    -------
    DataVectors
        Dataclass holding:
            raw input sentences,
            features extracted from sentences,
            labels for sentences
            source dataset of sentences
    """

    logger.info("Loading training data.")

    # contextlib.closing automatically calls conn.close() on exiting the context.
    with closing(
        sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
    ) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(f"SELECT id, sentence, tokens, tags FROM {table}")
        data = [dict(row) for row in c.fetchall()]

    all_vectors = DataVectors(
        sentences=[row["sentence"] for row in data],
        tokens=[row["tokens"] for row in data],
        tags=[row["tags"] for row in data],
        uids=[row["id"] for row in data],
    )

    logger.info("%d usable vectors.", len(all_vectors.sentences))
    return all_vectors

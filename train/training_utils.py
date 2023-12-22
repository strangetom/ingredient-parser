#!/usr/bin/env python3

import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingredient_parser import PreProcessor


@dataclass
class DataVectors:
    """Dataclass to store the loaded and transformed inputs"""

    sentences: list[str]
    features: list[list[dict[str, str]]]
    labels: list[list[str]]
    source: list[str]


def load_json(json_filename: str, max_rows: int) -> list[dict]:
    """Load json file containing training data

    Parameters
    ----------
    json_filename : str
        Name of JSON file
    max_rows : int
        Maximum number of rows to read

    Returns
    -------
    list[dict]
        List of dicts. Each dict contains the sentence, tokens and labels for each token.
    """
    with open(json_filename, "r") as f:
        data = json.load(f)

    if len(data) > max_rows:
        data = data[:max_rows]

    filename = Path(json_filename).name
    print(f"[INFO] Loaded {len(data)} vectors from {filename}.")

    return data


def load_datasets(datasets: list[str], number: int) -> DataVectors:
    """Load raw data from csv files and transform into format required for training.

    Parameters
    ----------
    datasets : list[str]
        List of csv files to load raw data from
    number : int
        Maximum number of inputs to load from each csv file

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
    sentences = []
    features = []
    labels = []
    source = []

    for dataset in datasets:
        dataset_id = Path(dataset).name.split("-")[0]
        dataset_dicts = load_json(dataset, number)
        sents = [d["sentence"] for d in dataset_dicts]

        # Transform from csv format to training format
        print(f"[INFO] Transforming '{dataset_id}' vectors.")
        sentence_features = extract_features(sents)

        sentences.extend(sents)
        features.extend(sentence_features)
        labels.extend([d["labels"] for d in dataset_dicts])
        source.extend([dataset_id] * len(sents))

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

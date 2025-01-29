#!/usr/bin/env python3

import argparse
import json
import os
import sqlite3
import tempfile

import fasttext

from ingredient_parser.en import PreProcessor

from .training_utils import DEFAULT_MODEL_LOCATION

sqlite3.register_converter("json", json.loads)


def prepare_training_data(
    database: str,
    table: str,
    datasets: list[str],
) -> str:
    """Prepare training data for training embeddings.

    Sentences from the selected datasets in the training database are tokenized. Each
    token is made lowercase and then written to a temporary file, one sentence per line.
    The tokens are spaced separated in the temporary file.

    Parameters
    ----------
    database : str
        Path to database of training data
    table : str
        Name of database table containing training data
    datasets : list[str]
        List of data source to include.
        Valid options are: nyt, cookstr, bbc, cookstr, tc
    """
    print("[INFO] Loading and preparing training data.")

    bindings = ",".join(["?"] * len(datasets))
    with sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT sentence FROM {table} WHERE source IN ({bindings})",
            datasets,
        )
        sentences = [sent for (sent,) in c.fetchall()]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for sent in sentences:
            tokens = PreProcessor(sent).tokenized_sentence
            f.write(" ".join(t.feat_text.lower() for t in tokens))
            f.write("\n")

    return f.name


def train_embeddings(args: argparse.Namespace) -> None:
    """Train fasttext embeddings model on recipe ingredient sentences.

    Parameters
    ----------
    args : argparse.Namespace
        Model training configuration
    """
    training_file = prepare_training_data(args.database, args.table, args.datasets)

    print("[INFO] Training embeddings model.")
    model = fasttext.train_unsupervised(
        training_file,
        model="skipgram",  #  model type, skipgram or cbow
        minn=2,  #  smallest subtoken n-grams to generate
        maxn=5,  #  largest subtoken n-grams to generate
        minCount=2,  # only include tokens that occur at least this many times
        dim=30,  # model dimensions
        epoch=50,  # training epochs
        lr=0.05,  # learning rate, between 0 and 1
    )

    if args.save_model is None:
        save_model = DEFAULT_MODEL_LOCATION["embeddings"]
    else:
        save_model = args.save_model
    model.save_model(save_model)

    os.remove(training_file)

    print(f"[INFO] Embeddings model saved to {save_model}.")

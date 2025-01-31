#!/usr/bin/env python3

import argparse
import csv
import os
import tempfile

import floret
from tqdm import tqdm

from ingredient_parser.en import PreProcessor

from .training_utils import DEFAULT_MODEL_LOCATION


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

    csvs = [
        "train/data/allrecipes/allrecipes-ingredients-snapshot-2017.csv",
        "train/data/bbc/bbc-ingredients-snapshot-2017.csv",
        "train/data/cookstr/cookstr-ingredients-snapshot-2017.csv",
        "train/data/nytimes/nyt-ingredients-snapshot-2015.csv",
        "train/data/tastecooking/tastecooking-ingredients-snapshot-2024.csv",
    ]

    sentences = []
    for file in csvs:
        with open(file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sentences.append(row["input"])

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for sent in tqdm(sentences):
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
    model = floret.train_unsupervised(
        training_file,
        mode="floret",  #  more size/memory efficient
        model="skipgram",  #  model type, skipgram or cbow
        minn=2,  #  smallest subtoken n-grams to generate
        maxn=5,  #  largest subtoken n-grams to generate
        minCount=1,  # only include tokens that occur at least this many times
        dim=10,  # model dimensions
        epoch=50,  # training epochs
        lr=0.1,  # learning rate, between 0 and 1
        wordNgrams=2,  # length of word n-grams
        bucket=50000,
        hashCount=2,
    )

    if args.save_model is None:
        save_model = DEFAULT_MODEL_LOCATION["embeddings"]
    else:
        save_model = args.save_model
    model.save_model(save_model)

    os.remove(training_file)

    print(f"[INFO] Embeddings model saved to {save_model}.")

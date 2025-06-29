#!/usr/bin/env python3

import csv
import gzip
import logging
from functools import lru_cache
from importlib.resources import as_file, files

import pycrfsuite

from ._embeddings import GloVeModel

logger = logging.getLogger("ingredient-parser")


@lru_cache
def load_parser_model() -> pycrfsuite.Tagger:  # type: ignore
    """Load parser model.

    This function is cached so that when the model has been loaded once, it does not
    need to be loaded again, the cached model is returned.

    Returns
    -------
    pycrfsuite.Tagger
        Parser model loaded into Tagger object.
    """
    logger.debug("Loading parser model: model.en.crfsuite")
    tagger = pycrfsuite.Tagger()  # type: ignore
    with as_file(files(__package__) / "data/model.en.crfsuite") as p:
        tagger.open(str(p))
        return tagger


@lru_cache
def load_embeddings_model() -> GloVeModel:  # type: ignore
    """Load embeddings model.

    This function is cached so that when the model has been loaded once, it does not
    need to be loaded again, the cached model is returned.

    Returns
    -------
    GloVeModel
        Embeddings model.
    """
    logger.debug("Loading embeddings model: ingredient_embeddings.25d.glove.txt.gz")
    return GloVeModel("data/ingredient_embeddings.25d.glove.txt.gz")


@lru_cache
def load_embeddings_bigrams() -> set[tuple[str, str]]:
    """Load embeddings bigrams from csv file..

    The bigrams are stored in pairs in a csv file.

    Returns
    -------
    set[tuple[str, str]]
        Set of bigram tuples.
    """
    logger.debug("Loading embeddings bigrams: bigrams.csv.gz")
    bigrams = set()
    with as_file(files(__package__) / "data/bigrams.csv.gz") as p:
        with gzip.open(p, "rt") as f:
            reader = csv.reader(f)
            for row in reader:
                bigrams.add(tuple(row))

    return bigrams

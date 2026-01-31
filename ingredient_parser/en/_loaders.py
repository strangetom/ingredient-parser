#!/usr/bin/env python3

import gzip
import json
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
    logger.debug("Loading parser model: 'model.en.crfsuite'")
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
    logger.debug("Loading embeddings model: 'ingredient_embeddings.35d.glove.txt.gz'.")
    return GloVeModel("data/ingredient_embeddings.35d.glove.txt.gz")


@lru_cache
def load_ingredient_tagdict() -> dict[str, str]:
    """Cached function for loading ingredient token part of speech tagdict.

    The entries in this dict are used to bypass the part of speech tagging model so the
    token is always given the tag in this dict.

    Returns
    -------
    dict[str, str]
        Dict of token:tag pairs
    """
    logger.debug("Loading ingredient POS tagdict: 'ingredient_tagdict.json.gz'.")
    with as_file(files(__package__) / "data/ingredient_tagdict.json.gz") as p:
        with gzip.open(p, "rt") as f:
            tagdict = json.load(f)

    return tagdict

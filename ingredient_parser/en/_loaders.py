#!/usr/bin/env python3

from functools import lru_cache
from importlib.resources import as_file, files

import pycrfsuite

from ._embeddings import GloVeModel


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
    tagger = pycrfsuite.Tagger()  # type: ignore
    with as_file(files(__package__) / "model.en.crfsuite") as p:
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
    return GloVeModel("ingredient_embeddings.25d.glove.txt.gz")

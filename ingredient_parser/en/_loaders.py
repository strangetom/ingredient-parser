#!/usr/bin/env python3

import logging
from functools import lru_cache
from importlib.resources import as_file, files

from ..inference import NumpyCRFInference
from ..perceptron import PerceptronTagger
from ._embeddings import GloVeModel

logger = logging.getLogger("ingredient-parser")


@lru_cache
def load_parser_model() -> NumpyCRFInference:
    """Load parser model.

    This function is cached so that when the model has been loaded once, it does not
    need to be loaded again, the cached model is returned.

    Returns
    -------
    NumpyCRFInference
        Parser model loaded into Tagger object.
    """
    logger.debug("Loading parser model: 'model.en.json.gz'")
    with as_file(files(__package__) / "data/model.en.json.gz") as p:
        tagger = NumpyCRFInference(p)
        return tagger


@lru_cache
def load_pos_tagger_model() -> PerceptronTagger:
    """Load part of speech tagger model.

    This function is cached so that when the model has been loaded once, it does not
    need to be loaded again, the cached model is returned.

    Returns
    -------
    PerceptronTagger
        Part of speech model loaded into PerceptronTagger object.
    """
    logger.debug("Loading part of speech tagger model: 'pos_tagger.en.json.gz'")
    with as_file(files(__package__) / "data/pos_tagger.en.json.gz") as p:
        tagger = PerceptronTagger(p)
        return tagger


@lru_cache
def load_embeddings_model() -> GloVeModel:
    """Load embeddings model.

    This function is cached so that when the model has been loaded once, it does not
    need to be loaded again, the cached model is returned.

    Returns
    -------
    GloVeModel
        Embeddings model.
    """
    logger.debug("Loading embeddings model: 'ingredient_embeddings.35d.glove.txt.gz'.")
    with as_file(
        files(__package__) / "data/ingredient_embeddings.35d.glove.txt.gz"
    ) as p:
        return GloVeModel(str(p))

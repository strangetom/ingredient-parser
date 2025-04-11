#!/usr/bin/env python3

from functools import lru_cache
from importlib.resources import as_file, files

import floret
import pycrfsuite


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
def load_embeddings_model() -> floret.floret._floret:  # type: ignore
    """Load embeddings model.

    This function is cached so that when the model has been loaded once, it does not
    need to be loaded again, the cached model is returned.

    Returns
    -------
    floret.floret._floret
        Embeddigns model.
    """
    with as_file(files(__package__) / "ingredient_embeddings.25d.floret.bin") as p:
        return floret.load_model(str(p))

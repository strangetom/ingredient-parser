#!/usr/bin/env python3

import csv
import gzip
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import as_file, files

import floret
import pycrfsuite
from nltk import pos_tag

from ._utils import prepare_embeddings_tokens, tokenize


@dataclass
class FDCIngredient:
    """Dataclass for details of an ingredient from the FoodDataCentral database."""

    fdc_id: int
    data_type: str
    description: str
    category: str
    tokens: tuple[str, ...]
    pos_tags: tuple[str, ...]


@lru_cache
def load_foundation_foods_data() -> list[FDCIngredient]:
    """Load foundation foods CSV.

    This function is cached so that when the data has been loaded once, it does not
    need to be loaded again, the cached data is returned.

    Returns
    -------
    list[FDCIngredient]
        List of FDCIngredient objects.
    """
    ingredients = []
    with as_file(files(__package__) / "fdc_ingredients.csv.gz") as p:
        with gzip.open(p, "rt") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tokens = tuple(tokenize(row["description"]))
                pos_tags = tuple(pos for _, pos in pos_tag(tokens))

                tokens_in_vocab = [
                    (token, pos)
                    for token, pos in prepare_embeddings_tokens(tokens, pos_tags)
                ]

                tokens, pos_tags = zip(*tokens_in_vocab)
                ingredients.append(
                    FDCIngredient(
                        fdc_id=int(row["fdc_id"]),
                        data_type=row["data_type"],
                        description=row["description"],
                        category=row["category"],
                        tokens=tuple(tokens),
                        pos_tags=tuple(pos_tags),
                    )
                )

    return ingredients


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
    with as_file(files(__package__) / "ingredient_embeddings.5d.floret.bin") as p:
        return floret.load_model(str(p))

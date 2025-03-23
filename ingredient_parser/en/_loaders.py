#!/usr/bin/env python3

import csv
import gzip
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import as_file, files

import floret
import pycrfsuite
from nltk import pos_tag

from ._utils import tokenize


@dataclass
class FDCIngredient:
    """Dataclass for details of an ingredient from the FoodDataCentral database."""

    fdc_id: int
    data_type: str
    description: str
    category: str
    common_name: str
    tokens: list[str]
    pos_tags: list[str]


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
                tokens = tokenize(row["description"])
                pos_tags = [pos for _, pos in pos_tag(tokens)]
                ingredients.append(
                    FDCIngredient(
                        fdc_id=int(row["fdc_id"]),
                        data_type=row["data_type"],
                        description=row["description"],
                        category=row["category"],
                        common_name=row["common_name"],
                        tokens=tokens,
                        pos_tags=pos_tags,
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
    with as_file(files(__package__) / "embeddings.floret.bin") as p:
        return floret.load_model(str(p))

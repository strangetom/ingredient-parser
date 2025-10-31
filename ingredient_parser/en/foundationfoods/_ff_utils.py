#!/usr/bin/env python3

import csv
import gzip
import logging
from functools import lru_cache
from importlib.resources import as_file, files

from ..._common import consume
from .._utils import prepare_embeddings_tokens, tokenize
from ._ff_dataclasses import FDCIngredient

logger = logging.getLogger("ingredient-parser.foundation-foods")

# Phrase and token substitutions to normalise spelling of ingredient name tokens to the
# spellings used in the FDC ingredient descriptions.
# All tokens in these dicts are stemmed and lower case.
FDC_PHRASE_SUBSTITUTIONS: dict[tuple[str, ...], list[str]] = {
    ("doubl", "cream"): ["heavi", "cream"],
    ("glac", "cherri"): ["maraschino", "cherri"],
    ("ice", "sugar"): ["powder", "sugar"],
    ("mang", "tout"): ["snow", "pea"],
    ("plain", "flour"): ["all", "purpos", "flour"],
    ("singl", "cream"): ["light", "cream"],
    ("haa", "avocado"): ["hass", "avocado"],
}
FDC_TOKEN_SUBSTITUTIONS: dict[str, str] = {
    "aubergin": "eggplant",
    "beetroot": "beet",
    "capsicum": "bell",
    "chile": "chili",
    "chilli": "chili",
    "coriand": "cilantro",
    "cornflour": "cornstarch",
    "courgett": "zucchini",
    "gherkin": "pickl",
    "mangetout": "snowpea",
    "prawn": "shrimp",
    "rocket": "arugula",
    "swede": "rutabaga",
    "yoghurt": "yogurt",
}
FDC_TOKEN_TO_PHRASE_SUBSTITUTIONS: dict[str, list[str]] = {
    "lemongrass": ["lemon", "grass"],
    "low-sodium": ["low", "sodium"],
}


def normalise_spelling(tokens: list[str]) -> list[str]:
    """Normalise spelling in `tokens` to standard spellings used in FDC ingredient
    descriptions.

    This also include subtitution of certain ingredients to use the FDC version e.g.
    courgette -> zucchini; coriander -> cilantro.

    Parameters
    ----------
    tokens : list[str]
        List of stemmed tokens.

    Returns
    -------
    list[str]
        List of tokens with spelling normalised.
    """
    itokens = iter(tokens)

    normalised_tokens = []
    for i, token in enumerate(itokens):
        token = token.lower()
        if i < len(tokens) - 1:
            next_token = tokens[i + 1].lower()
        else:
            next_token = ""

        if (token, next_token) in FDC_PHRASE_SUBSTITUTIONS:
            normalised_tokens.extend(FDC_PHRASE_SUBSTITUTIONS[(token, next_token)])
            # Jump forward to avoid processing next_token again.
            consume(itokens, 1)
        elif token in FDC_TOKEN_TO_PHRASE_SUBSTITUTIONS:
            normalised_tokens.extend(FDC_TOKEN_TO_PHRASE_SUBSTITUTIONS[token])
        elif token in FDC_TOKEN_SUBSTITUTIONS:
            normalised_tokens.append(FDC_TOKEN_SUBSTITUTIONS[token])
        else:
            normalised_tokens.append(token)

    if normalised_tokens != tokens:
        logger.debug(f"Normalised tokens: {normalised_tokens}.")

    return normalised_tokens


@lru_cache
def load_fdc_ingredients() -> list[FDCIngredient]:
    """Cached function for loading FDC ingredients from CSV.

    Returns
    -------
    list[FDCIngredient]
        List of FDC ingredients.
    """
    foundation_foods = []
    with as_file(files(__package__).joinpath("..", "data/fdc_ingredients.csv.gz")) as p:
        with gzip.open(p, "rt") as f:
            logger.debug("Loading FDC ingredients: 'fdc_ingredients.csv.gz'.")
            reader = csv.DictReader(f)
            for row in reader:
                tokens = tuple(tokenize(row["description"]))
                prepared_tokens = prepare_embeddings_tokens(tokens)
                if not prepared_tokens:
                    logger.debug(
                        f"'{row['description']}' has no tokens in embedding vocabulary."
                    )
                    continue
                foundation_foods.append(
                    FDCIngredient(
                        fdc_id=int(row["fdc_id"]),
                        data_type=row["data_type"],
                        description=row["description"],
                        category=row["category"],
                        tokens=prepared_tokens,
                    )
                )

    logger.debug(f"Loaded {len(foundation_foods)} FDC ingredients.")
    return foundation_foods

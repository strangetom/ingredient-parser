#!/usr/bin/env python3

import csv
import gzip
import logging
import string
from functools import lru_cache
from importlib.resources import as_file, files
from itertools import groupby

from ..._common import consume
from .._constants import STOP_WORDS
from .._loaders import load_embeddings_model
from .._utils import stem, tokenize
from ._ff_constants import NEGATION_TOKENS
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
    "long-grain": ["long", "grain"],
    "medium-grain": ["medium", "grain"],
    "short-grain": ["short", "grain"],
    "bone-in": ["bone", "in"],
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


@lru_cache(maxsize=512)
def prepare_embeddings_tokens(tokens: tuple[str, ...]) -> list[str]:
    """Prepare tokens for use with embeddings model.

    This involves obtaning the stem for the token and discarding tokens which are
    numeric, which are punctuation, or which are in STOP_WORDS.

    Parameters
    ----------
    tokens : tuple[str, ...]
        Tuple of tokens.

    Returns
    -------
    list[str]
        Prepared tokens.
    """
    # Split tokens on hyphens
    split_tokens = []
    for token in tokens:
        if "-" in token:
            split_tokens.extend([t for t in token.split("-") if t])
        else:
            split_tokens.append(token)

    stemmed_tokens = [
        stem(token.lower())
        for token in split_tokens
        if not token.isnumeric()
        and not token.isdigit()
        and not token.isdecimal()
        and not token.isspace()
        and token not in string.punctuation
        and token not in STOP_WORDS
        and len(token) > 1
    ]

    normalised_tokens = normalise_spelling(stemmed_tokens)

    embeddings = load_embeddings_model()
    return [token for token in normalised_tokens if token in embeddings]


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
                tokens, negated_tokens = tokenize_with_negation(row["description"])
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
                        negated_tokens=negated_tokens,
                    )
                )

    logger.debug(f"Loaded {len(foundation_foods)} FDC ingredients.")
    return foundation_foods


def tokenize_with_negation(description: str) -> tuple[tuple[str, ...], set[str]]:
    """Tokenize description, return tokens and negated tokens.
    Negated tokens are tokens that occur in a phrase after a token such as "no", "not",
    "without". Phrases are determined by splitting the description on commas.
    Parameters
    ----------
    description : str
        FDC description to tokenize.
    Returns
    -------
    tuple[tuple[str, ...], set[str]]
        tuple of description tokens.
        set of negated tokens.
    """
    tokens = tokenize(description)
    negated_tokens = set()
    for _, phrase in groupby(tokens, lambda x: x != ","):
        phrase = list(phrase)
        for neg in NEGATION_TOKENS:
            if neg in phrase:
                neg_idx = phrase.index(neg)
                # Include negation token negated_tokens set since it won't hold any
                # further relevant semantic information.
                negated_tokens |= set(phrase[neg_idx:])

    tokens = tuple(token for token in tokens if token not in negated_tokens)
    return tokens, negated_tokens

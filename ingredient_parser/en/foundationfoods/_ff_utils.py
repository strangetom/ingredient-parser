#!/usr/bin/env python3

import csv
import gzip
import logging
import string
from functools import lru_cache
from importlib.resources import as_file, files
from itertools import groupby

from ..._common import consume
from .._loaders import load_embeddings_model
from .._utils import stem, tokenize
from ._ff_constants import (
    AMBIGUOUS_ADJECTIVES,
    NEGATION_TOKENS,
    REDUCED_RELEVANCE_TOKENS,
)
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
    "mint": "spearmint",
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
    "water": ["tap", "water"],
}


def normalise_spelling(tokens: list[str]) -> list[str]:
    """Normalise spelling in `tokens` to standard spellings used in FDC ingredient
    descriptions.

    This also include substitution of certain ingredients to use the FDC version e.g.
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
        logger.debug(f"Normalised '{tokens}' to '{normalised_tokens}'.")

    return normalised_tokens


@lru_cache(maxsize=512)
def prepare_embeddings_tokens(tokens: tuple[str, ...]) -> list[str]:
    """Prepare tokens for use with embeddings model.

    This involves obtaining the stem for the token and discarding tokens which are
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
    logger = logging.getLogger("ingredient-parser.fdc")

    foundation_foods = []
    with as_file(files(__package__).joinpath("..", "data/fdc_ingredients.csv.gz")) as p:
        with gzip.open(p, "rt") as f:
            logger.debug("Loading FDC ingredients: 'fdc_ingredients.csv.gz'.")
            reader = csv.DictReader(f)
            for row in reader:
                tokens_weights = tokenize_fdc_description(row["description"])
                if not tokens_weights:
                    logger.debug(
                        f"'{row['description']}' has no tokens in embedding vocabulary."
                    )
                    continue
                tokens, weights = zip(*tokens_weights)
                foundation_foods.append(
                    FDCIngredient(
                        fdc_id=int(row["fdc_id"]),
                        data_type=row["data_type"],
                        description=row["description"],
                        category=row["category"],
                        tokens=list(tokens),
                        weights=list(weights),
                    )
                )

    logger.debug(f"Loaded {len(foundation_foods)} FDC ingredients.")
    return foundation_foods


def tokenize_fdc_description(description: str) -> list[tuple[str, float]]:
    """Tokenize FDC ingredient description, returning tokens and weight for each token.

    Tokens that are not compatible with the embeddings are discarded.

    Weights are calculated using a 1e-3 subtraction based on the number of phrases in
    the description. Each phrase is determined by the position of commas and later
    phrases have lower weights. For example

    Oil, olive, extra light
    1   1-1e-3 1-2e-3 1-2e-3

    Negated tokens are given a weight of 0. These are tokens that occur in a phrase
    after a token such as "no", "not", "without".

    Tokens with reduced relevant have their weight reduced by 0.5. These are tokens that
    occur in a phrase after a token such as "with", indicating that they are not the
    main ingredient the description is referring to.

    Parameters
    ----------
    description : str
        FDC description to tokenize.

    Returns
    -------
    list[tuple[str, float]]
        List of (token, weight) tuples.
    """
    embeddings = load_embeddings_model()
    tokens = tokenize(description.lower())

    weights = []
    prepared_tokens = []
    phrase_count = 0
    for is_phrase, phrase in groupby(tokens, lambda x: x != ","):
        if not is_phrase:
            # If not phrase (i.e. is the comma), set weight to 0 if token is in vocab.
            # These tokens will be discarded later anyway.
            for token in phrase:
                if token in embeddings:
                    prepared_tokens.append(phrase)
                    weights.append(0.0)
            continue

        phrase = list(prepare_embeddings_tokens(tuple(phrase)))
        phrase_weights = [1.0 - phrase_count * 1e-3] * len(phrase)

        # Check for negated tokens and set weight to 0.
        for neg in NEGATION_TOKENS:
            if neg in phrase:
                # Include negation token negated_tokens set since it won't hold any
                # further relevant semantic information.
                for neg_idx in range(phrase.index(neg), len(phrase)):
                    phrase_weights[neg_idx] = 0

        # Check for tokens that indicate reduced relevance and reduce their weight
        for rr in REDUCED_RELEVANCE_TOKENS:
            if rr in phrase:
                for rr_idx in range(phrase.index(rr), len(phrase)):
                    phrase_weights[rr_idx] = max(phrase_weights[rr_idx] - 0.5, 0)

        prepared_tokens.extend(phrase)
        weights.extend(phrase_weights)
        phrase_count += 1

    return list(zip(prepared_tokens, weights))


def strip_ambiguous_leading_adjectives(
    tokens: list[str], pos_tags: list[str]
) -> list[str]:
    """Strip ambiguous leading adjectives from list of tokens.

    Ambiguous adjectives are adjectives like "hot" which could refer to temperature or
    spiciness. In this example, when referring to temperature the matchers will confuse
    it with the spiciness meaning and return incorrect matches.

    If all tokens are ambiguous adjectives, return original list rather than return
    an empty list.

    Parameters
    ----------
    tokens : list[str]
        List of tokens.
    pos_tags : list[str]
        List of POS tags for tokens.

    Returns
    -------
    list[str]
        List of tokens.

    Examples
    --------
    >>> strip_ambiguous_leading_adjectives(
        ["hot", "chicken", "stock"], ["JJ", "NN", "NN"]
    )
    ["chicken", "stock"]
    """
    original_tokens = tokens
    while pos_tags[0].startswith("J") and tokens[0] in AMBIGUOUS_ADJECTIVES:
        tokens = tokens[1:]
        pos_tags = pos_tags[1:]

        if not tokens:
            break

    if not tokens:
        return original_tokens

    return tokens

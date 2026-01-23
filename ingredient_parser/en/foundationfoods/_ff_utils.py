#!/usr/bin/env python3

import csv
import gzip
import logging
import string
from dataclasses import dataclass
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
from ._ff_dataclasses import FDCIngredient, IngredientToken

logger = logging.getLogger("ingredient-parser.foundation-foods")


@dataclass
class TokenizedFDCDescription:
    tokens: list[str]
    embedding_tokens: list[str]
    embedding_weights: list[float]


# Phrase and token substitutions to normalise spelling of ingredient name tokens to the
# spellings used in the FDC ingredient descriptions.
# All tokens in these dicts are stemmed and lower case.
FDC_PHRASE_SUBSTITUTIONS: dict[tuple[str, ...], list[str]] = {
    # Prevent "cilantro" replacing "coriander" in the context of "coriander seeds".
    ("coriand", "seed"): ["coriand", "seed"],
    ("doubl", "cream"): ["heavi", "cream"],
    ("garlic", "granul"): ["garlic", "powder"],
    ("onion", "granul"): ["onion", "powder"],
    ("glac", "cherri"): ["maraschino", "cherri"],
    ("ice", "sugar"): ["powder", "sugar"],
    ("mang", "tout"): ["snow", "pea"],
    ("plain", "flour"): ["all", "purpos", "flour"],
    ("singl", "cream"): ["light", "cream"],
    ("haa", "avocado"): ["hass", "avocado"],
    ("broad", "bean"): ["fava", "bean"],
    ("self", "rais"): ["self", "rise"],
    ("appl", "sauc"): ["applesauc"],
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
    "filo": "phyllo",
    "gherkin": "pickl",
    "mangetout": "snowpea",
    "mint": "spearmint",
    "prawn": "shrimp",
    "puré": "pure",
    "rocket": "arugula",
    "swede": "rutabaga",
    "yoghurt": "yogurt",
    "demerara": "turbinado",  # i.e. sugar
    "gruyèr": "gruyer",  # Gruyère cheese
}
FDC_TOKEN_TO_PHRASE_SUBSTITUTIONS: dict[str, list[str]] = {
    "lemongrass": ["lemon", "grass"],
    "low-sodium": ["low", "sodium"],
    "long-grain": ["long", "grain"],
    "medium-grain": ["medium", "grain"],
    "short-grain": ["short", "grain"],
    "bone-in": ["bone", "in"],
    "water": ["tap", "water"],
    "beansprout": ["bean", "sprout"],
    "breadcrumb": ["bread", "crumb"],
}

# Types of pasta that should be normalised to "pasta, dry". The names are stemmed.
# Note that spaghetti is excluded because it can also refer to a type of squash.
PASTA_TYPES = [
    "bucatini",
    "conchigli",  # conchiglie
    "ditalini",
    "farfall"  # farfalle
    "fettuccin",  # fettuccine
    "fusilli",
    "gemelli",
    "lasagn",  # lasagne
    "linguin",  # linguine
    "macaroni",
    "orecchiett",  # orecchiette
    "orzo",
    "paccheri",
    "pappardell",  # pappardelle
    "penn",  # penne
    "rigatoni",
    "rotini",
    "stellin",  # stelline
    "tagliatell",  # tagliatelle
]
for type_ in PASTA_TYPES:
    FDC_TOKEN_TO_PHRASE_SUBSTITUTIONS[type_] = ["pasta", "dri"]


def normalise_spelling(tokens: list[IngredientToken]) -> list[IngredientToken]:
    """Normalise spelling in `tokens` to standard spellings used in FDC ingredient
    descriptions.

    This also include substitution of certain ingredients to use the FDC version e.g.
    courgette -> zucchini; coriander -> cilantro.

    Parameters
    ----------
    tokens : list[IngredientToken]
        List of stemmed tokens.

    Returns
    -------
    list[IngredientToken]
        List of tokens with spelling normalised.
    """
    itokens = iter(tokens)

    normalised_tokens = []
    for i, ing_token in enumerate(itokens):
        token = ing_token.token.lower()
        if i < len(tokens) - 1:
            next_token = tokens[i + 1].token.lower()
        else:
            next_token = ""

        if (token, next_token) in FDC_PHRASE_SUBSTITUTIONS:
            normalised_tokens.extend(
                [
                    IngredientToken(t, ing_token.pos_tag)
                    for t in FDC_PHRASE_SUBSTITUTIONS[(token, next_token)]
                ]
            )
            # Jump forward to avoid processing next_token again.
            consume(itokens, 1)
        elif token in FDC_TOKEN_TO_PHRASE_SUBSTITUTIONS:
            normalised_tokens.extend(
                [
                    IngredientToken(t, ing_token.pos_tag)
                    for t in FDC_TOKEN_TO_PHRASE_SUBSTITUTIONS[token]
                ]
            )
        elif token in FDC_TOKEN_SUBSTITUTIONS:
            normalised_tokens.append(
                IngredientToken(FDC_TOKEN_SUBSTITUTIONS[token], ing_token.pos_tag)
            )
        else:
            normalised_tokens.append(ing_token)

    if normalised_tokens != tokens:
        norm_tokens = [t.token for t in normalised_tokens]
        logger.debug(f"Normalised '{[t.token for t in tokens]}' to '{norm_tokens}'.")

    return normalised_tokens


@lru_cache(maxsize=512)
def prepare_tokens(tokens: tuple[IngredientToken, ...]) -> list[IngredientToken]:
    """Prepare tokens for use with embeddings model.

    This involves obtaining the stem for the token and discarding tokens which are
    numeric, which are punctuation, or which are in STOP_WORDS.

    Parameters
    ----------
    tokens : tuple[IngredientToken, ...]
        Tuple of tokens.

    Returns
    -------
    list[IngredientToken]
        Prepared tokens.
    """
    # Split tokens on hyphens
    split_tokens = []
    for ing_token in tokens:
        if "-" in ing_token.token:
            token_parts = [t for t in ing_token.token.split("-") if t]
            split_tokens.extend(
                [IngredientToken(p, ing_token.pos_tag) for p in token_parts]
            )
        else:
            split_tokens.append(ing_token)

    stemmed_tokens = [
        IngredientToken(stem(ing_token.token.lower()), ing_token.pos_tag)
        for ing_token in split_tokens
        if not ing_token.token.isnumeric()
        and not ing_token.token.isdigit()
        and not ing_token.token.isdecimal()
        and not ing_token.token.isspace()
        and ing_token.token not in string.punctuation
        and len(ing_token.token) > 1
    ]

    return normalise_spelling(stemmed_tokens)


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
                tokenized_description = tokenize_fdc_description(row["description"])
                if not tokenized_description.embedding_tokens:
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
                        tokens=tokenized_description.tokens,
                        embedding_tokens=tokenized_description.embedding_tokens,
                        embedding_weights=tokenized_description.embedding_weights,
                    )
                )

    logger.debug(f"Loaded {len(foundation_foods)} FDC ingredients.")
    return foundation_foods


def tokenize_fdc_description(description: str) -> TokenizedFDCDescription:
    """Tokenize FDC ingredient description, returning tokens and weight for each token.

    Tokens that are not compatible with the embeddings are discarded.

    Weights are calculated using a 1e-3 subtraction based on the number of phrases in
    the description. Each phrase is determined by the position of commas and later
    phrases have lower weights. For example

    Oil,   olive,    extra   light
    1     1-(1e-3) 1-(2e-3) 1-(2e-3)

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
    TokenizedFDCDescription
    """
    embeddings = load_embeddings_model()
    tokens = tokenize(description.lower())
    prepared_tokens = prepare_tokens(tuple(IngredientToken(t, "") for t in tokens))

    embedding_weights = []
    prepared_embedding_tokens = []
    phrase_count = 0
    for is_phrase, phrase in groupby(tokens, lambda x: x != ","):
        if not is_phrase:
            # If not phrase (i.e. is the comma), set weight to 0 if token is in vocab.
            # These tokens will be discarded later anyway.
            for token in phrase:
                if token in embeddings:
                    prepared_embedding_tokens.append(phrase)
                    embedding_weights.append(0.0)
            continue

        phrase = [
            tok.token
            for tok in prepare_tokens(tuple(IngredientToken(t, "") for t in phrase))
            if tok.token in embeddings
        ]
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

        prepared_embedding_tokens.extend(phrase)
        embedding_weights.extend(phrase_weights)
        phrase_count += 1

    return TokenizedFDCDescription(
        tokens=[t.token for t in prepared_tokens],
        embedding_tokens=prepared_embedding_tokens,
        embedding_weights=embedding_weights,
    )


def strip_ambiguous_leading_adjectives(
    tokens: list[IngredientToken],
) -> list[IngredientToken]:
    """Strip ambiguous leading adjectives from list of tokens.

    Ambiguous adjectives are adjectives like "hot" which could refer to temperature or
    spiciness. In this example, when referring to temperature the matchers will confuse
    it with the spiciness meaning and return incorrect matches.

    If all tokens are ambiguous adjectives, return original list rather than return
    an empty list.

    Parameters
    ----------
    tokens : list[IngredientToken]
        List of tokens.

    Returns
    -------
    list[IngredientToken]
        List of tokens.

    Examples
    --------
    >>> strip_ambiguous_leading_adjectives(
        ["hot", "chicken", "stock"], ["JJ", "NN", "NN"]
    )
    ["chicken", "stock"]
    """
    original_tokens = tokens
    while tokens[0].pos_tag.startswith("J") and tokens[0].token in AMBIGUOUS_ADJECTIVES:
        tokens = tokens[1:]

        if not tokens:
            break

    if not tokens:
        return original_tokens

    return tokens

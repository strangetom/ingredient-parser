#!/usr/bin/env python3

import copy
import csv
import gzip
import re
import string
from collections import namedtuple
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import as_file, files
from itertools import chain

from nltk.metrics.distance import edit_distance

from ..dataclasses import FoundationFood

# NamedTuple for holding the resultant score of the match between an ingredient name and
# an FDC ingredient. A NamedTuple is used here instead of a dataclass to enable `sorted`
# to consider each part of the score in the correct order.
MatchScore = namedtuple(
    "MatchScore", ["full_match", "partial_match", "data_type", "fraction_match"]
)


@dataclass
class FDCIngredient:
    """Dataclass for details of an ingredient from the FoodDataCentral database."""

    fdc_id: int
    data_type: str
    description: str
    category: str
    description_tokens: set[str]


# Order in which the FoodDataCentral data sources are preferred.
# The higher number indicates higher preference.
PREFERRED_DATA_SOURCES = {
    "foundation_food": 2,
    "survey_fndds_food": 1,
}

WHITESPACE_TOKENISER = re.compile(r"\S+")
PUNCTUATION_TOKENISER = re.compile(rf"([{string.punctuation}])")


def tokenize_fdc_description(description: str) -> set[str]:
    """Tokenize FDC ingredient description into individual words, ignoring all
    punctuation.

    This function is similar to the tokeniser for ingredient sentences, but we return a
    Set of strings and discard punctuation.

    Parameters
    ----------
    description : str
        FDC ingredient description

    Returns
    -------
    set[str]
        Set of tokens

    Examples
    --------
    >>> tokenize_fdc_description("Pepper, bell, red, raw")
    {"pepper", "bell", "red", raw"}
    """
    tokens = [
        PUNCTUATION_TOKENISER.split(tok)
        for tok in WHITESPACE_TOKENISER.findall(description)
    ]
    return {
        tok.lower()
        for tok in chain.from_iterable(tokens)
        if tok not in string.punctuation
    }


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
        with gzip.open(str(p), "rt") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tokens = tokenize_fdc_description(row["description"])
                ingredients.append(
                    FDCIngredient(
                        fdc_id=int(row["fdc_id"]),
                        data_type=row["data_type"],
                        description=row["description"],
                        category=row["category"],
                        description_tokens=tokens,
                    )
                )

    return ingredients


def score_fdc_ingredient(
    ingredient_name: set[tuple[str, str]], fdc_ingredient: FDCIngredient
) -> MatchScore:
    """Score match between tokens of ingredient_name and FDC ingredient description.

    A hierarchical score is returned, comprised of the following in order of importance.
      1. Full matches, tokens in ingredient name that appear exactly in FDC description
      2. Partial matches, tokens in ingredient name that are have an edit distance of no
         more than 2 from a token in FDC description
      3. Preferred data source (foundation_foods > survery_fndds_foods)
      4. The fraction of tokens in FDC description that have been matched

    Parameters
    ----------
    ingredient_name : set[tuple[str, str]]
        Ingredient name (token, part of speech) pairs
    fdc_ingredient : FDCIngredient
        FDC ingredient

    Returns
    -------
    MatchScore
        MatchScore for FDC ingredient
    """
    full_matches, partial_matches = 0, 0
    consumed_ingredient_tokens = set()

    fdc_tokens = copy.deepcopy(fdc_ingredient.description_tokens)
    fdc_tokens_len = len(fdc_tokens)

    # First, calculate number of exact matches
    # If the ingredient name token is a noun, check the plural or singular version if
    # no exact match and treat this match as an exact match also.

    # Can replace this with an intersection and diff?
    for tok, _ in ingredient_name:
        if tok in fdc_tokens:
            full_matches += 1
            fdc_tokens.remove(tok)
            consumed_ingredient_tokens.add(tok)
        else:
            # check plural/singular
            ...

    # Second, calculate partial matches that have an edit (Levenstein) distance of 2 or
    # less.

    for tok, _ in ingredient_name:
        if tok in consumed_ingredient_tokens:
            continue

        # This needs to calculate the edit distance for all remaining fdc_ing tokens
        # and then select the token lowest non-zero score.
        for fdc_tok in fdc_tokens:
            distance = edit_distance(tok, fdc_tok)
            if distance <= 2:
                partial_matches += 1
                fdc_tokens.remove(fdc_tok)
                consumed_ingredient_tokens.add(tok)
                break

    return MatchScore(
        full_matches,
        partial_matches,
        PREFERRED_DATA_SOURCES[fdc_ingredient.data_type],
        (full_matches + partial_matches) / fdc_tokens_len,
    )


def match_foundation_foods(
    tokens: list[str],
    labels: list[str],
    pos: list[str],
) -> FoundationFood:
    """Extract foundation foods from tokens labelled as NAME.

    Parameters
    ----------
    tokens : list[str]
        Sentence tokens
    labels : list[str]
        Labels for sentence tokens
    pos : list[str]
        Part of speech tags for tokens

    Returns
    -------
    list[FoundationFood]
        List of foundation foods.
    """
    fdc_ingredients = load_foundation_foods_data()

    token_pos = {
        (tok, pos) for tok, pos, label in zip(tokens, pos, labels) if label != "PUNC"
    }

    scores: list[tuple[FDCIngredient, MatchScore]] = []
    for fdc_ingredient in fdc_ingredients:
        score = score_fdc_ingredient(token_pos, fdc_ingredient)
        scores.append((fdc_ingredient, score))

        if score[0] == len(fdc_ingredient.description_tokens):
            # If the first element of score (i.e. the full matches) is the same as the
            # length of FDC Ingredient description tokens, then we don't need to
            # continue because that will be a perfect match.
            break

    # Sort to find best score
    best_fdc_match, best_score = sorted(scores, key=lambda x: x[1], reverse=True)[0]
    return FoundationFood(
        text=best_fdc_match.description,
        confidence=best_score.fraction_match,
        fdc_id=best_fdc_match.fdc_id,
        category=best_fdc_match.category,
        data_type=best_fdc_match.data_type,
    )

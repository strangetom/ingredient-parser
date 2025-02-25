#!/usr/bin/env python3

import csv
import gzip
import re
import string
from collections import namedtuple
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import as_file, files
from itertools import chain

# from nltk.metrics.distance import edit_distance
from ..dataclasses import FoundationFood

# NamedTuple for holding the resultant score of the match between an ingredient name and
# an FDC ingredient. A NamedTuple is used here instead of a dataclass to enable `sorted`
# to consider each part of the score in the correct order.
MatchScore = namedtuple(
    "MatchScore",
    [
        "noun_match_fraction",
        "other_match_fraction",
        "data_type",
        "total_match_fraction",
    ],
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
        with gzip.open(p, "rt") as f:
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


# Key = singular word ending, value = characters to append to make plural
# https://github.com/weixu365/pluralizer-py/blob/master/pluralizer/pluralizer_rules.py
PLURALISATION_RULES = {
    re.compile(r"(j|s|ss|sh|ch|x|z)$", re.I): r"\1es",
    re.compile(r"(?<=[bcdfghjklmpqrstvwxyz])(o)$", re.I): r"\1es",
    re.compile(r"(?<=[bcdfghjklmpqrstvwxyz])(y)$", re.I): "ies",
    re.compile(r"(?<=qu)(y)$", re.I): "ies",
    re.compile(r"(fe?)$", re.I): "ves",
    re.compile(r"(us)$", re.I): "i",
    re.compile(r"(is)$", re.I): "es",
    re.compile(r"(ix)$", re.I): "ices",
    re.compile(r"(\'s)$", re.I): "s's",
}

SINGULARISATION_RULES = {
    re.compile(r"(j|s|ss|sh|ch|x|z)es$", re.I): r"\1",
    re.compile(r"(?<=[bcdfghjklmpqrstvwxyz])(o)es$", re.I): r"\1",
    re.compile(r"(?<=[bcdfghjklmpqrstvwxyz])(ies)$", re.I): "y",
    re.compile(r"(?<=qu)(ies)$", re.I): "y",
    # re.compile(r"(fe?)$", re.I): "ves",
    # re.compile(r"(us)$", re.I): "i",
    # re.compile(r"(is)$", re.I): "es",
    # re.compile(r"(ix)$", re.I): "ices",
    # re.compile(r"(\'s)$", re.I): "s's",
}


@lru_cache(maxsize=512)
def get_plural_singular_noun(noun: str, pos_tag: str) -> str:
    """For the given noun, if plural return the singular form and vice versa.

    Parameters
    ----------
    noun : str
        Noun to return plural or singular form of.
    pos_tag : str
        Part of speech for noun.

    Returns
    -------
    str
        If given noun is plural, return singular form.
        If given noun is singular, return plural form.

    Raises
    ------
    ValueError
        Raised if pos_tag is not for a noun.
        i.e. not one of NN, NNP, NNS, NNPS
    """
    if pos_tag not in {"NN", "NNP", "NNS", "NNPS"}:
        raise ValueError(f"Part of speech ({pos_tag}) indicates {noun} is not a noun.")

    if pos_tag.endswith("S"):
        # Plural, so make singular
        for pattern, sub in SINGULARISATION_RULES.items():
            if pattern.search(noun):
                return pattern.sub(sub, noun)

        if noun.endswith("s"):
            return noun[:-1]

        return noun
    else:
        # Singular, so make plural
        for pattern, sub in PLURALISATION_RULES.items():
            if pattern.search(noun):
                return pattern.sub(sub, noun)

        return noun + "s"


def score_fdc_ingredient(
    ingredient_name: set[tuple[str, str]], fdc_ingredient: FDCIngredient
) -> MatchScore:
    """Score match between tokens of ingredient_name and FDC ingredient description.

    A hierarchical score is returned, comprised of the following in order of importance.
    1. Fraction of noun tokens in ingredient name matching token in FDC decription.
    2. Fraction of non-noun tokens in ingredient name matching token in FDC description.
    3. Preferred data source (foundation_foods > survery_fndds_foods)
    4. The fraction of tokens in FDC description that have been matched

    The first step also considers the plural and singular form of the noun and counts a
    match for either as a match for the token.

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
    noun_matches, other_matches = 0, 0
    total_nouns = len([pos for _, pos in ingredient_name if pos.startswith("NN")])
    total_others = len([pos for _, pos in ingredient_name if not pos.startswith("NN")])

    consumed_ingredient_tokens = set()
    consumed_fdc_tokens = set()

    fdc_tokens = fdc_ingredient.description_tokens
    fdc_tokens_len = len(fdc_tokens)

    # Calculate matches
    # If the ingredient name token is a noun, check the plural or singular version if
    # no exact match and treat this match as an exact match also.
    for tok, pos in ingredient_name:
        if tok in fdc_tokens:
            if tok in consumed_fdc_tokens:
                continue

            if pos.startswith("NN"):
                noun_matches += 1
            else:
                other_matches += 1
            consumed_fdc_tokens.add(tok)
            consumed_ingredient_tokens.add(tok)
        elif pos.startswith("NN"):
            # Not an exact match, but still a noun
            ps_tok = get_plural_singular_noun(tok, pos)
            if ps_tok in fdc_tokens:
                noun_matches += 1
                consumed_fdc_tokens.add(ps_tok)
                consumed_ingredient_tokens.add(tok)

    return MatchScore(
        noun_matches / total_nouns if total_nouns > 0 else 0,
        other_matches / total_others if total_others > 0 else 0,
        PREFERRED_DATA_SOURCES[fdc_ingredient.data_type],
        (noun_matches + other_matches) / fdc_tokens_len,
    )


def match_foundation_foods(
    tokens: list[str],
    labels: list[str],
    pos: list[str],
) -> FoundationFood | None:
    """Match ingredient name to foundation foods from FDC Ingredient.

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
    FoundationFood | None
        Matching foundation food, or None if no match can be found.
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

    # If the match isn't very good, return None
    if best_score.noun_match_fraction <= 0.5 and best_score.total_match_fraction <= 0.5:
        return None

    return FoundationFood(
        text=best_fdc_match.description,
        confidence=best_score.total_match_fraction,
        fdc_id=best_fdc_match.fdc_id,
        category=best_fdc_match.category,
        data_type=best_fdc_match.data_type,
    )

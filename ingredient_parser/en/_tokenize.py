#!/usr/bin/env python3

import re
from itertools import chain

from .._common import consume, is_float

# Define regular expressions used by tokenizer.
# Matches one or more non-white-space characters
WHITESPACE_TOKENISER = re.compile(r"\S+")
# Matches and captures one of the specified punctuation marks.
PUNCTUATION_TOKENISER = re.compile(r"([\(\)\[\]\{\}\,/:;\?\!\*\~])")
# Matches and captures full stop at end of string
# (?<!\.\w) is a negative look behind that prevents matches if the last full stop
# is preceded by a a full stop then a word character.
FULL_STOP_TOKENISER = re.compile(r"(?<!\.\w)(\.)$")


def tokenize(sentence: str) -> list[str]:
    """Tokenise an ingredient sentence.

    The sentence is split on white space characters into a list of tokens.
    If any of these tokens contains of the punctuation marks captured by
    PUNCTUATION_TOKENISER, these are then split and isolated as a separate
    token.

    The returned list of tokens has any empty tokens removed.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to tokenize.

    Returns
    -------
    list[str]
        List of tokens from sentence.

    Examples
    --------
    >>> tokenize("2 cups (500 ml) milk")
    ["2", "cups", "(", "500", "ml", ")", "milk"]

    >>> tokenize("1-2 mashed bananas: as ripe as possible")
    ["1-2", "mashed", "bananas", ":", "as", "ripe", "as", "possible"]

    >>> tokenize("1.5 kg bananas, mashed")
    ["1.5", "kg", "bananas", ",", "mashed"]

    >>> tokenize("Freshly grated Parmesan cheese, for garnish.")
    ["Freshly", "grated", "Parmesan", "cheese", ",", "for", "garnish", "."]

    >>> tokenize("2 onions, finely chopped*")
    ["2", "onions", ",", "finely", "chopped", "*"]

    >>> tokenize("2 cups beef and/or chicken stock")
    ["2", "cups", "beef", "and/or", "chicken", "stock"]
    """
    tokens = [
        PUNCTUATION_TOKENISER.split(tok)
        for tok in WHITESPACE_TOKENISER.findall(sentence)
    ]
    flattened = [tok for tok in chain.from_iterable(tokens) if tok]

    # Recombine "and/or" into a single token
    combined = combine_and_or(flattened)
    # Recombine "No. 1" and similar into a single token
    combined = combine_no_number(combined)

    # Second pass to separate full stops from end of tokens
    tokens = [FULL_STOP_TOKENISER.split(tok) for tok in combined]

    return [tok for tok in chain.from_iterable(tokens) if tok]


def combine_and_or(tokens: list[str]) -> list[str]:
    """Combine ["and", "/", "or"] into a single token.

    Parameters
    ----------
    tokens : list[str]
        Flat list of tokens.

    Returns
    -------
    list[str]
        Input tokens with any instances of and/or combined into a single token.

    Examples
    --------
    >>> combine_and_or(["2", "cups", "beef", "and/or", "chicken", "stock"])
    ["2", "cups", "beef", "and/or", "chicken", "stock"]

    >>> combine_and_or(["1-2", "bananas", ":", "as", "ripe", "as", "possible"])
    ["1-2", "bananas", ":", "as", "ripe", "as", "possible"]
    """
    AND_OR_PATTERN = ["and", "/", "or"]

    combined = []
    idx = iter(range(len(tokens)))
    for i in idx:
        # Short circuit: If tokens[i] is not equal to the first element
        # of AND_OR_PATTERN, skip to next iteration
        if tokens[i] == AND_OR_PATTERN[0] and tokens[i : i + 3] == AND_OR_PATTERN:
            combined.append("and/or")
            consume(idx, len(AND_OR_PATTERN) - 1)
        else:
            combined.append(tokens[i])

    return combined


def combine_no_number(tokens: list[str]) -> list[str]:
    """Combine "No." followed by a number into a single token.

    Parameters
    ----------
    tokens : list[str]
        Flat list of tokens.

    Returns
    -------
    list[str]
        Input tokens with any instances of No. followed by number combined into a single
        token.

    Examples
    --------
    >>> combine_no_number(["1", "teaspoon", "No.", "1", "curing", "salt"])
    ['1', 'teaspoon', 'No. 1', 'curing', 'salt']
    """
    combined = []
    idx = iter(range(len(tokens)))
    for i in idx:
        if i < len(tokens) - 1 and tokens[i] == "No." and is_float(tokens[i + 1]):
            combined.append("No. " + tokens[i + 1])
            consume(idx, 1)
        else:
            combined.append(tokens[i])

    return combined

#!/usr/bin/env python3

import re

from .._common import is_float

# Define regular expressions used by tokenizer.
# Matches one or more non-white-space characters
WHITESPACE_TOKENISER = re.compile(r"\S+")
# Matches and captures one of the specified punctuation marks.
# Note that this does not include full stops.
PUNCTUATION_TOKENISER = re.compile(r"([\(\)\[\]\{\}\,/:;\?\!\*\~])")
# Matches and captures full stop at end of string
# (?<!\.\w) is a negative look behind that prevents matches if the last full stop
# is preceded by a a full stop then a word character.
FULL_STOP_TOKENISER = re.compile(r"(?<!\.\w)(\.)$")
# Matches a full stop at the end of a white space delimited token, i.e. one that is
# followed by white space or the end of the string. Used to skip the full stop pass
# for the many sentences that have no such token.
TRAILING_FULL_STOP = re.compile(r"\.(?:\s|\Z)")


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
    # Surround punctuation marks with space, then split on white space.
    # Doing it this way, instead of splitting on white space then splitting punctuation,
    # avoids calling PUNCTUATION_TOKENISER on each token - it's only called once per
    # sentence.
    padded_punctation = PUNCTUATION_TOKENISER.sub(r" \1 ", sentence)
    tokens = padded_punctation.split()

    if "/" in tokens:
        # Recombine "and/or" into a single token.
        tokens = combine_and_or(tokens)

    if "no." in padded_punctation.lower():
        # Recombine "No. 1" and similar into a single token.
        tokens = combine_no_number(tokens)

    if TRAILING_FULL_STOP.search(padded_punctation):
        # Second pass to separate full stops from end of tokens, but only if we have
        # detected a full stop followed by a space or the end of the string.
        # Otherwise there's no need to do anything.
        tokens = split_full_stops(tokens)

    return tokens


def combine_and_or(tokens: list[str]) -> list[str]:
    """Combine ["and", "/", "or"] into a single token.

    This function retains the case of the original tokens.

    Parameters
    ----------
    tokens : list[str]
        List of tokens.

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
    combined = []
    n = len(tokens)
    i = 0
    while i < n:
        if (
            tokens[i].lower() == "and"
            and i + 2 < n
            and tokens[i + 1] == "/"
            and tokens[i + 2].lower() == "or"
        ):
            combined.append(tokens[i] + "/" + tokens[i + 2])
            i += 3
        else:
            combined.append(tokens[i])
            i += 1

    return combined


def combine_no_number(tokens: list[str]) -> list[str]:
    """Combine "No." followed by a number into a single token.

    This function retains the case of the original tokens.

    Parameters
    ----------
    tokens : list[str]
        List of tokens.

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
    n = len(tokens)
    i = 0
    while i < n:
        if tokens[i].lower() == "no." and i + 1 < n and is_float(tokens[i + 1]):
            combined.append(tokens[i] + " " + tokens[i + 1])
            i += 2
        else:
            combined.append(tokens[i])
            i += 1

    return combined


def split_full_stops(tokens: list[str]) -> list[str]:
    """Split full stop from the end of a token.

    The full stop is not split from the end of a token if it preceded by a full stop
    then a word character, for example "U.S." does not have the trailing full stop
    split.

    Parameters
    ----------
    tokens : list[str]
        List of tokens.

    Returns
    -------
    list[str]
        Input token with trailing full stops split from tokens.

    Examples
    --------
    >>> split_full_stops(["garnish."])
    ['garnish', '.']

    >>> split_full_stops(["U.S.", "beef"])
    ['U.S.', 'beef']
    """
    split = []
    for tok in tokens:
        if tok.endswith("."):
            split.extend(t for t in FULL_STOP_TOKENISER.split(tok) if t)
        else:
            split.append(tok)

    return split

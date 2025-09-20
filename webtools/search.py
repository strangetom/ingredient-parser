#!/usr/bin/env python3

# {{DEFAULT}}
import json
import logging
import sqlite3
from itertools import islice
from typing import Generator, Iterable, TypeVar

from _globals import SQL3_DATABASE, SQL3_DATABASE_TABLE

from ingredient_parser.en.preprocess import PreProcessor

logger = logging.getLogger(__name__)
sqlite3.register_converter("json", json.loads)


def udf_find_sublist_index(
    tokens_list: str, target_list: str, case_sensitive: bool, whole_word: bool
) -> int:
    """Return starting index of target_list within tokens_list, or -1 if not found.

    This function is designed to be a user defined SQL function, which means the
    tokens_list and target_list are strings of JSON (as they are stored in the
    database).

    This function will only return the index of the first match if there are multiple
    matches.

    Parameters
    ----------
    tokens_list : str
        JSON string of list of tokens to find the target_list within.
    target_list : str
        JSON string of list of target tokens to find within tokens_list.
    case_sensitive : bool
        If True, matching is case sensitive.
        If False, matching is not case sensitive.
    whole_word : bool
        If True, each target token must exactly match the token in tokens_list.
        If False, each target token must be a substring of the matching token in
        tokens_list

    Returns
    -------
    int
        Starting index of target_list in tokens_list.
        If no match is found, return -1.
    """
    try:
        if not case_sensitive:
            tokens_list = tokens_list.lower()
            target_list = target_list.lower()

        tokens = json.loads(tokens_list)
        target = json.loads(target_list)

        if whole_word:
            # Match whole words only
            for i in range(len(tokens) - len(target) + 1):
                if target[0] == tokens[i] and tokens[i : i + len(target)] == target:
                    return i
            return -1
        else:
            # Match partial words
            for i in range(len(tokens) - len(target) + 1):
                if target[0] not in tokens[i]:
                    # Short cut, if first token of target is not a substring of the
                    # current token in tokens_list, skip to next
                    continue

                matching = True
                for j in range(len(target)):
                    # Iterate over each token in target and check that it is a substring
                    # of the corresponding token in tokens
                    if target[j] not in tokens[i + j]:
                        matching = False
                        break

                if matching:
                    return i

            return -1
    except Exception:
        return -1


def string_search(
    sentence: str,
    labels: list[str],
    sources: list[str],
    case_sensitive: bool,
    whole_word: bool,
) -> list:
    """Search database for entries containing sentence, given the supplied conditions.

    The labels of the matching tokens in an entry must be in the supplied labels list.
    The source of a matching entry must be in the supplied sources list.

    Parameters
    ----------
    sentence : str
        Sentence to search for.
        This can be a partial sentence.
    labels : list[str]
        Allowed labels for matching tokens.
    sources : list[str]
        Allowed sources for matches.
    case_sensitive : bool
        If True, search is case sensitive.
        If False, search is not case sensitive.
    whole_word : bool
        If True, tokens must match exactly.
        If False, tokens in supplied sentence must be substrings of the tokens in the
        matching entries.

    Returns
    -------
    list
        List of matching database entries.
    """
    search_tokens = [t.text for t in PreProcessor(sentence).tokenized_sentence]
    search_tokens_len = len(search_tokens)

    matches = []
    with sqlite3.connect(SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        conn.create_function(
            "find_sublist_index", 4, udf_find_sublist_index, deterministic=True
        )
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT *, find_sublist_index(tokens, :target, :case, :whole) as start_index 
            FROM {SQL3_DATABASE_TABLE} WHERE start_index >= 0
            """,
            {"target": search_tokens, "case": case_sensitive, "whole": whole_word},
        )

        for match in cursor.fetchall():
            start_index = match["start_index"]
            match_labels = {
                label
                for i, label in enumerate(match["labels"])
                if i in list(range(start_index, start_index + search_tokens_len))
            }
            if not match_labels.issubset(set(labels)):
                # Reject match if the labels of matching tokens are not in allowed list
                # of labels.
                continue

            if match["source"] not in sources:
                # Reject match if source not in allowed list of sources
                continue

            matches.append(match)

    conn.close()
    return matches


T = TypeVar("T")


def batched(
    iterable: Iterable[T],
    n: int,
) -> Generator[tuple[T, ...]]:
    """Batch data into tuples of length *n*.

    Parameters
    ----------
    iterable : Iterable
        Iterable to batch.
    n : int
        Size of each batch,

    Yields
    ------
    tuple
        Tuple of elements from input.

    Examples
    --------
    >>> list(batched("ABCDEFG", 3))
    [('A', 'B', 'C'), ('D', 'E', 'F'), ('G',)]
    """
    if n < 1:
        raise ValueError("n must be at least one")

    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        yield batch


def id_search(ids: list[int]) -> list:
    """Return database entries with give IDs.

    Parameters
    ----------
    ids : list[int]
        IDs of rows to return.

    Returns
    -------
    list
        List of database entries with given IDs.
    """
    batch_size = 250  # SQLite has a default limit of 999 parameters
    matches = []
    with sqlite3.connect(SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        for batch in batched(ids, batch_size):
            cursor.execute(
                f"""
                SELECT *
                FROM {SQL3_DATABASE_TABLE}
                WHERE id IN ({",".join(["?"] * len(batch))})
                """,
                (batch),
            )
            matches += cursor.fetchall()

    conn.close()
    return matches


def list_all_entries() -> list:
    """List all entries in database.

    Returns
    -------
    list
        List of database entries.
    """
    matches = []
    with sqlite3.connect(SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {SQL3_DATABASE_TABLE}")
        matches += cursor.fetchall()

    conn.close()
    return matches

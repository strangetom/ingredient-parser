#!/usr/bin/env python3

import concurrent.futures as cf
import json
import logging
import sqlite3
from dataclasses import dataclass
from functools import partial
from itertools import chain, islice
from typing import Any, Callable, Iterable

from matplotlib import pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
)

from ingredient_parser import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

sqlite3.register_converter("json", json.loads)

DEFAULT_MODEL_LOCATION = "ingredient_parser/en/data/model.en.crfsuite"


@dataclass
class DataVectors:
    """Dataclass to store the loaded and transformed inputs."""

    sentences: list[str]
    features: list[list[dict[str, str]]]
    tokens: list[list[str]]
    labels: list[list[str]]
    source: list[str]
    uids: list[int]
    discarded: int


@dataclass
class Metrics:
    """Metrics returned by sklearn.metrics.classification_report for each label."""

    precision: float
    recall: float
    f1_score: float
    support: int


@dataclass
class TokenStats:
    """Statistics for token classification performance."""

    B_NAME_TOK: Metrics
    I_NAME_TOK: Metrics
    NAME_VAR: Metrics
    NAME_MOD: Metrics
    NAME_SEP: Metrics
    QTY: Metrics
    UNIT: Metrics
    SIZE: Metrics
    COMMENT: Metrics
    PURPOSE: Metrics
    PREP: Metrics
    PUNC: Metrics
    macro_avg: Metrics
    weighted_avg: Metrics
    accuracy: float


@dataclass
class TokenStatsCombinedName:
    """Statistics for token classification performance."""

    NAME: Metrics
    QTY: Metrics
    UNIT: Metrics
    SIZE: Metrics
    COMMENT: Metrics
    PURPOSE: Metrics
    PREP: Metrics
    PUNC: Metrics
    macro_avg: Metrics
    weighted_avg: Metrics
    accuracy: float


@dataclass
class SentenceStats:
    """Statistics for sentence classification performance."""

    accuracy: float


@dataclass
class Stats:
    """Statistics for token and sentence classification performance."""

    token: TokenStats | TokenStatsCombinedName
    sentence: SentenceStats
    seed: int


def chunked(iterable: Iterable, n: int) -> Iterable:
    """Break *iterable* into lists of length *n*.

    By the default, the last yielded list will have fewer than *n* elements
    if the length of *iterable* is not divisible by *n*:

    Parameters
    ----------
    iterable : Iterable
        Iterable to chunk.
    n : int
        Size of each chunk.

    Returns
    -------
    Iterable
        Chunks of iterable with size n (or less for the last chunk).

    Examples
    --------
    >>> list(chunked([1, 2, 3, 4, 5, 6], 3))
    [[1, 2, 3], [4, 5, 6]]

    >>> list(chunked([1, 2, 3, 4, 5, 6, 7, 8], 3))
    [[1, 2, 3], [4, 5, 6], [7, 8]]
    """

    def take(n: int, iterable: Iterable) -> list:
        """Return first n items of the iterable as a list.

        Parameters
        ----------
        n : int
            Number of items to return in list.
        iterable : Iterable
            Iterable to return items from.

        Returns
        -------
        list
            List of first n items of iterable.
        """
        return list(islice(iterable, n))

    return iter(partial(take, n, iter(iterable)), [])


def select_preprocessor(lang: str) -> Any:
    """Select appropraite PreProcessor class for given language.

    Parameters
    ----------
    lang : str
        Language of training data.

    Returns
    -------
    Any
        PreProcessor class for pre-processing in given language.

    Raises
    ------
    ValueError
        Selected langauage not supported
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f'Unsupported language "{lang}"')

    match lang:
        case "en":
            from ingredient_parser.en import PreProcessor

            return PreProcessor


def load_datasets(
    database: str,
    table: str,
    datasets: list[str],
    discard_other: bool = True,
    combine_name_labels: bool = False,
) -> DataVectors:
    """Load raw data from csv files and transform into format required for training.

    Parameters
    ----------
    database : str
        Path to database of training data.
    table : str
        Name of database table containing training data.
    datasets : list[str]
        List of data source to include.
        Valid options are: nyt, cookstr, bbc, cookstr, tc.
        Default is PARSER.
    discard_other : bool, optional
        If True, discard sentences containing tokens with OTHER label.
    combine_name_labels :  bool, optional
        If True, combine all labels containing "NAME" into a single "NAME" label.

    Returns
    -------
    DataVectors
        Dataclass holding:
            raw input sentences,
            features extracted from sentences,
            labels for sentences
            source dataset of sentences
    """
    PreProcessor = select_preprocessor(table)

    logger.info("Loading and transforming training data.")

    n = len(datasets)
    with sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            f"SELECT * FROM {table} WHERE source IN ({','.join(['?'] * n)})",
            datasets,
        )
        data = [dict(row) for row in c.fetchall()]
    conn.close()

    # Chunk data into 4 groups to process in parallel.
    n_chunks = 4
    # Define chunk size so all groups have about the same number of elements, except the
    # last group which will be slightly smaller.
    chunk_size = int((len(data) + n_chunks) / n_chunks)
    chunks = chunked(data, chunk_size)

    with cf.ProcessPoolExecutor(max_workers=4) as executor:
        vectors = [
            vec
            for vec in executor.map(
                process_sentences,
                chunks,
                [PreProcessor] * n_chunks,
                [discard_other] * n_chunks,
                [combine_name_labels] * n_chunks,
            )
        ]

    all_vectors = DataVectors(
        sentences=list(chain.from_iterable(v.sentences for v in vectors)),
        features=list(chain.from_iterable(v.features for v in vectors)),
        tokens=list(chain.from_iterable(v.tokens for v in vectors)),
        labels=list(chain.from_iterable(v.labels for v in vectors)),
        source=list(chain.from_iterable(v.source for v in vectors)),
        uids=list(chain.from_iterable(v.uids for v in vectors)),
        discarded=sum(v.discarded for v in vectors),
    )

    logger.info(f"{len(all_vectors.sentences):,} usable vectors.")
    logger.info(f"{all_vectors.discarded:,} discarded due to OTHER labels.")
    return all_vectors


def process_sentences(
    data: list[dict],
    PreProcessor: Callable,
    discard_other: bool,
    combine_name_labels: bool,
) -> DataVectors:
    """Process sentences from database into format needed for training and evaluation.

    Parameters
    ----------
    data : list[dict]
        List of dicts, where each dict is the database row.
    PreProcessor : Callable
        PreProcessor class to preprocess sentences.
    discard_other : bool
        If True, discard sentences with OTHER.
    combine_name_labels : bool
        If True, combine all labels containing "NAME" into a single "NAME" label.

    Returns
    -------
    DataVectors
        Dataclass holding:
            raw input sentences,
            features extracted from sentences,
            labels for sentences,
            source dataset of sentences,
            uids for each sentence,
            number of discarded sentences

    Raises
    ------
    ValueError
        Raised if number of calculated token does not match number of labels.
    """
    source, sentences, features, tokens, labels, uids = [], [], [], [], [], []
    discarded = 0
    for entry in data:
        if discard_other and "OTHER" in entry["labels"]:
            discarded += 1
            continue

        source.append(entry["source"])
        sentences.append(entry["sentence"])
        p = PreProcessor(entry["sentence"])
        uids.append(entry["id"])
        features.append(p.sentence_features())
        tokens.append([t.text for t in p.tokenized_sentence])

        if combine_name_labels:
            new_labels = []
            for label in entry["labels"]:
                if "NAME" in label:
                    new_labels.append("NAME")
                else:
                    new_labels.append(label)
            labels.append(new_labels)
        else:
            labels.append(entry["labels"])

        # Ensure length of tokens and length of labels are the same
        if len(p.tokenized_sentence) != len(entry["labels"]):
            raise ValueError(
                (
                    f'"{entry["sentence"]}" (ID: {entry["id"]}) has '
                    f"{len(p.tokenized_sentence)} tokens "
                    f"but {len(entry['labels'])} labels."
                )
            )

    return DataVectors(sentences, features, tokens, labels, source, uids, discarded)


def evaluate(
    predictions: list[list[str]],
    truths: list[list[str]],
    seed: int,
    combine_name_labels: bool,
) -> Stats:
    """Calculate statistics on the predicted labels for the test data.

    Parameters
    ----------
    predictions : list[list[str]]
        Predicted labels for each test sentence.
    truths : list[list[str]]
        True labels for each test sentence.
    seed : int
        Seed value that produced the results.
    combine_name_labels : bool
        If True, all NAME labels are combined into a single NAME label.

    Returns
    -------
    Stats
        Dataclass holding token and sentence statistics.
    """
    # Generate token statistics
    # Flatten prediction and truth lists
    flat_predictions = list(chain.from_iterable(predictions))
    flat_truths = list(chain.from_iterable(truths))
    labels = list(set(flat_predictions))

    report = classification_report(
        flat_truths,
        flat_predictions,
        labels=labels,
        output_dict=True,
    )

    # Convert report to TokenStats dataclass
    token_stats = {}
    for k, v in report.items():  # type: ignore
        # Convert dict to Metrics
        if k in [*labels, "macro avg", "weighted avg"]:
            k = k.replace(" ", "_")
            token_stats[k] = Metrics(
                v["precision"], v["recall"], v["f1-score"], int(v["support"])
            )

    token_stats["accuracy"] = accuracy_score(flat_truths, flat_predictions)
    if combine_name_labels:
        token_stats = TokenStatsCombinedName(**token_stats)
    else:
        token_stats = TokenStats(**token_stats)

    # Generate sentence statistics
    # The only statistics that makes sense here is accuracy because there are only
    # true-positive results (i.e. correct) and false-negative results (i.e. incorrect)
    correct_sentences = len([p for p, t in zip(predictions, truths) if p == t])
    sentence_stats = SentenceStats(correct_sentences / len(predictions))

    return Stats(token_stats, sentence_stats, seed)


def confusion_matrix(
    predictions: list[list[str]],
    truths: list[list[str]],
    figure_path="confusion_matrix.svg",
) -> None:
    """Plot and save a confusion matrix for token labels.

    Parameters
    ----------
    predictions : list[list[str]]
        Predicted labels for each test sentence.
    truths : list[list[str]]
        True labels for each test sentence.
    figure_path : str, optional
        Path to save figure to.
    """
    # Flatten prediction and truth lists
    flat_predictions = list(chain.from_iterable(predictions))
    flat_truths = list(chain.from_iterable(truths))
    labels = list(set(flat_predictions))

    cm = ConfusionMatrixDisplay.from_predictions(
        flat_truths, flat_predictions, labels=labels
    )
    # Set the diagonal to -1, to better highlight the mislabels
    for i in range(cm.confusion_matrix.shape[0]):
        cm.confusion_matrix[i, i] = -1

    fig, ax = plt.subplots(figsize=(10, 10))
    cm.plot(ax=ax, colorbar=False)
    ax.tick_params(axis="x", labelrotation=45)
    fig.tight_layout()
    fig.savefig(figure_path)
    logger.info(f"Confusion matrix saved to {figure_path}.")
    plt.close(fig)


def convert_num_ordinal(num: int | float | str) -> str:
    """Convert a number (int-like) into its ordinal.

    Falls back to input if unsuccessful.

    Parameters
    ----------
    num : int | float | str
        Number to convert to ordinal.

    Returns
    -------
    str
        Ordinal version of number.

    Examples
    --------
    >>> convert_num_ordinal(0)
    "0th"

    >>> convert_num_ordinal("3")
    "3rd"

    >>> convert_num_ordinal(122.0)
    "122nd"

    >>> convert_num_ordinal(213)
    "213th"
    """
    try:
        n = int(num)
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        else:
            suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
        return str(n) + suffix
    except TypeError or ValueError:
        return str(num)

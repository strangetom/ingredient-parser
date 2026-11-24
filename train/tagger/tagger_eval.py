#!/usr/bin/env python3

import logging
from dataclasses import dataclass
from itertools import chain

from sklearn.metrics import (
    accuracy_score,
    classification_report,
)
from tabulate import tabulate

from ingredient_parser.perceptron import PerceptronTagger

logger = logging.getLogger(__name__)


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

    token: TokenStats
    sentence: SentenceStats
    seed: int


def evaluate(
    predictions: list[list[str]],
    truths: list[list[str]],
    seed: int,
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

    Returns
    -------
    Stats
        Dataclass holding token and sentence statistics.
    """
    # Generate token statistics
    # Flatten prediction and truth lists
    flat_predictions = list(chain.from_iterable(predictions))
    flat_truths = list(chain.from_iterable(truths))
    tags = list(set(flat_predictions))

    report = classification_report(
        flat_truths,
        flat_predictions,
        labels=tags,
        output_dict=True,
        zero_division="warn",
    )

    # Convert report to TokenStats dataclass
    token_stats = {}
    for k, v in report.items():  # type: ignore
        # Convert dict to Metrics
        if k in ["macro avg", "weighted avg"]:
            k = k.replace(" ", "_")
            token_stats[k] = Metrics(
                v["precision"], v["recall"], v["f1-score"], int(v["support"])
            )

    token_stats["accuracy"] = accuracy_score(flat_truths, flat_predictions)
    token_stats = TokenStats(**token_stats)

    # Generate sentence statistics
    # The only statistics that makes sense here is accuracy because there are only
    # true-positive results (i.e. correct) and false-negative results (i.e. incorrect)
    correct_sentences = len([p for p, t in zip(predictions, truths) if p == t])
    sentence_stats = SentenceStats(correct_sentences / len(predictions))

    return Stats(token_stats, sentence_stats, seed)


def evaluate_model_only(
    tagger: PerceptronTagger,
    tokens_test: list[list[str]],
    tags_test: list[list[str]],
    seed: int,
) -> tuple[Stats, list[list[str]], list[list[float]]]:
    """Evaluate model only and print results.

    Parameters
    ----------
    tagger : NumpyCRFInference
        Tagger instance.
    tokens_test : list[list[FeatureDict]]
        List of token lists for test sentences.
    tags_test : list[list[str]]
        List of true tag lists for test sentences.
    seed : int
        Seed used to train model.

    Returns
    -------
    tuple[Stats, list[list[str]], list[list[float]]]
        Stats object containing accuracy results.
        Predicted labels for each sentence.
        Scores for each tag. Note these are always 1.0.
    """
    logger.info("Evaluating model using test data.")
    tags_pred, scores_pred = [], []
    for tokens in tokens_test:
        _, tags = zip(*tagger.tag(tokens))
        tags_pred.append(list(tags))
        scores_pred.append([1.0] * len(tokens))

    stats = evaluate(tags_pred, tags_test, seed)

    headers = ["Sentence-level results", "Word-level results"]
    table = []
    table.append(
        [
            f"Accuracy: {100 * stats.sentence.accuracy:.2f}%",
            f"Accuracy: {100 * stats.token.accuracy:.2f}%\n"
            f"Precision (micro) {100 * stats.token.weighted_avg.precision:.2f}%\n"
            f"Recall (micro) {100 * stats.token.weighted_avg.recall:.2f}%\n"
            f"F1 score (micro) {100 * stats.token.weighted_avg.f1_score:.2f}%",
        ]
    )
    formatted_table = "\n" + tabulate(
        table,
        headers=headers,
        tablefmt="fancy_grid",
        maxcolwidths=[None, None],
        stralign="left",
        numalign="right",
    )
    logger.info(formatted_table)

    return stats, tags_pred, scores_pred

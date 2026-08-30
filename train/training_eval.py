#!/usr/bin/env python3

import logging
from dataclasses import dataclass
from itertools import chain

from sklearn.metrics import (
    accuracy_score,
    classification_report,
)
from tabulate import tabulate

from ingredient_parser.dataclasses import LabelledToken, ParsedIngredient
from ingredient_parser.inference import FeatureDict, NumpyCRFInference

from .training_utils import select_postprocessor

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


def evaluate_model_only(
    tagger: NumpyCRFInference,
    features_test: list[list[FeatureDict]],
    truth_test: list[list[str]],
    seed: int,
    combine_name_labels: bool = False,
) -> tuple[Stats, list[list[str]], list[list[float]]]:
    """Evaluate model only and print results.

    Parameters
    ----------
    tagger : NumpyCRFInference
        Tagger instance.
    features_test : list[list[FeatureDict]]
        List of feature lists for test sentences.
    truth_test : list[list[str]]
        List of true label lists for test sentences.
    seed : int
        Seed used to train model.
    combine_name_labels : bool, optional
        If True, combine all NAME labels into a single NAME label.

    Returns
    -------
    tuple[Stats, list[list[str]], list[list[float]]]
        Stats object containing accuracy results.
        Predicted labels for each sentence.
        Scores for predicted labels for each sentence.
    """
    logger.info("Evaluating model using test data.")
    labels_pred, scores_pred = [], []
    for X in features_test:
        labels, scores = zip(
            *tagger.tag_from_features(
                X, expect_name_in_output=False, constrain_transitions=False
            )
        )
        labels_pred.append(list(labels))
        scores_pred.append(list(scores))

    stats = evaluate(labels_pred, truth_test, seed, combine_name_labels)

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

    return stats, labels_pred, scores_pred


def evaluate_model_with_label_corrections(
    tagger: NumpyCRFInference,
    features_test: list[list[FeatureDict]],
    truth_test: list[list[str]],
    seed: int,
    combine_name_labels: bool = False,
) -> tuple[Stats, list[list[str]], list[list[float]]]:
    """Evaluate model, including invalid label corrections, and print results.

    Parameters
    ----------
    tagger : NumpyCRFInference
        Tagger instance.
    features_test : list[list[FeatureDict]]
        List of feature lists for test sentences.
    truth_test : list[list[str]]
        List of true label lists for test sentences.
    seed : int
        Seed used to train model.
    combine_name_labels : bool, optional
        If True, combine all NAME labels into a single NAME label.

    Returns
    -------
    tuple[Stats, list[list[str]], list[list[float]]]
        Stats object containing accuracy results.
        Predicted labels for each sentence.
        Scores for predicted labels for each sentence.
    """
    logger.info(
        "Evaluating model (including invalid label corrections) using test data."
    )
    labels_pred, scores_pred = [], []
    for X in features_test:
        labels, scores = zip(
            *tagger.tag_from_features(
                X, expect_name_in_output=True, constrain_transitions=True
            )
        )
        labels_pred.append(list(labels))
        scores_pred.append(list(scores))

    stats = evaluate(labels_pred, truth_test, seed, combine_name_labels)

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

    return stats, labels_pred, scores_pred


def evalate_postprocessor_output(
    tagger: NumpyCRFInference,
    features_test: list[list[FeatureDict]],
    tokens_test: list[list[str]],
    truth_test: list[list[str]],
):
    """Evaluate combined model and full post-processing and print results.

    Parameters
    ----------
    tagger : NumpyCRFInference
        Tagger instance.
    features_test : list[list[FeatureDict]]
        List of feature lists for test sentences.
    tokens_test : list[list[str]]
        List of token lists for test sentences.
    truth_test : list[list[str]]
        List of true label lists for test sentences.
    """
    logger.info(
        (
            "Evaluating model (including invalid label corrections) and "
            "post-processing using test data."
        )
    )

    PostProcessor = select_postprocessor("en")

    correct = 0
    for features, tokens, true_labels in zip(features_test, tokens_test, truth_test):
        predicted_labels, _ = zip(
            *tagger.tag_from_features(
                features, expect_name_in_output=True, constrain_transitions=True
            )
        )
        predicted_tokens = [
            LabelledToken(
                index=idx,
                text=token,
                pos_tag=feature_dict["pos"],
                label=label,
                score=0,
                plural=False,
            )
            for idx, (feature_dict, token, label) in enumerate(
                zip(features, tokens, predicted_labels)
            )
        ]
        predicted_parsed = PostProcessor("", predicted_tokens, {}).parsed

        true_tokens = [
            LabelledToken(
                index=idx,
                text=token,
                pos_tag=feature_dict["pos"],
                label=label,
                score=0,
                plural=False,
            )
            for idx, (feature_dict, token, label) in enumerate(
                zip(features, tokens, true_labels)
            )
        ]
        true_parsed = PostProcessor("", true_tokens, {}).parsed

        if compare_parsed_sentences(predicted_parsed, true_parsed):
            correct += 1

    logger.info(
        "%.2f%% of test sentence produce correct results.",
        100 * correct / len(features_test),
    )


def compare_parsed_sentences(
    predicted: ParsedIngredient, true: ParsedIngredient
) -> bool:
    """Compare ParsedIngredient objects generated from predicted and true labels.

    Only the text fields of the IngredientText, IngredientAmount and
    CompositeIngredientAmount objects are compared; scores and other fields are ignored.

    Parameters
    ----------
    predicted : ParsedIngredient
        ParsedIngredient object generated from predicted labels.
    true : ParsedIngredient
        ParsedIngredient object generated from true labels.

    Returns
    -------
    bool
        True, if the ParsedIngredient objects are equivalent, else False.
    """
    # Name
    if len(predicted.name) != len(true.name):
        return False

    for predicted_name, true_name in zip(predicted.name, true.name):
        if predicted_name.text != true_name.text:
            return False

    # Amount
    if len(predicted.amount) != len(true.amount):
        return False

    for predicted_amount, true_amount in zip(predicted.amount, true.amount):
        if predicted_amount.text != true_amount.text:
            return False
    # Size
    if (predicted.size is None) ^ (true.size is None):
        return False
    elif (
        (predicted.size is not None)
        and (true.size is not None)
        and (predicted.size.text != true.size.text)
    ):
        return False

    # Prep
    if (predicted.preparation is None) ^ (true.preparation is None):
        return False
    elif (
        (predicted.preparation is not None)
        and (true.preparation is not None)
        and (predicted.preparation.text != true.preparation.text)
    ):
        return False

    # Comment
    if (predicted.comment is None) ^ (true.comment is None):
        return False
    elif (
        (predicted.comment is not None)
        and (true.comment is not None)
        and (predicted.comment.text != true.comment.text)
    ):
        return False

    # Purpose
    if (predicted.purpose is None) ^ (true.purpose is None):
        return False
    elif (
        (predicted.purpose is not None)
        and (true.purpose is not None)
        and (predicted.purpose.text != true.purpose.text)
    ):
        return False

    return True

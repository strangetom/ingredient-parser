#!/usr/bin/env python3

import logging
from collections import Counter
from itertools import chain

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader("train/viz"),
    trim_blocks=False,
)


def test_results_to_html(
    sentences: list[str],
    sentence_tokens: list[str],
    labels_truth: list[list[str]],
    labels_prediction: list[list[str]],
    scores_prediction: list[list[float]],
    sentence_sources: list[str],
) -> None:
    """Output results for test vectors that failed to label entire sentence with the
    truth labels in HTML format.

    Parameters
    ----------
    sentences : list[str]
        List of ingredient sentences
    sentence_tokens : list[str]
        List of tokens for sentence
    labels_truth : list[list[str]]
        True labels for tokens
    labels_prediction : list[list[str]]
        Predicted labels for tokens
    scores_prediction : list[list[float]]
        Scores for predicted labels for tokens
    sentence_sources : list[str]
        List of sentence sources
    """
    incorrect_sentences = []
    # Sort by sentence sort
    for src, sentence, tokens, truth, prediction, scores in sorted(
        zip(
            sentence_sources,
            sentences,
            sentence_tokens,
            labels_truth,
            labels_prediction,
            scores_prediction,
        )
    ):
        if truth != prediction:
            # Count mismatches and only include if greater than 0
            mismatch_count = sum(i != j for i, j in zip(truth, prediction))
            if mismatch_count > 0:
                label_errors = list(
                    chain.from_iterable(
                        [{t, p} for t, p in zip(truth, prediction) if t != p]
                    )
                )

                incorrect_sentence = {
                    "sentence": sentence,
                    "tokens": tokens,
                    "labels": list(zip(truth, prediction)),
                    "scores": scores,
                    "source": src,
                    "mismatch_count": mismatch_count,
                    "label_errors": label_errors,
                }
                incorrect_sentences.append(incorrect_sentence)

    # Count unique numbers of errors.
    error_counts = {sentence["mismatch_count"] for sentence in incorrect_sentences}

    # Count incorrect sentences per source.
    sentence_source_counts = Counter(sentence_sources)
    error_source_counts = Counter(
        [sentence["source"] for sentence in incorrect_sentences]
    )
    error_source = [
        (source, count, 100 * count / sentence_source_counts[source])
        for source, count in error_source_counts.items()
    ]

    # Count incorrect sentence per label.
    label_error_count = Counter(
        chain.from_iterable(
            [sentence["label_errors"] for sentence in incorrect_sentences]
        )
    )
    error_label = sorted(label_error_count.items(), key=lambda x: x[0])

    test_results = {
        "sentences": incorrect_sentences,
        "error_counts": sorted(error_counts),
        "error_source": error_source,
        "error_label": error_label,
    }

    test_results_template = TEMPLATE_ENVIRONMENT.get_template("test_results.html.jinja")
    html = test_results_template.render(test_results)
    with open("test_results.html", "w") as f:
        f.write(html)

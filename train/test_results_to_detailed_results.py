import csv
from collections import defaultdict
from dataclasses import dataclass

from ingredient_parser import PreProcessor


@dataclass(frozen=True, order=True)
class _TokenPrediction:
    token: str
    index: int
    sentence: str
    truth: str
    prediction: str


@dataclass(frozen=True, order=True)
class _SentenceLabeling:
    sentence: str
    truth: str
    prediction: str


def test_results_to_detailed_results(
    sentences: list[str],
    labels_truth: list[list[str]],
    labels_prediction: list[list[str]],
    scores_prediction: list[list[float]],
    sentence_sources: list[str],
) -> None:
    """Output detailed labeling results for test vectors to tab-separated values files.

    Parameters
    ----------
    sentences : list[str]
        List of ingredient sentences
    labels_truth : list[list[str]]
        True labels for sentence
    labels_prediction : list[list[str]]
        Predicted labels for sentence
    scores_prediction : list[list[float]]
        Scores for predicted labels for sentence
    sentence_sources : list[str]
        List of sentence sources, either NYT of SF
    """
    # Compute classification stats
    # sentence_classif: sentence => (# correct, # incorrect)
    sentence_classif = defaultdict(lambda: defaultdict(int))
    # sentence_details: sentence => classification details about the sentence
    sentence_details = defaultdict(_SentenceLabeling)
    # token_classif: token => (# correct, # incorrect)
    token_classif = defaultdict(lambda: defaultdict(int))
    # token_details: auxilliary info for misclassified tokens
    token_details = []

    for src, sentence, truth, prediction, scores in sorted(
        zip(
            sentence_sources,
            sentences,
            labels_truth,
            labels_prediction,
            scores_prediction,
        )
    ):
        # per-sentence numbers
        correct = truth == prediction
        sentence_classif[sentence][correct] += 1
        sentence_details[sentence] = _SentenceLabeling(sentence, truth, prediction)

        # per-token numbers
        tokens: list[str] = PreProcessor(
            sentence, defer_pos_tagging=True
        ).tokenized_sentence
        idx = 0
        for token, truth1, prediction1, score in zip(tokens, truth, prediction, scores):
            correct = truth1 == prediction1
            token_classif[token][correct] += 1
            if not correct:
                token_details.append(
                    _TokenPrediction(token, idx, sentence, truth1, prediction1)
                )
            idx += 1

    # Write out classification stats
    # Per-token stats
    with open("classification_results_tokens.tsv", "w") as crs:
        writer = csv.writer(crs, delimiter="\t", lineterminator="\n")
        writer.writerow(["token", "total", "correct", "incorrect", "fraction_correct"])
        for token, token_dict in token_classif.items():
            correct, incorrect = token_dict[True], token_dict[False]
            total = correct + incorrect
            frac_correct = float(correct) / total
            assert "\t" not in token, f"token has a tab: {token}"
            writer.writerow([token, total, correct, incorrect, f"{frac_correct:.3f}"])

    with open("classification_results_token_sentences.tsv", "w") as crts:
        writer = csv.writer(crts, delimiter="\t", lineterminator="\n")
        writer.writerow(["token", "index", "truth", "prediction", "sentence"])
        for tcr in sorted(token_details):
            writer.writerow(
                [tcr.token, tcr.index, tcr.truth, tcr.prediction, tcr.sentence]
            )

    # Per-sentence stats
    with open("classification_results_sentences.tsv", "w") as crs:
        writer = csv.writer(crs, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "sentence",
                "total",
                "correct",
                "incorrect",
                "fraction_correct",
                "truth",
                "prediction",
            ]
        )
        for sentence, sentence_dict in sentence_classif.items():
            correct, incorrect = sentence_dict[True], sentence_dict[False]
            total = correct + incorrect
            frac_correct = float(correct) / total
            assert "\t" not in sentence, f"sentence has a tab: {sentence}"
            writer.writerow(
                [
                    sentence,
                    total,
                    correct,
                    incorrect,
                    f"{frac_correct:.3f}",
                    ",".join(sentence_details[sentence].truth),
                    ",".join(sentence_details[sentence].prediction),
                ]
            )

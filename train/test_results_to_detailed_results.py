import csv
from collections import defaultdict
from dataclasses import dataclass


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
    truth: list[str]
    prediction: list[str]


def test_results_to_detailed_results(
    sentences: list[str],
    sentence_tokens: list[str],
    features_truth: list[list[dict[str, str | bool]]],
    labels_truth: list[list[str]],
    labels_prediction: list[list[str]],
    scores_prediction: list[list[float]],
) -> None:
    """Output detailed labeling results for test vectors to tab-separated values files.

    Parameters
    ----------
    sentences : list[str]
        List of ingredient sentences.
    sentence_tokens : list[str]
        List of tokens for sentence.
    labels_truth : list[list[str]]
        True labels for sentence.
    features_truth : list[list[dict[str, str | bool]]]
        Features for tokens in sentences.
    labels_prediction : list[list[str]]
        Predicted labels for sentence.
    scores_prediction : list[list[float]]
        Scores for predicted labels for sentence.
    """
    # Compute classification stats
    # sentence_classif: sentence => (# correct, # incorrect)
    sentence_classif = defaultdict(lambda: defaultdict(int))
    # sentence_details: sentence => classification details about the sentence
    sentence_details = {}
    # token_classif: token => (# correct, # incorrect)
    token_classif = defaultdict(lambda: defaultdict(int))
    # token_details: auxilliary info for misclassified tokens
    token_details = []
    # feature_classif: feature => (# correct, # incorrect)
    feature_classif = defaultdict(lambda: defaultdict(int))

    for sentence, tokens, features, truth, prediction in sorted(
        zip(sentences, sentence_tokens, features_truth, labels_truth, labels_prediction)
    ):
        # per-sentence numbers
        correct = truth == prediction
        sentence_classif[sentence][correct] += 1
        sentence_details[sentence] = _SentenceLabeling(sentence, truth, prediction)

        # per-token numbers
        idx = 0
        for token, truth1, prediction1 in zip(tokens, truth, prediction):
            correct = truth1 == prediction1
            token_classif[token][correct] += 1
            if not correct:
                token_details.append(
                    _TokenPrediction(token, idx, sentence, truth1, prediction1)
                )
            idx += 1

        # per feature numbers
        for feature_dict, truth1, prediction1 in zip(features, truth, prediction):
            correct = truth1 == prediction1
            for feature, value in feature_dict.items():
                feature_str = feature + "=" + str(value)
                feature_classif[feature_str][correct] += 1

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

    # Per-feature stats
    with open("classification_results_features.tsv", "w") as crs:
        writer = csv.writer(crs, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ["feature", "total", "correct", "incorrect", "fraction_correct"]
        )
        for feature, feature_dict in feature_classif.items():
            correct, incorrect = feature_dict[True], feature_dict[False]
            total = correct + incorrect
            frac_correct = float(correct) / total
            writer.writerow([feature, total, correct, incorrect, f"{frac_correct:.3f}"])

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

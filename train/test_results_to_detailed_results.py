from collections import defaultdict

from ingredient_parser import PreProcessor


def test_results_to_detailed_results(
    sentences: list[str],
    labels_truth: list[list[str]],
    labels_prediction: list[list[str]],
    scores_prediction: list[list[float]],
    sentence_sources: list[str],
) -> None:
    # Compute token classification stats
    # token_classif: token => (# correct, # incorrect)
    token_classif = defaultdict(lambda: defaultdict(int))
    for src, sentence, truth, prediction, scores in sorted(
        zip(
            sentence_sources,
            sentences,
            labels_truth,
            labels_prediction,
            scores_prediction,
        )
    ):
        tokens: list[str] = PreProcessor(
            sentence, defer_pos_tagging=True
        ).tokenized_sentence
        for token, truth1, prediction1, score in zip(
                tokens, truth, prediction, scores
        ):
            correct = truth1 == prediction1
            token_classif[token][correct] += 1

    with open("classification_results_tokens.tsv", "w") as tcr:
        print("\t".join(["token", "total", "correct", "incorrect", "fraction_correct"]), file=tcr)
        for token, token_dict in token_classif.items():
            correct, incorrect = token_dict[True], token_dict[False]
            total = correct + incorrect
            frac_correct = float(correct) / total
            assert "\t" not in token, f"token has a tab: {token}"
            print("\t".join(map(str, [token, total, correct, incorrect,
                            f"{frac_correct:.3f}"])), file=tcr)

    # TODO: Count sentences most often misclassified
    # TODO: Count token pairs most often misclassified

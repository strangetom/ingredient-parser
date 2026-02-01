#!/usr/bin/env python3

import argparse
import pathlib
from collections import defaultdict

import matplotlib as mpl
import matplotlib.pyplot as plt
import pycrfsuite

# Various formatting parameters
mpl.rcParams["text.color"] = "#ebdbb2"
mpl.rcParams["xtick.color"] = "#ebdbb2"
mpl.rcParams["ytick.color"] = "#ebdbb2"
mpl.rcParams["grid.color"] = "#ebdbb2"
mpl.rcParams["grid.linestyle"] = "--"
mpl.rcParams["grid.alpha"] = 0.5
mpl.rcParams["axes.labelcolor"] = "#ebdbb2"
mpl.rcParams["axes.facecolor"] = "#32302f"
mpl.rcParams["figure.facecolor"] = "#32302f"


COLORS = {
    "B_NAME_TOK": "#cc241d",
    "I_NAME_TOK": "#98971a",
    "NAME_VAR": "#d79921",
    "NAME_MOD": "#458588",
    "NAME_SEP": "#b16286",
    "QTY": "#689d6a",
    "UNIT": "#a89984",
    "PREP": "#fb4934",
    "PURPOSE": "#b8bb26",
    "COMMENT": "#fabd2f",
    "SIZE": "#83a598",
    "PUNC": "#d3869b",
}
LABEL_OFFSET = {
    "B_NAME_TOK": 5 / 20,
    "I_NAME_TOK": 4 / 20,
    "NAME_VAR": 3 / 20,
    "NAME_MOD": 2 / 20,
    "NAME_SEP": 1 / 20,
    "QTY": 0,
    "UNIT": -1 / 20,
    "PREP": -2 / 20,
    "PURPOSE": -3 / 20,
    "COMMENT": -4 / 20,
    "SIZE": -5 / 20,
    "PUNC": -6 / 20,
}


# Define type for model features.
# The dict key is the feature name e.g. sentence_length, without the specific value.
# The dict value has keys of labels and values of a list of weights for that label
# for all instances of the feature e.g. sentence_length:4, sentence_length:8 etc.
FeatureWeights = dict[str, dict[str, list[float]]]


def plot(features: FeatureWeights, output: pathlib.Path) -> str:
    """Plot figure showing distribution of weights for each label for each feature.

    Parameters
    ----------
    features : FeatureWeights
        Feature names, and the weights for each label.
    output : pathlib.Path
        Path to save output to.

    Returns
    -------
    str
        Path to saved file.
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 100))

    unlabelled_lines = {
        "B_NAME_TOK",
        "I_NAME_TOK",
        "NAME_VAR",
        "NAME_MOD",
        "NAME_SEP",
        "QTY",
        "UNIT",
        "PREP",
        "PURPOSE",
        "COMMENT",
        "SIZE",
        "PUNC",
    }
    for i, (feat, weights) in enumerate(features.items()):
        for label, weights in weights.items():
            y = [i + LABEL_OFFSET[label]] * len(weights)

            label_prefix = "" if label in unlabelled_lines else "_"
            ax.scatter(weights, y, color=COLORS[label], label=label_prefix + label)
            if label_prefix == "":
                unlabelled_lines.remove(label)

    x_min, x_max = ax.get_xlim()
    for i in range(len(features)):
        ax.hlines(i + 0.5, x_min, x_max, color="#7c6f64")

    ax.set_yticks(list(range(len(features))))
    ax.set_yticklabels(list(features.keys()))
    ax.set_ylim((-0.5, len(features) - 0.5))
    ax.set_xlim((x_min, x_max))
    ax.grid(True, axis="x")
    ax.legend()

    fig.tight_layout()
    if output.suffix != ".png":
        output = output.with_suffix(".png")
    fig.savefig(output, dpi=200)
    return output


def load_model_features(model_path: str) -> FeatureWeights:
    """Load model features.

    Parameters
    ----------
    model_path : str
        Path to model.

    Returns
    -------
    FeatureWeights
        Weights for each feature.
    """
    tagger = pycrfsuite.Tagger()
    tagger.open(str(model_path))

    tagger_features = tagger.info()
    features = defaultdict(lambda: defaultdict(list))
    for (feature, label), weight in tagger_features.state_features.items():
        feature_name = feature.split(":", 1)[0]
        features[feature_name][label].append(weight)

    return features


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate plot of model weights.")
    parser.add_argument(
        "--model",
        "-m",
        type=pathlib.Path,
        default="ingredient_parser/en/data/model.en.crfsuite",
        help="Path for model.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=pathlib.Path,
        default="weight_plot.png",
        help="Path for model.",
    )
    args = parser.parse_args()

    features = load_model_features(args.model)
    output = plot(features, args.output)
    print(f"Weights plot save to {output}.")

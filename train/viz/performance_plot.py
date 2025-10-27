#!/usr/bin/env python3

import csv

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# Various formatting parameters
mpl.rcParams["text.color"] = "#ebdbb2"
mpl.rcParams["xtick.color"] = "#ebdbb2"
mpl.rcParams["ytick.color"] = "#ebdbb2"
mpl.rcParams["axes.labelcolor"] = "#ebdbb2"
mpl.rcParams["axes.facecolor"] = "#1d2021"
mpl.rcParams["figure.facecolor"] = "#1d2021"


def load_data() -> tuple[tuple[str], list[float], list[float]]:
    """Load performance history data from csv

    Returns
    -------
    tuple[tuple[str], list[float], list[float]]
        releases is a tuple of str
        sentence is a list of floats
        word is a list of floats
    """
    with open("train/performance_history.csv", "r") as f:
        reader = csv.reader(f)
        # Skip first row because it contains column headings
        data = list(reader)[1:]

    releases, sentence, word = zip(*data)
    sentence = [float(s) for s in sentence]
    word = [float(w) for w in word]

    return releases, sentence, word


def main():
    """Plot figure and save to docs/source/_static folder"""
    releases, sentence, word = load_data()

    fig, ax = plt.subplots(figsize=(12, 6), layout="constrained")

    x = np.arange(0, 2 * len(releases), 2)  # the label locations
    width = 0.95  # the width of the bars

    offset = 0
    rects = ax.bar(
        x + offset, sentence, width, label="Sentence accuracy", color="#3e686a"
    )
    ax.bar_label(rects, padding=-40, fontsize=12, rotation=90, fmt="%.2f")

    offset = width
    rects = ax.bar(x + offset, word, width, label="Token accuracy", color="#9f4e19")
    ax.bar_label(rects, padding=-40, fontsize=12, rotation=90, fmt="%.2f")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])

    ax.set_ylabel("Accuracy (%)", fontsize=18)
    ax.set_xticks(x + width / 2, releases, fontsize=12, rotation=45)
    ax.legend(loc="upper left", ncols=1, fontsize=16)
    ax.set_ylim(82, 101)
    ax.set_xlim(-0.7, 2 * len(releases) - 0.3)
    fig.savefig("docs/source/_static/diagrams/performance-history.svg")


if __name__ == "__main__":
    main()

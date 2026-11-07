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
mpl.rcParams["axes.facecolor"] = "#32302f"
mpl.rcParams["figure.facecolor"] = "#32302f"


def load_data() -> tuple[tuple[str], list[int]]:
    """Load performance history data from csv

    Returns
    -------
    tuple[tuple[str], list[float]]
        releases is a tuple of str
        sentence_rate is a list of floats
    """
    with open("train/performance_history.csv") as f:
        reader = csv.reader(f)
        # Skip first row because it contains column headings
        data = list(reader)[1:]

    releases, _, _, sentence_rate = zip(*data)
    sentence_rate = [int(r) if r else 0 for r in sentence_rate]

    releases = tuple(
        release if rate > 0 else "-" for release, rate in zip(releases, sentence_rate)
    )

    return releases, sentence_rate


def main():
    """Plot figure and save to docs/source/_static folder"""
    releases, sentence_rate = load_data()

    fig, ax = plt.subplots(figsize=(12, 6), layout="constrained")

    x = np.arange(0, 2 * len(releases), 2)  # the label locations
    width = 0.95  # the width of the bars

    offset = 0.5
    rects = ax.bar(
        x + offset, sentence_rate, width, label="Sentences per second", color="#3e686a"
    )
    ax.bar_label(rects, fontsize=13, rotation=90, fmt="%i")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])

    ax.set_ylabel("Sentences per second", fontsize=18)
    ax.set_xticks(x + width / 2, releases, fontsize=12, rotation=45)
    ax.legend(loc="upper left", ncols=1, fontsize=16)
    ax.set_xlim(-0.7, 2 * len(releases) - 0.3)
    fig.savefig("docs/source/_static/diagrams/execution-performance-history.svg")


if __name__ == "__main__":
    main()

import logging
import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from itertools import chain
from pathlib import Path
from typing import Any, Callable, TextIO

import matplotlib
import numpy as np

matplotlib.use(
    "Agg"
)  # suppress matplotlib gui / headless environment for simple file dump
from matplotlib import pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

logger = logging.getLogger(__name__)


@contextmanager
def change_log_level(level: int) -> Generator[None, None, None]:
    """Context manager to temporarily change logging level within the context.

    On exiting the context, the original level is restored.

    Parameters
    ----------
    level : int
        Logging level to use within context manager.

    Yields
    ------
    Generator[None, None, None]
        Generator, yielding None
    """
    original_level = logger.getEffectiveLevel()
    logger.setLevel(level)
    yield
    logger.setLevel(original_level)


@contextmanager
def set_redirect_log_stream(io_stream: TextIO) -> Generator[None, None, None]:
    """Context manager to accept io_stream for logging used in web app
        Required by web app as it bypasses train.py where logging is configured

    Parameters
    ----------
    io_stream : TextIO
        io.IOString() stream

    Yields
    ------
    Generator[None, None, None]
        Generator, yielding None
    """
    logging.basicConfig(
        stream=io_stream,
        level=logging.INFO,
        format="[%(levelname)s] (%(module)s) %(message)s",
    )

    yield


@contextmanager
def set_temp_working_directory(new_path: Path) -> Generator[None, None, None]:
    """Context manager to temporarily set working directory
       Required by web app when html,tsv training files are dumped

    Parameters
    ----------
    new_path : Path
        Working directory path

    Yields
    ------
    Generator[None, None, None]
        Generator, yielding None
    """
    original_path = os.getcwd()
    os.chdir(new_path)
    try:
        yield
    finally:
        os.chdir(original_path)


def train_model_bypass_logging(func: Callable, *args) -> tuple[float, Any]:
    """Train parser model, suppressing logging.

    Parameters
    ----------
    func :  Callable
        Trainer function to call with given arguments.
    *args :
        train_parser_model function arguments.

    Returns
    -------
    tuple[float, Stats]
        Tuple of elapsed time, evaluation statistics.
    """
    start_time = time.monotonic()
    stats = None
    with change_log_level(
        logging.WARNING
    ):  # Temporarily stop logging below WARNING for multi-processing
        stats = func(*args)
    return time.monotonic() - start_time, stats


def create_confusion_matrix(
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
    labels = sorted(set(flat_truths) | set(flat_predictions))

    cm = confusion_matrix(flat_truths, flat_predictions, labels=labels)
    np.fill_diagonal(cm, -1)
    fig, ax = plt.subplots(figsize=(10, 10))

    fig, ax = plt.subplots(figsize=(10, 10))
    ConfusionMatrixDisplay(cm, display_labels=labels).plot(ax=ax, colorbar=False)
    ax.tick_params(axis="x", labelrotation=45)
    fig.tight_layout()
    fig.savefig(figure_path)
    logger.info("Confusion matrix saved to '%s'.", figure_path)
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
    except (TypeError, ValueError):
        return str(num)

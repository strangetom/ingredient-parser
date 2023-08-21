#!/usr/bin/env python3

import os
import platform
import re
import subprocess
from importlib.resources import as_file, files

from ._constants import UNITS


def pluralise_units(sentence: str) -> str:
    """Pluralise units in the sentence.

    Use the same UNITS dictionary as PreProcessor to make any units in sentence plural

    Parameters
    ----------
    sentence : str
        Input sentence

    Returns
    -------
    str
        Input sentence with any words in the values of UNITS replaced with their plural
        version

    Examples
    --------
    >>> pluralise_units("2 bag")
    '2 bags'

    >>> pluralise_units("13 ounce")
    '13 ounces'

    >>> pluralise_units("1.5 loaf bread")
    '1.5 loaves bread'
    """
    for plural, singular in UNITS.items():
        sentence = re.sub(rf"\b({singular})\b", f"{plural}", sentence)

    return sentence


def show_model_card() -> None:
    """Open model card in default application."""
    with as_file(files(__package__) / "ModelCard.md") as p:
        if platform.system() == "Darwin":  # macOS
            subprocess.call(("open", p))
        elif platform.system() == "Windows":  # Windows
            os.startfile(p)
        else:  # linux variants
            subprocess.call(("xdg-open", p))

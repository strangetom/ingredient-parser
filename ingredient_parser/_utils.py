#!/usr/bin/env python3

import os
import platform
import subprocess
from importlib.resources import as_file, files


def show_model_card() -> None:
    """Open model card in default application."""
    with as_file(files(__package__) / "ModelCard.md") as p:
        if platform.system() == "Darwin":  # macOS
            subprocess.call(("open", p))
        elif platform.system() == "Windows":  # Windows
            os.startfile(p)
        else:  # linux variants
            subprocess.call(("xdg-open", p))

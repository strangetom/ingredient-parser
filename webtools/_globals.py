#!/usr/bin/env python3

import re
from pathlib import Path

# Globals
parent_dir = Path(__file__).parent.parent
NPM_BUILD_DIRECTORY = "build"
SQL3_DATABASE_TABLE = "en"
SQL3_DATABASE = parent_dir / "train/data/training.sqlite3"
MODEL_REQUIREMENTS = parent_dir / "requirements-dev.txt"
RESERVED_LABELLER_SEARCH_CHARS = re.compile(r"\*\*|\~\~|\=\=")  # ** or ~~ or ==
RESERVED_DOTNUM_RANGE_CHARS = re.compile(
    r"^\d*\.?\d*(?<!\.)\.\.(?!\.)\d*\.?\d*$"  # {digit}..{digit}
)

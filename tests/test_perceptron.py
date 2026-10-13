import json
import sqlite3

import pytest
from nltk import pos_tag

from ingredient_parser.perceptron import PerceptronTagger


@pytest.fixture
def load_sentences() -> list[list[str]]:
    """Load tokens for 500 random sentences from training data.

    Returns
    -------
    list[list[str]]
        List of list of tokens.
    """
    sqlite3.register_converter("json", json.loads)
    with sqlite3.connect(
        "train/data/training.sqlite3", detect_types=sqlite3.PARSE_DECLTYPES
    ) as conn:
        c = conn.cursor()
        c.execute("SELECT tokens FROM en ORDER BY RANDOM() LIMIT 500")
        sentences = [toks for (toks,) in c.fetchall()]

    conn.close()
    return sentences


class TestNumpyPerceptronTagger:
    def test_nltk_equivalence(self, load_sentences: list[list[str]]):
        """Test that the NumPy implementation of the PerceptronTagger is equivalent to
        NLTK's pos_tag.

        Parameters
        ----------
        load_sentences : list[list[str]]
            List of list of tokens.
        """
        tagger = PerceptronTagger()
        for tokens in load_sentences:
            assert pos_tag(tokens) == tagger.tag(tokens)

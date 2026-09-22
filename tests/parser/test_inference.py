import logging
from pathlib import Path

import pytest

from ingredient_parser.inference import NumpyCRFInference


class TestNumpyCRFInference:
    def test_model_file_format(self):
        """Test Exception raised if model file is not .json.gz."""
        with pytest.raises(ValueError, match=r"Model must be a .json.gz file."):
            _ = NumpyCRFInference("test/path.json")

    # def test_single_NAME_VAR_label(self, caplog):
    #    """Test debug message is output when the label sequence only contains a single
    #    NAME_VAR group.
    #    """
    #    labels = ["QTY", "UNIT", "NAME_VAR", "B_NAME_TOK", "I_NAME_TOK"]
    #    scores = [0.0] * len(labels)
    #    model = NumpyCRFInference(Path("ingredient_parser/en/data/model.en.json.gz"))
    #    with caplog.at_level(logging.DEBUG):
    #        model._detect_invalid_label_sequence(labels, scores)
    #        assert caplog.record_tuples[-1] == (
    #            "ingredient_parser.inference",
    #            logging.DEBUG,
    #            (
    #                "Invalid label sequence for NAME_VAR label: single NAME_VAR group."
    #                "Parsed names may be incorrect."
    #            ),
    #        )

    def test_single_NAME_VAR_group(self, caplog):
        """Test debug message is output when the label sequence only contains multiple
        NAME_VAR groups, but they aren't separated by PUNC or NAME_SEP.
        """
        labels = ["QTY", "UNIT", "NAME_VAR", "COMMENT", "NAME_VAR", "B_NAME_TOK"]
        scores = [0.0] * len(labels)
        model = NumpyCRFInference(Path("ingredient_parser/en/data/model.en.json.gz"))
        with caplog.at_level(logging.DEBUG):
            model._detect_invalid_label_sequence(labels, scores)
            assert caplog.record_tuples[-1] == (
                "ingredient_parser.inference",
                logging.DEBUG,
                (
                    "Invalid label sequence for NAME_VAR label: NAME_VAR groups not "
                    "separated by NAME_SEP or PUNC. Parsed names may be incorrect."
                ),
            )

    def test_NAME_MOD_with_single_B_NAME_TOK(self, caplog):
        """ """
        labels = ["QTY", "UNIT", "NAME_MOD", "NAME_MOD", "NAME_SEP", "B_NAME_TOK"]
        scores = [0.0] * len(labels)
        model = NumpyCRFInference(Path("ingredient_parser/en/data/model.en.json.gz"))
        with caplog.at_level(logging.DEBUG):
            model._detect_invalid_label_sequence(labels, scores)
            assert caplog.record_tuples[-1] == (
                "ingredient_parser.inference",
                logging.DEBUG,
                (
                    "Invalid label sequence for NAME_MOD label: NAME_MOD is not "
                    "followed by at least 2 NAME_VAR or 2 B_NAME_TOK. "
                    "Parsed names may be incorrect."
                ),
            )

    def test_no_marginals(self):
        """Test that a ValueError is raised when calling .marginals() before labelling a
        sentence.
        """
        model = NumpyCRFInference(Path("ingredient_parser/en/data/model.en.json.gz"))
        with pytest.raises(ValueError, match="Cannot return marginals"):
            model.marginal("QTY", 0)

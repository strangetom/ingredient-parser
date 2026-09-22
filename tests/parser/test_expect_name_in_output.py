from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ingredient_parser import parse_ingredient
from ingredient_parser.en._loaders import load_parser_model
from ingredient_parser.inference import NumpyCRFInference


class Test_expect_name_in_output:
    def test_enabled(self):
        """
        Test that the return name is not []
        """
        sentence = "1 cup, plus 2 tablespoons olive oil"
        tagger = load_parser_model()

        def mock_predict_sequence(features_seq, constrain_transitions=True):
            """
            Mock predict sequence function that always return "COMMENT" for all labels.

            Modify the marginals for the last two tokens so the B_NAME_TOK and
            I_NAME_TOK have lower scores than the COMMENT label, but high enough so that
            guess_ingredient_name would select them if enabled.
            """
            n = len(features_seq)
            labels = ["COMMENT"] * n
            scores = [0.5] * n

            #
            marginals = np.full((n, tagger.model.n_labels), 0.01)
            marginals[n - 2, tagger.model.label_to_idx["B_NAME_TOK"]] = 0.3
            marginals[n - 1, tagger.model.label_to_idx["I_NAME_TOK"]] = 0.2
            tagger.model.marginals = marginals
            return labels, scores

        with patch.object(
            tagger.model, "predict_sequence", side_effect=mock_predict_sequence
        ):
            parsed = parse_ingredient(sentence, expect_name_in_output=True)

        assert parsed.name != []

    def test_disabled(self):
        """
        Test that the returned name is []
        """
        sentence = "1 cup, plus 2 tablespoons olive oil"
        tagger = load_parser_model()

        def mock_predict_sequence(features_seq, constrain_transitions=True):
            """
            Mock predict sequence function that always return "COMMENT" for all labels.

            Modify the marginals for the last two tokens so the B_NAME_TOK and
            I_NAME_TOK have lower scores than the COMMENT label, but high enough so that
            guess_ingredient_name would select them if enabled.
            """
            n = len(features_seq)
            labels = ["COMMENT"] * n
            scores = [0.5] * n

            #
            marginals = np.full((n, tagger.model.n_labels), 0.01)
            marginals[n - 2, tagger.model.label_to_idx["B_NAME_TOK"]] = 0.3
            marginals[n - 1, tagger.model.label_to_idx["I_NAME_TOK"]] = 0.2
            tagger.model.marginals = marginals
            return labels, scores

        with patch.object(
            tagger.model, "predict_sequence", side_effect=mock_predict_sequence
        ):
            parsed = parse_ingredient(sentence, expect_name_in_output=False)

        assert parsed.name == []

    def test_disabled_name_not_separate(self):
        """
        Test that the returned name is [] when not separating names
        """
        sentence = "1 cup, plus 2 tablespoons olive or vegetable oil"
        tagger = load_parser_model()

        def mock_predict_sequence(features_seq, constrain_transitions=True):
            """
            Mock predict sequence function that always return "COMMENT" for all labels.

            Modify the marginals for the last 4 tokens so the B_NAME_TOK, NAME_SEP and
            NAME_VAR have lower scores than the COMMENT label, but high enough so that
            guess_ingredient_name would select them if enabled.
            """
            n = len(features_seq)
            labels = ["COMMENT"] * n
            scores = [0.5] * n

            #
            marginals = np.full((n, tagger.model.n_labels), 0.01)
            marginals[n - 4, tagger.model.label_to_idx["NAME_VAR"]] = 0.17
            marginals[n - 3, tagger.model.label_to_idx["NAME_SEP"]] = 0.25
            marginals[n - 2, tagger.model.label_to_idx["NAME_VAR"]] = 0.3
            marginals[n - 1, tagger.model.label_to_idx["B_NAME_TOK"]] = 0.2
            tagger.model.marginals = marginals
            return labels, scores

        with patch.object(
            tagger.model, "predict_sequence", side_effect=mock_predict_sequence
        ):
            parsed = parse_ingredient(
                sentence, expect_name_in_output=False, separate_names=False
            )

        assert parsed.name == []

    @pytest.mark.model_dependent
    def test_enabled_but_no_name(self):
        """
        Test that the return name is None even though guess_name_fallback is enabled.
        """
        sentence = "2 tablespoons"
        parsed = parse_ingredient(sentence, expect_name_in_output=True)
        assert parsed.name == []


class Test_guess_ingredient_name:
    @patch("ingredient_parser.inference.NumpyCRFInference.load")
    def test_simple(self, mock_load):
        """
        Test that the first COMMENT label gets converted to B_NAME_TOK and the second
        COMMENT label gets converted to I_NAME_TOK.
        """
        # Mock load function so we don't load the real model.
        inference = NumpyCRFInference(model_file=Path("model.json.gz"))

        def mock_marginals_side_effect(label, position):
            """Mocked replacement for NumpyCRFInference.marginals() function."""
            mock_marginals = {
                2: {
                    "B_NAME_TOK": 0.3,
                    "I_NAME_TOK": 0.0,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.05,
                    "NAME_MOD": 0.07,
                },
                3: {
                    "B_NAME_TOK": 0.02,
                    "I_NAME_TOK": 0.35,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.15,
                    "NAME_MOD": 0.02,
                },
            }
            return mock_marginals.get(position, {}).get(label, 0.0)

        inference.marginal = MagicMock(side_effect=mock_marginals_side_effect)

        labels = ["QTY", "UNIT", "COMMENT", "COMMENT"]
        scores = [1.0, 1.0, 0.6, 0.5]

        new_labels, new_scores = inference._guess_ingredient_name(labels, scores)
        assert new_labels == ["QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        assert new_scores == [1.0, 1.0, 0.3, 0.35]

    @patch("ingredient_parser.inference.NumpyCRFInference.load")
    def test_below_threshold(self, mock_load):
        """
        Test that the first COMMENT label gets converted to B_NAME_TOK and the second
        COMMENT label does not get modified because the highest NAME label score does
        not exceed the threshold.
        """
        # Mock load function so we don't load the real model.
        inference = NumpyCRFInference(model_file=Path("model.json.gz"))

        def mock_marginals_side_effect(label, position):
            """Mocked replacement for NumpyCRFInference.marginals() function."""
            mock_marginals = {
                2: {
                    "B_NAME_TOK": 0.3,
                    "I_NAME_TOK": 0.0,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.05,
                    "NAME_MOD": 0.07,
                },
                3: {
                    "B_NAME_TOK": 0.02,
                    "I_NAME_TOK": 0.15,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.15,
                    "NAME_MOD": 0.02,
                },
            }
            return mock_marginals.get(position, {}).get(label, 0.0)

        inference.marginal = MagicMock(side_effect=mock_marginals_side_effect)

        labels = ["QTY", "UNIT", "COMMENT", "COMMENT"]
        scores = [1.0, 1.0, 0.6, 0.5]

        new_labels, new_scores = inference._guess_ingredient_name(labels, scores)
        assert new_labels == ["QTY", "UNIT", "B_NAME_TOK", "COMMENT"]
        assert new_scores == [1.0, 1.0, 0.3, 0.5]

    @patch("ingredient_parser.inference.NumpyCRFInference.load")
    def test_multiple_options(self, mock_load):
        """
        Test that the PREP labels are converted to NAME labels because they are a longer
        sequence of consecutive labels than the two COMMENT labels.
        """
        # Mock load function so we don't load the real model.
        inference = NumpyCRFInference(model_file=Path("model.json.gz"))

        def mock_marginals_side_effect(label, position):
            """Mocked replacement for NumpyCRFInference.marginals() function."""
            mock_marginals = {
                2: {
                    "B_NAME_TOK": 0.3,
                    "I_NAME_TOK": 0.0,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.05,
                    "NAME_MOD": 0.07,
                },
                3: {
                    "B_NAME_TOK": 0.02,
                    "I_NAME_TOK": 0.27,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.15,
                    "NAME_MOD": 0.02,
                },
                5: {
                    "B_NAME_TOK": 0.3,
                    "I_NAME_TOK": 0.0,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.05,
                    "NAME_MOD": 0.07,
                },
                6: {
                    "B_NAME_TOK": 0.02,
                    "I_NAME_TOK": 0.52,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.15,
                    "NAME_MOD": 0.02,
                },
                7: {
                    "B_NAME_TOK": 0.22,
                    "I_NAME_TOK": 0.3,
                    "NAME_SEP": 0.0,
                    "NAME_VAR": 0.05,
                    "NAME_MOD": 0.07,
                },
            }
            return mock_marginals.get(position, {}).get(label, 0.0)

        inference.marginal = MagicMock(side_effect=mock_marginals_side_effect)

        labels = ["QTY", "UNIT", "COMMENT", "COMMENT", "PUNC", "PREP", "PREP", "PREP"]
        scores = [1.0, 1.0, 0.6, 0.5, 1.0, 0.4, 0.45, 0.28]

        new_labels, new_scores = inference._guess_ingredient_name(labels, scores)
        assert new_labels == [
            "QTY",
            "UNIT",
            "COMMENT",
            "COMMENT",
            "PUNC",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "I_NAME_TOK",
        ]
        assert new_scores == [1.0, 1.0, 0.6, 0.5, 1.0, 0.3, 0.52, 0.3]

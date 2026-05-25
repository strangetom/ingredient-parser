from unittest.mock import MagicMock

import pytest

from ingredient_parser import parse_ingredient
from ingredient_parser.en.parser import guess_ingredient_name


class Test_expect_name_in_output:
    @pytest.mark.model_dependent
    def test_enabled(self):
        """
        Test that the return name is not []
        """
        sentence = "1 cup, plus 2 tablespoons olive oil"
        parsed = parse_ingredient(sentence, expect_name_in_output=True)
        assert parsed.name != []

    @pytest.mark.model_dependent
    def test_disabled(self):
        """
        Test that the returned name is []
        """
        sentence = "1 cup, plus 2 tablespoons olive oil"
        parsed = parse_ingredient(sentence, expect_name_in_output=False)
        assert parsed.name == []

    @pytest.mark.model_dependent
    def test_disabled_name_not_separate(self):
        """
        Test that the returned name is [] when not separating names
        """
        sentence = "1 cup, plus 2 tablespoons olive oil"
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
    def test_simple(self):
        """
        Test that the first COMMENT label gets converted to B_NAME_TOK and the second
        COMMENT label gets converted to I_NAME_TOK.
        """
        labels = ["QTY", "UNIT", "COMMENT", "COMMENT"]
        scores = [1.0, 1.0, 0.6, 0.5]

        mock_tagger = MagicMock()
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
        mock_tagger.marginal.side_effect = lambda label, idx: mock_marginals.get(
            idx, {}
        ).get(label, 0.0)

        new_labels, new_scores = guess_ingredient_name(mock_tagger, labels, scores)
        assert new_labels == ["QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        assert new_scores == [1.0, 1.0, 0.3, 0.35]

    def test_below_threshold(self):
        """
        Test that the first COMMENT label gets converted to B_NAME_TOK and the second
        COMMENT label does not get modified because the highest NAME label score does
        not exceed the threshold.
        """
        labels = ["QTY", "UNIT", "COMMENT", "COMMENT"]
        scores = [1.0, 1.0, 0.6, 0.5]

        mock_tagger = MagicMock()
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
        mock_tagger.marginal.side_effect = lambda label, idx: mock_marginals.get(
            idx, {}
        ).get(label, 0.0)

        new_labels, new_scores = guess_ingredient_name(mock_tagger, labels, scores)
        assert new_labels == ["QTY", "UNIT", "B_NAME_TOK", "COMMENT"]
        assert new_scores == [1.0, 1.0, 0.3, 0.5]

    def test_multiple_options(self):
        """
        Test that the PREP labels are converted to NAME labels because they are a longer
        sequence of consecutive labels than the two COMMENT labels.
        """
        labels = ["QTY", "UNIT", "COMMENT", "COMMENT", "PUNC", "PREP", "PREP", "PREP"]
        scores = [1.0, 1.0, 0.6, 0.5, 1.0, 0.4, 0.45, 0.28]

        mock_tagger = MagicMock()
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
        mock_tagger.marginal.side_effect = lambda label, idx: mock_marginals.get(
            idx, {}
        ).get(label, 0.0)

        new_labels, new_scores = guess_ingredient_name(mock_tagger, labels, scores)
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

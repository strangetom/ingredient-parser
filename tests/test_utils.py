import pytest

from ingredient_parser.utils import (
    average,
    find_idx,
    fix_punctuation,
    group_consecutive_idx,
    join_adjacent,
    pluralise_units,
)


class TestUtils_find_idx:
    def test_name(self):
        """
        Returns indices of NAME labels
        """
        input_labels = ["QTY", "UNIT", "NAME", "NAME", "COMMENT", "COMMENT"]
        assert find_idx(input_labels, "NAME") == [2, 3]

    def test_comment(self):
        """
        Returns indices of COMMENT labels
        """
        input_labels = ["QTY", "UNIT", "NAME", "NAME", "COMMENT", "COMMENT"]
        assert find_idx(input_labels, "COMMENT") == [4, 5]

    def test_qty(self):
        """
        Returns indices of QTY labels
        """
        input_labels = ["QTY", "UNIT", "NAME", "NAME", "COMMENT", "COMMENT"]
        assert find_idx(input_labels, "QTY") == [0]

    def test_unit(self):
        """
        Returns indices of UNIT labels
        """
        input_labels = ["QTY", "UNIT", "NAME", "NAME", "COMMENT", "COMMENT"]
        assert find_idx(input_labels, "UNIT") == [1]

    def test_other(self):
        """
        Returns indices of OTHER labels
        """
        input_labels = [
            "QTY",
            "UNIT",
            "NAME",
            "NAME",
            "OTHER",
            "COMMENT",
            "COMMENT",
            "OTHER",
        ]
        assert find_idx(input_labels, "OTHER") == [4, 7]

    def test_comment_including_comma(self):
        """
        Returns indices of COMMENT labels, including COMMA
        """
        input_labels = ["QTY", "UNIT", "NAME", "NAME", "COMMA", "COMMENT", "COMMENT"]
        assert find_idx(input_labels, "COMMENT") == [4, 5, 6]


class TestUtils_group_consecutive_indices:
    def test_single_group(self):
        """
        Return single group
        """
        input_indices = [0, 1, 2, 3, 4]
        groups = group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [input_indices]

    def test_multiple_groups(self):
        """
        Return groups of consecutive indices
        """
        input_indices = [0, 1, 2, 4, 5, 6, 8, 9]
        groups = group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [[0, 1, 2], [4, 5, 6], [8, 9]]


class TestUtils_join_adjacent:
    def test_single_group(self):
        """
        Join all input strings into single string
        """
        input_strings = ["a", "b", "c", "d", "e", "f"]
        input_indices = [1, 2, 3, 4]
        assert join_adjacent(input_strings, input_indices) == "b c d e"

    def test_multiple_groups(self):
        """
        Join input strings into two string
        """
        input_strings = ["a", "b", "c", "d", "e", "f"]
        input_indices = [0, 1, 3, 4, 5]
        assert join_adjacent(input_strings, input_indices) == ["a b", "d e f"]

    def test_no_groups(self):
        """
        Return empty string
        """
        input_strings = ["a", "b", "c", "d", "e", "f"]
        input_indices = []
        assert join_adjacent(input_strings, input_indices) == ""


class TestUtils_fix_punctuation:
    def test_opening_paren(self):
        """
        Space following opening parenthesis is removed
        """
        input_sentence = "2 cups ( high quality) bread flour"
        assert fix_punctuation(input_sentence) == "2 cups (high quality) bread flour"

    def test_closing_paren(self):
        """
        Space preceding closing parenthesis is removed
        """
        input_sentence = "2 cups (high quality ) bread flour"
        assert fix_punctuation(input_sentence) == "2 cups (high quality) bread flour"

    def test_comma(self):
        """
        Space preceding comma is removed
        """
        input_sentence = "salt and pepper , to taste"
        assert fix_punctuation(input_sentence) == "salt and pepper, to taste"

    def test_all(self):
        """
        Spaces following opening parenthesis, preceding closing parenthesis,
        preceding comma are removed
        """
        input_sentence = "2 teaspoons ( kosher ) salt , to taste"
        assert fix_punctuation(input_sentence) == "2 teaspoons (kosher) salt, to taste"

    def test_starting_comma(self):
        """
        Leading comma in sentence removed
        """
        input_sentence = ", or to taste"
        assert fix_punctuation(input_sentence) == "or to taste"


class TestUtils_pluralise_units:
    def test_single(self):
        """
        Each singular unit gets pluralised
        """
        assert pluralise_units("teaspoon") == "teaspoons"
        assert pluralise_units("cup") == "cups"
        assert pluralise_units("loaf") == "loaves"
        assert pluralise_units("leaf") == "leaves"
        assert pluralise_units("chunk") == "chunks"
        assert pluralise_units("Box") == "Boxes"
        assert pluralise_units("Wedge") == "Wedges"

    def test_embedded(self):
        """
        The unit embedded in each sentence gets pluralised
        """
        assert pluralise_units("2 tablespoon olive oil") == "2 tablespoons olive oil"
        assert (
            pluralise_units("3 cup (750 milliliter) milk")
            == "3 cups (750 milliliters) milk"
        )


@pytest.fixture
def labels():
    """
    Return labels for testing average function
    """
    return [
        "QTY",
        "UNIT",
        "NAME",
        "NAME",
        "COMMA",
        "COMMENT",
        "COMMENT",
        "COMMENT",
        "COMMENT",
    ]


@pytest.fixture
def scores():
    """
    Return scores for each labels for testing average function
    """
    return [
        0.9995912554903719,
        0.9973499215679792,
        0.9374103977762065,
        0.9144715768558962,
        0.9997843568900641,
        0.9999263435592202,
        0.9995634086142597,
        0.9999196125676765,
        0.9959501880520711,
    ]


class TestUtils_average:
    def test_average_qty(self, labels, scores):
        """
        Average QTY label score
        """
        assert average(labels, scores, "QTY") == 0.9996

    def test_average_unit(self, labels, scores):
        """
        Average UNIT label score
        """
        assert average(labels, scores, "UNIT") == 0.9973

    def test_average_name(self, labels, scores):
        """
        Average NAME label score
        """
        assert average(labels, scores, "NAME") == 0.9259

    def test_average_comment(self, labels, scores):
        """
        Average COMMENT label score
        """
        assert average(labels, scores, "COMMENT") == 0.9988

    def test_average_other(self, labels, scores):
        """
        Average OTHER label score
        """
        assert average(labels, scores, "OTHER") == 0

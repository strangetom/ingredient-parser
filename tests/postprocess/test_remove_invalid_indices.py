import pytest

from ingredient_parser.en import PostProcessor


@pytest.fixture
def p():
    """Define a PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    sentence = "2, 14 ounce cans coconut milk: opened (not chilled)"
    tokens = [
        "2",
        ",",
        "14",
        "ounce",
        "can",
        "coconut",
        "milk",
        ":",
        "opened",
        "(",
        "not",
        "chilled",
        ")",
    ]
    pos_tags = [
        "CD",
        ",",
        "CD",
        "NN",
        "MD",
        "VB",
        "NN",
        ":",
        "VBN",
        "(",
        "RB",
        "VBN",
        ")",
    ]
    labels = [
        "QTY",
        "PUNC",
        "QTY",
        "UNIT",
        "UNIT",
        "NAME",
        "NAME",
        "PUNC",
        "PREP",
        "PUNC",
        "COMMENT",
        "COMMENT",
        "PUNC",
    ]
    scores = [0.0] * len(labels)

    return PostProcessor(sentence, tokens, pos_tags, labels, scores)


class TestPostProcessor_fix_punctuation:
    def test_leading_punctuation(self, p):
        """
        Test index of starting punctuation is removed.
        """
        assert p._remove_invalid_indices([1, 2, 3]) == [2, 3]

    def test_trailing_punctuation(self, p):
        """
        Test index of tailing punctuation is removed.
        """
        assert p._remove_invalid_indices([5, 6, 7]) == [5, 6]

    def test_open_parenthesis(self, p):
        """
        Test index of open parenthesis is removed.
        """
        assert p._remove_invalid_indices([8, 9, 10, 11]) == [8, 10, 11]

    def test_close_parenthesis(self, p):
        """
        Test index of close parenthesis is removed.
        """
        assert p._remove_invalid_indices([10, 11, 12]) == [10, 11]

    def test_valid_parenthesis(self, p):
        """
        Test no indices are removed.
        """
        assert p._remove_invalid_indices([8, 9, 10, 11, 12]) == [8, 9, 10, 11, 12]

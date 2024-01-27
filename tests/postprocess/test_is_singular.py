import pytest

from ingredient_parser import PostProcessor


@pytest.fixture
def p():
    """Define a PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    sentence = "2 14 ounce cans coconut milk"
    tokens = ["2", "14", "ounce", "can", "coconut", "milk"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "NAME", "NAME"]
    scores = [
        0.9991370577083561,
        0.9725378063405858,
        0.9978510889596651,
        0.9922350007952175,
        0.9886087821704076,
        0.9969237827902526,
    ]

    return PostProcessor(sentence, tokens, labels, scores)


class TestPostProcessor_is_singular:
    def test_is_singular(self, p):
        """
        Test that UNIT at index is indicated as singular
        """
        tokens = ["4", "salmon", "fillets", "2", "pounds", "each"]
        labels = ["QTY", "NAME", "NAME", "QTY", "UNIT", "COMMENT"]
        idx = [0, 1, 2, 3, 4, 5]
        assert p._is_singular(4, tokens, labels, idx)
        assert p.consumed == [5]

    def test_is_singular_in_brackets(self, p):
        """
        Test that UNIT at index is indicated as singular
        """
        tokens = ["4", "salmon", "fillets", "2", "pounds", "(", "900", "g", ")", "each"]
        labels = [
            "QTY",
            "NAME",
            "NAME",
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "COMMENT",
            "COMMENT",
        ]
        idx = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert p._is_singular(7, tokens, labels, idx)
        assert p.consumed == [9]

    def test_not_singular(self, p):
        """
        Test that UNIT at index is not indicated as singular
        """
        tokens = ["4", "salmon", "fillets", "2", "pounds", "minimum"]
        labels = ["QTY", "NAME", "NAME", "QTY", "UNIT", "COMMENT"]
        idx = [0, 1, 2, 3, 4, 5]
        assert not p._is_singular(4, tokens, labels, idx)
        assert p.consumed == []

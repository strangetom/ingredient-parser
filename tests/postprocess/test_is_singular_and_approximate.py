import pytest

from ingredient_parser.en import PostProcessor


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


class TestPostProcessor_is_singular_and_approximate:
    def test_is_singular_and_approximate(self, p):
        """
        Test that QTY at index is indicated as approximate and singular
        """
        tokens = ["each", "nearly", "2", "kg"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT"]
        idx = [0, 1, 2, 3]
        assert p._is_singular_and_approximate(2, tokens, labels, idx)
        assert p.consumed == [1, 0]

    def test_not_singular_and_approximate(self, p):
        """
        Test that QTY at index is not indicated as approximate and singular
        """
        tokens = ["both", "about", "2", "kg"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT"]
        idx = [0, 1, 2, 3]
        assert not p._is_singular_and_approximate(2, tokens, labels, idx)
        assert p.consumed == []

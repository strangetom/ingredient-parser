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


class TestPostProcessor_is_approximate:
    def test_is_approximate_about(self, p):
        """
        Test that QTY at index is indicated as approximate
        """
        tokens = ["about", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert p._is_approximate(1, tokens, labels)

    def test_is_approximate_approx(self, p):
        """
        Test that QTY at index is indicated as approximate
        """
        tokens = ["approx.", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert p._is_approximate(1, tokens, labels)

    def test_is_approximate_approximately(self, p):
        """
        Test that QTY at index is indicated as approximate
        """
        tokens = ["approximately", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert p._is_approximate(1, tokens, labels)

    def test_is_approximate_nearly(self, p):
        """
        Test that QTY at index is indicated as approximate
        """
        tokens = ["nearly", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert p._is_approximate(1, tokens, labels)

    def test_not_approximate(self, p):
        """
        Test that QTY at index is not indicated as approximate
        """
        tokens = ["maximum", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert not p._is_approximate(1, tokens, labels)

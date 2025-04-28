import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".")


class TestPreProcessor_identify_fractions:
    def test_less_than_one(self, p):
        """
        The fake fraction 1/2 is replaced with 0.5
        """
        input_sentence = "1/2 cup sugar"
        assert p._identify_fractions(input_sentence) == "#1$2 cup sugar"

    def test_greater_than_one(self, p):
        """
        The fake fraction 3 1/3 is replaced with 3.333
        """
        input_sentence = "1 pound melted butter, about 3 1/3 cups"
        assert (
            p._identify_fractions(input_sentence)
            == "1 pound melted butter, about 3#1$3 cups"
        )

    def test_no_fraction(self, p):
        """
        There is no fake fraction in the input
        """
        input_sentence = "pinch of salt"
        assert p._identify_fractions(input_sentence) == input_sentence

    def test_leading_space(self, p):
        """
        The fake fraction 1/2 is replaced with 0.5
        The input sentence starts with a space
        """
        input_sentence = " 1/2 cup sugar"
        assert p._identify_fractions(input_sentence) == " #1$2 cup sugar"

    def test_vulgar_fraction(self, p):
        """
        The unicode vulgar fraction (using FRACTION SLASH (U+2044)) is
        replaced with 0.5
        """
        input_sentence = "1⁄2 x 20g pack fresh thyme, leaves only"
        assert (
            p._identify_fractions(input_sentence)
            == "#1$2 x 20g pack fresh thyme, leaves only"
        )

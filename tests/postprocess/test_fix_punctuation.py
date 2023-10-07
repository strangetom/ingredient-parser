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


class TestPostProcessor_fix_punctuation:
    def test_leading_comma(self, p):
        """
        Test leading comma and space are removed
        """
        input_sentence = ", finely chopped"
        assert p._fix_punctuation(input_sentence) == "finely chopped"

    def test_trailing_comma(self, p):
        """
        Test trailing comma is removed
        """
        input_sentence = "finely chopped,"
        assert p._fix_punctuation(input_sentence) == "finely chopped"

    def test_space_following_open_parens(self, p):
        """
        Test space following open parenthesis is removed
        """
        input_sentence = "finely chopped ( diced)"
        assert p._fix_punctuation(input_sentence) == "finely chopped (diced)"

    def test_space_leading_close_parens(self, p):
        """
        Test space before close parenthesis is removed
        """
        input_sentence = "finely chopped (diced )"
        assert p._fix_punctuation(input_sentence) == "finely chopped (diced)"

    def test_unpaired_open_parenthesis(self, p):
        """
        Test unpaired open parenthesis is removed
        """
        input_sentence = "finely chopped diced)"
        assert p._fix_punctuation(input_sentence) == "finely chopped diced"

    def test_unpaired_close_parenthesis(self, p):
        """
        Test unpaired close parenthesis is removed
        """
        input_sentence = "finely chopped (diced"
        assert p._fix_punctuation(input_sentence) == "finely chopped diced"

    def test_multiple_unpaired_parentheses(self, p):
        """
        Test unmatched open and unmatched close parentheses are removed, but
        matched pair are kept.
        """
        input_sentence = "finely) (chopped) (diced"
        assert p._fix_punctuation(input_sentence) == "finely (chopped) diced"

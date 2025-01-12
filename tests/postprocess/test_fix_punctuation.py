import pytest

from ingredient_parser.en import PostProcessor


@pytest.fixture
def p():
    """Define a PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    sentence = "2 14 ounce cans coconut milk"
    tokens = ["2", "14", "ounce", "can", "coconut", "milk"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
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

    def test_multiple_space_before_comma(self, p):
        """
        Test space before punctuation in middle of sentence is removed
        """
        input_sentence = "finely chopped , diced"
        assert p._fix_punctuation(input_sentence) == "finely chopped, diced"

    def test_multiple_space_before_semicolon(self, p):
        """
        Test space before punctuation in middle of sentence is removed
        """
        input_sentence = "finely chopped ; diced"
        assert p._fix_punctuation(input_sentence) == "finely chopped; diced"

    def test_space_before_full_stop(self, p):
        """
        Test space before punctuation in middle of sentence is removed
        """
        input_sentence = "finely chopped ."
        assert p._fix_punctuation(input_sentence) == "finely chopped."

    def test_space_before_question_mark(self, p):
        """
        Test space before punctuation in middle of sentence is removed
        """
        input_sentence = "finely chopped !"
        assert p._fix_punctuation(input_sentence) == "finely chopped!"

    def test_space_before_asterisk(self, p):
        """
        Test space before asterisk is removed
        """
        input_sentence = "chopped *"
        assert p._fix_punctuation(input_sentence) == "chopped*"

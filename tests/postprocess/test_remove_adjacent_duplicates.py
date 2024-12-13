import pytest

from ingredient_parser.en import PostProcessor


@pytest.fixture
def p():
    """Define a PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    sentence = "2 14 ounce cans coconut milk"
    tokens = ["2", "14", "ounce", "can", "coconut", "milk"]
    token_labels = ["QTY", "QTY", "UNIT", "UNIT", "NAME", "NAME"]
    name_labels = ["O", "O", "O", "O", "B_NAME", "I_NAME"]
    scores = [
        0.9991370577083561,
        0.9725378063405858,
        0.9978510889596651,
        0.9922350007952175,
        0.9886087821704076,
        0.9969237827902526,
    ]

    return PostProcessor(sentence, tokens, token_labels, name_labels, scores)


class TestPostProcessor_remove_adjacent_duplicates:
    def test_adjacent_duplicate(self, p):
        """
        Test that index of second "finely" is not returned
        """
        input_list = ["finely", "finely", "chopped"]
        assert p._remove_adjacent_duplicates(input_list) == [1, 2]

    def test_non_adjacent_duplicate(self, p):
        """
        Test that index of non-adjacent duplicate is returned
        """
        input_list = ["finely", "chopped", "finely"]
        assert p._remove_adjacent_duplicates(input_list) == [0, 1, 2]

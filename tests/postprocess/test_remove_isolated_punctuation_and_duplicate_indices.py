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


class TestPostProcessor_remove_isolated_punctuation_and_duplicate_indices:
    def test_isolated_punctuation(self, p):
        """
        Test that index of "(" element is not returned
        """
        input_list = ["finely", "(", "chopped"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            2,
        ]

    def test_no_isolated_punctuation(self, p):
        """
        Test all indices are returned
        """
        input_list = ["finely", "chopped", "or", "diced"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            1,
            2,
            3,
        ]

    def test_adjacent_duplicate(self, p):
        """
        Test that index of second "finely" is not returned
        """
        input_list = ["finely", "finely", "chopped"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            2,
        ]

    def test_non_adjacent_duplicate(self, p):
        """
        Test that index of non-adjacent duplicate is returned
        """
        input_list = ["finely", "chopped", "finely"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            1,
            2,
        ]

    def test_isolated_punc_and_duplicates(self, p):
        """
        Test that index of "(" and second "finely" elements are not returned
        """
        input_list = ["finely", "finely", "(", "chopped"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            3,
        ]

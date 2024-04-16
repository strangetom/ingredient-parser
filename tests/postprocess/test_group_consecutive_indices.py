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


class TestPostProcessor_group_consecutive_indices:
    def test_single_group(self, p):
        """
        Return single group
        """
        input_indices = [0, 1, 2, 3, 4]
        groups = p._group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [input_indices]

    def test_multiple_groups(self, p):
        """
        Return groups of consecutive indices
        """
        input_indices = [0, 1, 2, 4, 5, 6, 8, 9]
        groups = p._group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [[0, 1, 2], [4, 5, 6], [8, 9]]

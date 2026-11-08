import pytest

from ingredient_parser.dataclasses import LabelledToken
from ingredient_parser.en import PostProcessor


@pytest.fixture
def p():
    """Define a PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    sentence = "2 14 ounce cans coconut milk"
    tokens = ["2", "14", "ounce", "can", "coconut", "milk"]
    pos_tags = ["CD", "CD", "NN", "MD", "VB", "NN"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
    scores = [
        0.9991370577083561,
        0.9725378063405858,
        0.9978510889596651,
        0.9922350007952175,
        0.9886087821704076,
        0.9969237827902526,
    ]
    labelled_tokens = [
        LabelledToken(
            index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
        )
        for i, (text, tag, label, score) in enumerate(
            zip(tokens, pos_tags, labels, scores)
        )
    ]

    return PostProcessor(sentence, labelled_tokens, custom_units={})


class TestPostProcessor_remove_adjacent_duplicates:
    def test_single_group(self, p):
        """
        Test that indices of all tokens are returned since there's only one group
        """
        input_list = [["mahi", "mahi"]]
        assert p._remove_boundary_duplicates(input_list) == [0, 1]

    def test_cross_boundary_duplicate(self, p):
        """
        Test that only indices [1, 2] are return because the token at index 0 (of the
        flattened list) is a duplicate.
        """
        input_list = [["smoked"], ["smoked", "pork"]]
        assert p._remove_boundary_duplicates(input_list) == [1, 2]

    def test_within_group_duplicate(self, p):
        """
        Test that no indices are removed because the duplicate is within a group.
        """
        input_list = [["hot", "smoked"], ["piri", "piri", "sauce"]]
        assert p._remove_boundary_duplicates(input_list) == [0, 1, 2, 3, 4]

import pytest

from ingredient_parser import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_collapse_ranges:
    def test_no_range(self, p):
        """
        Input sentence is unchanged
        """
        input_sentence = "100-200 g grated cheese"
        assert p._collapse_ranges(input_sentence) == input_sentence

    def test_left_hand_expand(self, p):
        """
        Spaces before hyphen are removed
        """
        input_sentence = "100 -200 g grated cheese"
        assert p._collapse_ranges(input_sentence) == "100-200 g grated cheese"

    def test_right_hand_expand(self, p):
        """
        Spaces after hyphen are removed
        """
        input_sentence = "100-  200 g grated cheese"
        assert p._collapse_ranges(input_sentence) == "100-200 g grated cheese"

    def test_both_sides_expanded(self, p):
        """
        Spaces before and after hyphen are removed
        """
        input_sentence = "100 -  200 g grated cheese"
        assert p._collapse_ranges(input_sentence) == "100-200 g grated cheese"

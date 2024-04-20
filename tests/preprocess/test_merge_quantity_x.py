import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_replace_dupe_units_ranges:
    def test_no_x(self, p):
        """
        Input sentence is unchanged
        """
        input_sentence = "100 g grated cheese"
        assert p._merge_quantity_x(input_sentence) == "100 g grated cheese"

    def test_single_match(self, p):
        """
        "1 x" is replaced with "1x"
        """
        input_sentence = "1 x 390 g jar roasted red peppers"
        assert p._merge_quantity_x(input_sentence) == "1x 390 g jar roasted red peppers"

    def test_two_match(self, p):
        """
        "1 x" is replaced with "1x" and "0.5 x" is replaced with "0.5x"
        """
        input_sentence = "1 x can or 0.5 x large jar tomato paste"
        assert (
            p._merge_quantity_x(input_sentence)
            == "1x can or 0.5x large jar tomato paste"
        )

import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_combine_quantities_split_by_and:
    def test_half(self, p):
        """
        "1 and 1/2" is replaced by 1.5
        """
        input_sentence = "1 and 1/2 tsp salt"
        assert p._combine_quantities_split_by_and(input_sentence) == "1.5 tsp salt"

    def test_quarter(self, p):
        """
        "1 and 1/4" is replaced by 1.25
        """
        input_sentence = "1 and 1/4 tsp salt"
        assert p._combine_quantities_split_by_and(input_sentence) == "1.25 tsp salt"

    def test_three_quarters(self, p):
        """
        "1 and 3/4" is replaced by 1.75
        """
        input_sentence = "1 and 3/4 tsp salt"
        assert p._combine_quantities_split_by_and(input_sentence) == "1.75 tsp salt"

    def test_third(self, p):
        """
        "1 and 1/3" is replaced by 1.333
        """
        input_sentence = "1 and 1/3 tsp salt"
        assert p._combine_quantities_split_by_and(input_sentence) == "1.333 tsp salt"

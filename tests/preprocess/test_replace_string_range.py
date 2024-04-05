import pytest

from ingredient_parser import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_replace_string_range:
    def test_integers(self, p):
        """
        Test range with format <num> or <num> where <num> are integers
        """
        input_sentence = "4 9 or 10 inch flour tortillas"
        assert p._replace_string_range(input_sentence) == "4 9-10 inch flour tortillas"

    def test_decimals(self, p):
        """
        Test range with format <num> or <num> where <num> are decimals
        """
        input_sentence = "1 15.5 or 16 ounce can black beans"
        assert (
            p._replace_string_range(input_sentence) == "1 15.5-16 ounce can black beans"
        )

    def test_decimals_less_than_one(self, p):
        """
        Test range with format <num> or <num> where <num> are decimals
        """
        input_sentence = "0.5 to 0.75 teaspoon hot Hungarian paprika"
        assert (
            p._replace_string_range(input_sentence)
            == "0.5-0.75 teaspoon hot Hungarian paprika"
        )

    def test_hyphens(self, p):
        """
        Test range where the numbers are followed by hyphens
        """
        input_sentence = "1 6- or 7-ounce can of wild salmon"
        assert (
            p._replace_string_range(input_sentence) == "1 6-7-ounce can of wild salmon"
        )

    def test_hyphens_with_spaces(self, p):
        """
        Test range where the numbers are followed by hyphens, where the hyphens are
        surrounded by spaces.
        """
        input_sentence = "1 6 - or 7 - ounce can of wild salmon"
        assert (
            p._replace_string_range(input_sentence)
            == "1 6-7 - ounce can of wild salmon"
        )

    def test_first_starts_with_zero(self, p):
        """
        Test (false) range where the first of the numbers starts with 0
        """
        input_sentence = "Type 00 or 1 flour"
        assert p._replace_string_range(input_sentence) == "Type 00 or 1 flour"

    def test_second_starts_with_zero(self, p):
        """
        Test (false) range where the second of the numbers starts with 0
        """
        input_sentence = "Type 1 or 00 flour"
        assert p._replace_string_range(input_sentence) == "Type 1 or 00 flour"

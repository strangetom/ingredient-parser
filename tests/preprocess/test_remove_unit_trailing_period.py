import pytest

from ingredient_parser import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_remove_unit_trailing_period:
    def test_tsp(self, p):
        """
        "tsps." is replaced by "tsps"
        """
        input_sentence = "2 tsps. ground cinnamon"
        assert (
            p._remove_unit_trailing_period(input_sentence) == "2 tsps ground cinnamon"
        )

    def test_tbsp(self, p):
        """
        "tbsp." is replaced by "tbsp"
        """
        input_sentence = "1 tbsp. tomato sauce"
        assert p._remove_unit_trailing_period(input_sentence) == "1 tbsp tomato sauce"

    def test_lb(self, p):
        """
        "lbs." is replaced by "lbs"
        """
        input_sentence = "3 lbs. minced beef"
        assert p._remove_unit_trailing_period(input_sentence) == "3 lbs minced beef"

    def test_oz(self, p):
        """
        "oz." is replaced by "oz"
        """
        input_sentence = "1 12oz. can chopped tomatoes"
        assert (
            p._remove_unit_trailing_period(input_sentence)
            == "1 12oz can chopped tomatoes"
        )

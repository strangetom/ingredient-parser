import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_split_quantity_and_units:
    def test_basic(self, p):
        """
        A space is inserted between the integer quantity and the unit
        """
        input_sentence = "100g plain flour"
        assert p._split_quantity_and_units(input_sentence) == "100 g plain flour"

    def test_decimal(self, p):
        """
        A space is inserted between the decimal quantity and the unit
        """
        input_sentence = "2.5cups orange juice"
        assert p._split_quantity_and_units(input_sentence) == "2.5 cups orange juice"

    def test_inch(self, p):
        """
        No space is inserted between the quantity and the inches symbol
        """
        input_sentence = '2.5" square chocolate'
        assert p._split_quantity_and_units(input_sentence) == '2.5" square chocolate'

    def test_hyphen_seperator(self, p):
        """
        The hyphen between the quantity and unit is replaced by a space
        """
        input_sentence = "2-pound whole chicken"
        assert p._split_quantity_and_units(input_sentence) == "2 pound whole chicken"

    def test_unit_then_number(self, p):
        """
        A space is inserted between adjacent number and letters
        """
        input_sentence = "2lb1oz cherry tomatoes"
        assert (
            p._split_quantity_and_units(input_sentence) == "2 lb 1 oz cherry tomatoes"
        )

    def test_unit_hyphen_number(self, p):
        """
        A space is inserted between the letter and hyphen, and hyphen and number
        """
        input_sentence = "2lb-1oz cherry tomatoes"
        assert (
            p._split_quantity_and_units(input_sentence) == "2 lb - 1 oz cherry tomatoes"
        )

    def test_non_unit(self, p):
        """
        No space is inserted between 4 and chop, and the hyphen is retained.
        """
        input_sentence = "1 4-chop rack of lamb"
        assert p._split_quantity_and_units(input_sentence) == "1 4-chop rack of lamb"

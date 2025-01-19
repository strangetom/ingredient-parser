import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".")


class TestPreProcessor_replace_dupe_units_ranges:
    def test_no_dupes(self, p):
        """
        Input sentence is unchanged
        """
        input_sentence = "100 g grated cheese"
        assert p._replace_dupe_units_ranges(input_sentence) == "100 g grated cheese"

    def test_no_dupe_range_pattern(self, p):
        """
        Input sentence is unchanged
        """
        input_sentence = "100 g - 20 oz goat's cheese"
        assert (
            p._replace_dupe_units_ranges(input_sentence)
            == "100 g - 20 oz goat's cheese"
        )

    def test_single_match(self, p):
        """
        14 oz - 17 oz is replaced by 14-17 oz
        """
        input_sentence = "400-500 g/14 oz - 17 oz rhubarb"
        assert (
            p._replace_dupe_units_ranges(input_sentence) == "400-500 g/14-17 oz rhubarb"
        )

    def test_two_match(self, p):
        """
        400 g - 500 g is replaced by 400-500 g
        and
        14 oz - 17 oz is replaced by 14-17 oz
        """
        input_sentence = "400 g - 500 g/14 oz - 17 oz rhubarb"
        assert (
            p._replace_dupe_units_ranges(input_sentence) == "400-500 g/14-17 oz rhubarb"
        )

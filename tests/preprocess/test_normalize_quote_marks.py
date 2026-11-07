import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".", custom_units={})


class TestPreProcessor_normalize_quote_marks:
    def test_double_quotes(self, p):
        """
        All double quotes are replaced with "
        """
        assert p._noramlize_quote_marks("1 2” piece ginger") == '1 2" piece ginger'
        assert p._noramlize_quote_marks("1 2“ piece ginger") == '1 2" piece ginger'
        assert p._noramlize_quote_marks("1 2″ piece ginger") == '1 2" piece ginger'

    def test_single_quotes(self, p):
        """
        All single quotes are replaced with '
        """
        assert (
            p._noramlize_quote_marks("3’ length sausage casing")
            == "3' length sausage casing"
        )
        assert (
            p._noramlize_quote_marks("3′ length sausage casing")
            == "3' length sausage casing"
        )

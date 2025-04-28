import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".")


class TestPreProcessor_replace_en_em_dash:
    def test_en_dash(self, p):
        """
        The en-dash is replaced with a hyphen.
        """
        input_sentence = "2 cups flour – white or self-raising"
        assert (
            p._replace_en_em_dash(input_sentence)
            == "2 cups flour - white or self-raising"
        )

    def test_em_dash(self, p):
        """
        The em-dash is replaced with a hyphen.
        """
        input_sentence = "2 cups flour — white or self-raising"
        assert (
            p._replace_en_em_dash(input_sentence)
            == "2 cups flour  -  white or self-raising"
        )

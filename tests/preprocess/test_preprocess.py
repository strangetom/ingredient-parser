import pytest

from ingredient_parser import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor__builtins__:
    def test__str__(self):
        """
        Test PreProcessor __str__
        """
        p = PreProcessor("1/2 cup chicken broth")
        truth = """Pre-processed recipe ingredient sentence
\t    Input: 1/2 cup chicken broth
\t  Cleaned: 0.5 cup chicken broth
\tTokenized: ['0.5', 'cup', 'chicken', 'broth']"""
        assert str(p) == truth

    def test__repr__(self):
        """
        Test PreProessor __repr__
        """
        p = PreProcessor("1/2 cup chicken broth")
        assert repr(p) == 'PreProcessor("1/2 cup chicken broth")'


class TestPreProcessor_normalise:
    def test_normalise(self):
        """
        The sentence is normalised
        """
        input_sentence = "1 to 1 1/2 tbsp. mint sauce"
        p = PreProcessor(input_sentence, defer_pos_tagging=True)
        assert p.sentence == "1-1.5 tbsp mint sauce"

    def test_degree_symbol(self):
        input_sentence = "¼ cup warm water (105°F)"
        p = PreProcessor(input_sentence, defer_pos_tagging=True)
        assert p.tokenized_sentence == [
            "0.25",
            "cup",
            "warm",
            "water",
            "(",
            "105°F",
            ")",
        ]

import pytest

from ingredient_parser import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_singlarise_units:
    def test_embedded(self, p):
        """
        The unit "cups" is replaced with "cup"
        """
        input_sentence = ["2.5", "cups", "beer"]
        tokenised_sentence, indices = p._singlarise_units(input_sentence)
        assert tokenised_sentence == ["2.5", "cup", "beer"]
        assert indices == [1]

    def test_capitalised(self, p):
        """
        The unit "Boxes" is replaced with "Box", with the capitalisation maintained
        """
        input_sentence = ["2.5", "Boxes", "Candy"]
        tokenised_sentence, indices = p._singlarise_units(input_sentence)
        assert tokenised_sentence == ["2.5", "Box", "Candy"]
        assert indices == [1]

    def test_start(self, p):
        """
        The unit "leaves" is replaced with "leaf"
        """
        input_sentence = ["leaves", "of", "basil"]
        tokenised_sentence, indices = p._singlarise_units(input_sentence)
        assert tokenised_sentence == ["leaf", "of", "basil"]
        assert indices == [0]

    def test_start_capitalised(self, p):
        """
        The unit "wedges" is replaced with "wedge", with the capitalisation maintained
        """
        input_sentence = ["Wedges", "of", "lemon"]
        tokenised_sentence, indices = p._singlarise_units(input_sentence)
        assert tokenised_sentence == ["Wedge", "of", "lemon"]
        assert indices == [0]

    def test_multiple_units(self, p):
        """
        The units "tablespoons" and "teaspoons" are replaced with "tablespoon" and
        "teaspoon" respectively
        """
        input_sentence = ["2", "tablespoons", "plus", "2", "teaspoons"]
        tokenised_sentence, indices = p._singlarise_units(input_sentence)
        assert tokenised_sentence == ["2", "tablespoon", "plus", "2", "teaspoon"]
        assert indices == [1, 4]

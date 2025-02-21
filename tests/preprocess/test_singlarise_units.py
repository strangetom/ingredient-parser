import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".")


class TestPreProcessor_singlarise_units:
    def test_embedded(self):
        """
        The unit "cups" is replaced with "cup"
        """
        p = PreProcessor("2.5 cups beer")
        assert [t.text for t in p.tokenized_sentence] == ["2.5", "cup", "beer"]
        assert p.singularised_indices == [1]

    def test_capitalised(self):
        """
        The unit "Boxes" is replaced with "Box", with the capitalisation maintained
        """
        p = PreProcessor("2.5 Boxes Candy")
        assert [t.text for t in p.tokenized_sentence] == ["2.5", "Box", "Candy"]
        assert p.singularised_indices == [1]

    def test_start(self):
        """
        The unit "leaves" is replaced with "leaf"
        """
        p = PreProcessor("leaves of basil")
        assert [t.text for t in p.tokenized_sentence] == ["leaf", "of", "basil"]
        assert p.singularised_indices == [0]

    def test_start_capitalised(self):
        """
        The unit "wedges" is replaced with "wedge", with the capitalisation maintained
        """
        p = PreProcessor("Wedges of lemon")
        assert [t.text for t in p.tokenized_sentence] == ["Wedge", "of", "lemon"]
        assert p.singularised_indices == [0]

    def test_multiple_units(self):
        """
        The units "tablespoons" and "teaspoons" are replaced with "tablespoon" and
        "teaspoon" respectively
        """
        p = PreProcessor("2 tablespoons plus 2 teaspoons")
        assert [t.text for t in p.tokenized_sentence] == [
            "2",
            "tablespoon",
            "plus",
            "2",
            "teaspoon",
        ]
        assert p.singularised_indices == [1, 4]

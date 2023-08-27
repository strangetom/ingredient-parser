import pytest

from ingredient_parser._utils import pluralise_units

'''
class TestUtils_group_consecutive_indices:
    def test_single_group(self):
        """
        Return single group
        """
        input_indices = [0, 1, 2, 3, 4]
        groups = group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [input_indices]

    def test_multiple_groups(self):
        """
        Return groups of consecutive indices
        """
        input_indices = [0, 1, 2, 4, 5, 6, 8, 9]
        groups = group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [[0, 1, 2], [4, 5, 6], [8, 9]]


class TestUtils_fix_punctuation:
    def test_opening_paren(self):
        """
        Space following opening parenthesis is removed
        """
        input_sentence = "2 cups ( high quality) bread flour"
        assert fix_punctuation(input_sentence) == "2 cups (high quality) bread flour"

    def test_closing_paren(self):
        """
        Space preceding closing parenthesis is removed
        """
        input_sentence = "2 cups (high quality ) bread flour"
        assert fix_punctuation(input_sentence) == "2 cups (high quality) bread flour"

    def test_comma(self):
        """
        Space preceding comma is removed
        """
        input_sentence = "salt and pepper , to taste"
        assert fix_punctuation(input_sentence) == "salt and pepper, to taste"

    def test_all(self):
        """
        Spaces following opening parenthesis, preceding closing parenthesis,
        preceding comma are removed
        """
        input_sentence = "2 teaspoons ( kosher ) salt , to taste"
        assert fix_punctuation(input_sentence) == "2 teaspoons (kosher) salt, to taste"

    def test_starting_comma(self):
        """
        Leading comma in sentence removed
        """
        input_sentence = ", or to taste"
        assert fix_punctuation(input_sentence) == "or to taste"
'''


class TestUtils_pluralise_units:
    def test_single(self):
        """
        Each singular unit gets pluralised
        """
        assert pluralise_units("teaspoon") == "teaspoons"
        assert pluralise_units("cup") == "cups"
        assert pluralise_units("loaf") == "loaves"
        assert pluralise_units("leaf") == "leaves"
        assert pluralise_units("chunk") == "chunks"
        assert pluralise_units("Box") == "Boxes"
        assert pluralise_units("Wedge") == "Wedges"

    def test_embedded(self):
        """
        The unit embedded in each sentence gets pluralised
        """
        assert pluralise_units("2 tablespoon olive oil") == "2 tablespoons olive oil"
        assert (
            pluralise_units("3 cup (750 milliliter) milk")
            == "3 cups (750 milliliters) milk"
        )

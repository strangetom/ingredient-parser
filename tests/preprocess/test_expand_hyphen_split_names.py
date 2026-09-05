import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".", custom_units={})


class TestPreProcessor_expand_hyphen_split_names:
    def test_single_hypen_split(self, p):
        """
        Stove- is converted to stove-popped.
        """
        input_sentence = "15 cups hot unsalted stove- or air-popped popcorn"
        assert (
            p._expand_hyphen_split_names(input_sentence)
            == "15 cups hot unsalted stove-popped or air-popped popcorn"
        )

    def test_single_hypen_split_with_apostrophe(self, p):
        """
        sheep's- is converted to sheep's-milk.
        """
        input_sentence = "2 tbsp semi-aged sheep's- or cow's-milk cheese"
        assert (
            p._expand_hyphen_split_names(input_sentence)
            == "2 tbsp semi-aged sheep's-milk or cow's-milk cheese"
        )

    def test_no_hypen_split(self, p):
        """
        Input sentence is unchanged
        """
        input_sentence = "4 tbsp tablespoons good- quality mayonnaise"
        assert (
            p._expand_hyphen_split_names(input_sentence)
            == "4 tbsp tablespoons good- quality mayonnaise"
        )

    def test_multiple_hypen_splits(self, p):
        """
        14 oz - 17 oz is replaced by 14-17 oz
        """
        input_sentence = (
            "1/3 cup peanut- or garlic-flavored stir-fry sauce "
            "or garlic- or ginger-infused oil"
        )
        assert p._expand_hyphen_split_names(input_sentence) == (
            "1/3 cup peanut-flavored or garlic-flavored stir-fry sauce "
            "or garlic-infused or ginger-infused oil"
        )

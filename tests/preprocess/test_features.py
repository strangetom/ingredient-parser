import pytest

from ingredient_parser.en import PreProcessor
from ingredient_parser.en._constants import DIMENSIONS


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".", custom_units={})


class TestPreProcessor_is_unit:
    def test_true(self, p):
        """
        "teaspoon" is a unit
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_unit(1)

    def test_false(self, p):
        """
        "pine" is not a unit
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._is_unit(2)

    def test_ambiguous_unit_clove_is_unit(self, p):
        """
        "teaspoon" is a unit
        """
        input_sentence = "2 garlic cloves"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_unit(2)

    def test_ambiguous_unit_clove_is_unit_capitalised(self, p):
        """
        "teaspoon" is a unit
        """
        input_sentence = "2 Garlic Cloves"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_unit(2)

    def test_ambiguous_unit_clove_is_not_unit(self, p):
        """
        "cloves" is a unit
        """
        input_sentence = "2 cloves"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._is_unit(1)

    def test_ambiguous_unit_clove_is_not_unit_capitalised(self, p):
        """
        "Cloves" is a unit
        """
        input_sentence = "2 Cloves"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._is_unit(1)

    def test_ambiguous_unit_clove_long_range(self, p):
        """
        "clove" is a unit
        """
        input_sentence = "1 head of garlic, about 10 cloves"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_unit(7)

    def test_ambiguous_unit_pound_is_not_unit(self, p):
        """
        "pound" is a unit
        """
        input_sentence = "1 package pound cake"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._is_unit(2)

    def test_ambiguous_unit_pound_is_unit(self, p):
        """
        "pound" is a unit in this instance
        """
        input_sentence = "1 pound cake flour"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_unit(1)


class TestPreProcessor_is_size:
    def test_true(self, p):
        """
        "large" is a size
        """
        input_sentence = "1 large avocado"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_size(1)

    def test_false(self, p):
        """
        "avocado" is a size
        """
        input_sentence = "1 large avocado"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._is_size(2)

    def test_medium_is_size(self, p):
        """
        "medium" is a size
        """
        input_sentence = "1 medium banana"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_size(1)

    def test_medium_is_not_size(self, p):
        """
        "medium" is not a size in the context of "medium-ripe"
        """
        input_sentence = "1 medium ripe banana"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._is_size(1)

    def test_medium_is_size_with_disambiguator(self, p):
        """
        "medium" is a size, despite "ripe" being within the disambiguating window.
        """
        input_sentence = "1 medium banana, ripe"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_size(1)


class TestPreProcessor_is_punc:
    def test_true(self, p):
        """
        "/" is a punctuation mark
        """
        assert p._is_punc("/")

    def test_false(self, p):
        """
        "beer" is not punctuation
        """
        assert not p._is_punc("beer")


class TestPreProcessor_is_inside_parentheses:
    def test_inside(self):
        """
        Token index is inside parens
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_inside_parentheses(5)

    def test_before(self):
        """
        Token index is before parens
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._is_inside_parentheses(2)

    def test_after(self):
        """
        Token index is before parens
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._is_inside_parentheses(7)

    def test_open_parens(self):
        """
        Token index is (
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_inside_parentheses(4)

    def test_close_parens(self):
        """
        Token index is (
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_inside_parentheses(6)

    def test_multiple_parens(self):
        input_sentence = "8-10 teaspoons (10 ml) pine nuts (ground), toasted"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._is_inside_parentheses(3)
        assert not p._is_inside_parentheses(6)
        assert p._is_inside_parentheses(9)


class TestPreProcess_follows_plus:
    def test_no_plus(self):
        """
        No "plus" in input
        """
        input_sentence = "freshly ground black pepper"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._follows_plus(2)

    def test_before_plus(self):
        """
        Token index is before "plus"
        """
        input_sentence = "freshly ground black pepper, plus more to taste"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._follows_plus(1)

    def test_after_plus(self):
        """
        Token index is after "plus"
        """
        input_sentence = "freshly ground black pepper, plus more to taste"
        p = PreProcessor(input_sentence, custom_units={})
        assert p._follows_plus(7)

    def test_index_is_plus(self):
        """
        Token at index is "plus"
        """
        input_sentence = "freshly ground black pepper, plus more to taste"
        p = PreProcessor(input_sentence, custom_units={})
        assert not p._follows_plus(5)

    def test_index_is_plus_and_follows_plus(self):
        """
        Token at index is "plus" and follows another "plus"
        """
        input_sentence = (
            "freshly ground black pepper, plus white pepper, plus more to taste"
        )
        p = PreProcessor(input_sentence, custom_units={})
        assert p._follows_plus(9)


class TestPreProcessor_word_shape:
    def test_word_shape(self, p):
        """
        Test words are transformed into correct shape pattern.
        """
        # Lower case
        assert p._word_shape("pepper") == "xxx"
        # Upper case
        assert p._word_shape("Pepper") == "Xxxx"
        # Accents
        assert p._word_shape("béchamel") == "xxx"
        # Numbers
        assert p._word_shape("2-pound") == "d-xxx"
        # Fraction
        assert p._word_shape("2#1$2") == "d#d$d"
        # Range
        assert p._word_shape("1-2") == "d-d"
        # Punctuation
        assert p._word_shape(",") == ","


class TestPreProccessor_is_dimension:
    def test_full_tokens(self, p):
        """
        Test that tokens in the DIMENSIONS constant return True for the is_dimension
        feature.
        """
        for token in DIMENSIONS:
            assert p._is_dimension(token)

    def test_partial_token(self, p):
        """
        Test that tokens ending with a hyphen followed by a dimension return True
        for the is_dimension feature.

        These cases includes token containing " to indicate inches.
        """
        assert p._is_dimension('2"-long')
        assert p._is_dimension('1"-thick')
        assert p._is_dimension('1/2"-wide')


class TestPreProcessor_ends_with_inch_symbol:
    def test_single_digit(self, p):
        """
        Test that '1"' is detected as ending with inch symbol.
        """
        assert p._ends_with_inch_symbol('1"')

    def test_range(self, p):
        """
        Test that the range '2-3"' is detected as ending with inch symbol.
        """
        assert p._ends_with_inch_symbol('2-3"')

    def test_contains_inch_symbol(self, p):
        """
        Test a token containing an inch symbol, not at the end, returns False.
        """
        assert not p._ends_with_inch_symbol('3"-long')

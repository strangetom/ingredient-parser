import pytest

from ingredient_parser import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_tag_partofspeech:
    """Test overrides for part of speech tagging"""

    def test_range(self, p):
        """
        The token is tagged as "CD"
        """
        assert p._tag_partofspeech(["3-4"]) == ["CD"]


class TestPreProcessor_is_unit:
    def test_true(self, p):
        """
        "glass" is a unit
        """
        assert p._is_unit("glass")

    def test_false(self, p):
        """
        "watt" is not a unit
        """
        assert not p._is_unit("watt")


class TestPreProcessor_is_numeric:
    def test_integer(self, p):
        """
        "1" is numeric
        """
        assert p._is_numeric("1")

    def test_decimal(self, p):
        """
        "2.667" is numeric
        """
        assert p._is_numeric("2.667")

    def test_integer_range(self, p):
        """
        "1-2" is numeric
        """
        assert p._is_numeric("1-2")

    def test_decimal_range(self, p):
        """
        "3.5-5.5" is numeric
        """
        assert p._is_numeric("3.5-5.5")

    def test_mixed_range(self, p):
        """
        "1-1.5" is numeric
        """
        assert p._is_numeric("1-1.5")

    def test_false(self, p):
        """
        "1/2" is not numeric
        """
        assert not p._is_numeric("1/2")

    def test_false_range(self, p):
        """
        "red-wine" is not numeric
        """
        assert not p._is_numeric("red-wine")

    def test_dozen(self, p):
        """
        "dozen" is numeric
        """
        assert p._is_numeric("dozen")


class TestPreProcessor_is_capitalised:
    def test_capitalised(self, p):
        """
        "Cheese" is capitalised
        """
        assert p._is_capitalised("Cheese")

    def test_embeded_capital(self, p):
        """
        "lemon-Zest" is not capitalised
        """
        assert not p._is_capitalised("lemon-Zest")

    def test_no_captials(self, p):
        """
        "sausage" is not capitalised
        """
        assert not p._is_capitalised("sausage")


class TestPreProcessor_is_inside_parentheses:
    def test_inside(self):
        """
        Token index is inside parens
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence)
        assert p._is_inside_parentheses(5)

    def test_before(self):
        """
        Token index is before parens
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence)
        assert not p._is_inside_parentheses(2)

    def test_after(self):
        """
        Token index is before parens
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence)
        assert not p._is_inside_parentheses(7)

    def test_open_parens(self):
        """
        Token index is (
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence)
        assert p._is_inside_parentheses(4)

    def test_close_parens(self):
        """
        Token index is (
        """
        input_sentence = "8-10 teaspoons pine nuts (ground), toasted"
        p = PreProcessor(input_sentence)
        assert p._is_inside_parentheses(6)

    def test_multiple_parens(self):
        input_sentence = "8-10 teaspoons (10 ml) pine nuts (ground), toasted"
        p = PreProcessor(input_sentence)
        assert p._is_inside_parentheses(3)
        assert not p._is_inside_parentheses(6)
        assert p._is_inside_parentheses(9)


class TestPreProcess_follows_plus:
    def test_no_plus(self):
        """
        No "plus" in input
        """
        input_sentence = "freshly ground black pepper"
        p = PreProcessor(input_sentence)
        assert not p._follows_plus(2)

    def test_before_plus(self):
        """
        Token index is before "plus"
        """
        input_sentence = "freshly ground black pepper, plus more to taste"
        p = PreProcessor(input_sentence)
        assert not p._follows_plus(1)

    def test_after_plus(self):
        """
        Token index is after "plus"
        """
        input_sentence = "freshly ground black pepper, plus more to taste"
        p = PreProcessor(input_sentence)
        assert p._follows_plus(7)

    def test_index_is_plus(self):
        """
        Token at index is "plus"
        """
        input_sentence = "freshly ground black pepper, plus more to taste"
        p = PreProcessor(input_sentence)
        assert not p._follows_plus(5)

    def test_index_is_plus_and_follows_plus(self):
        """
        Token at index is "plus" and follows another "plus"
        """
        input_sentence = (
            "freshly ground black pepper, plus white pepper, plus more to taste"
        )
        p = PreProcessor(input_sentence)
        assert p._follows_plus(9)


class TestPreProcess_follows_comma:
    def test_no_comma(self):
        """
        No comma in input
        """
        input_sentence = "freshly ground black pepper"
        p = PreProcessor(input_sentence)
        assert not p._follows_comma(2)

    def test_before_comma(self):
        """
        Token index is before comma
        """
        input_sentence = "freshly ground black pepper, to taste"
        p = PreProcessor(input_sentence)
        assert not p._follows_comma(1)

    def test_after_comma(self):
        """
        Token index is after comma
        """
        input_sentence = "freshly ground black pepper, to taste"
        p = PreProcessor(input_sentence)
        assert p._follows_comma(5)

    def test_index_is_comma(self):
        """
        Token at index is comma
        """
        input_sentence = "freshly ground black pepper, to taste"
        p = PreProcessor(input_sentence)
        assert not p._follows_comma(4)

    def test_index_is_comma_and_follows_comma(self):
        """
        Token at index is comma and follows another comma
        """
        input_sentence = "freshly ground black pepper, or white pepper, to taste"
        p = PreProcessor(input_sentence)
        assert p._follows_comma(8)


class TestPreProcessor_is_ambiguous_unit:
    def test_clove(self, p):
        """
        Clove is indicated as ambiguous unit
        """
        assert p._is_ambiguous_unit("clove")

    def test_leaves(self, p):
        """
        Leaves is indicated as ambiguous unit
        """
        assert p._is_ambiguous_unit("leaves")

    def test_slabs(self, p):
        """
        Clove is indicated as ambiguous unit
        """
        assert p._is_ambiguous_unit("slab")

    def test_wedges(self, p):
        """
        Clove is indicated as ambiguous unit
        """
        assert p._is_ambiguous_unit("wedges")

    def test_cup(self, p):
        """
        Cup is not indicated as ambiguous unit
        """
        assert not p._is_ambiguous_unit("cup")

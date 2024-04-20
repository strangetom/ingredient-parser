import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("", defer_pos_tagging=True)


class TestPreProcessor_replace_unicode_fractions:
    def test_half(self, p):
        """
        The unicode fraction ½ is converted to 1/2
        There is no space between the preceding character and the unicode fraction
        """
        input_sentence = "3½ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3 1/2 potatoes"

    def test_third(self, p):
        """
        The unicode fraction ⅓ is converted to 1/3
        There is no space between the preceding character and the unicode fraction
        """
        input_sentence = "3⅓ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3 1/3 potatoes"

    def test_two_thirds(self, p):
        """
        The unicode fraction ⅔ is converted to 2/3
        There is no space between the preceding character and the unicode fraction
        """
        input_sentence = "3⅔ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3 2/3 potatoes"

    def test_quarter(self, p):
        """
        The unicode fraction ¼ is converted to 1/4
        There is no space between the preceding character and the unicode fraction
        """
        input_sentence = "3¼ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3 1/4 potatoes"

    def test_three_quarters(self, p):
        """
        The unicode fraction ¾ is converted to 3/4
        There is no space between the preceding character and the unicode fraction
        """
        input_sentence = "3¾ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3 3/4 potatoes"

    def test_fifth(self, p):
        """
        The unicode fraction ⅕ is converted to 1/5
        """
        input_sentence = "3 ⅕ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  1/5 potatoes"

    def test_two_fifth(self, p):
        """
        The unicode fraction ⅖ is converted to 2/5
        """
        input_sentence = "3 ⅖ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  2/5 potatoes"

    def test_three_fifth(self, p):
        """
        The unicode fraction ⅗ is converted to 3/5
        """
        input_sentence = "3 ⅗ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  3/5 potatoes"

    def test_four_fifth(self, p):
        """
        The unicode fraction ⅘ is converted to 4/5
        """
        input_sentence = "3 ⅘ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  4/5 potatoes"

    def test_one_sixth(self, p):
        """
        The unicode fraction ⅙ is converted to 1/6
        """
        input_sentence = "3 ⅙ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  1/6 potatoes"

    def test_five_sixths(self, p):
        """
        The unicode fraction ⅚ is converted to 5/6
        """
        input_sentence = "3 ⅚ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  5/6 potatoes"

    def test_one_eighth(self, p):
        """
        The unicode fraction ⅛ is converted to 1/8
        """
        input_sentence = "3 ⅛ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  1/8 potatoes"

    def test_three_eighths(self, p):
        """
        The unicode fraction ⅜ is converted to 3/8
        """
        input_sentence = "3 ⅜ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  3/8 potatoes"

    def test_five_eighths(self, p):
        """
        The unicode fraction ⅝ is converted to 5/8
        """
        input_sentence = "3 ⅝ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  5/8 potatoes"

    def test_seven_eighths(self, p):
        """
        The unicode fraction ⅞ is converted to 7/8
        """
        input_sentence = "3 ⅞ potatoes"
        assert p._replace_unicode_fractions(input_sentence) == "3  7/8 potatoes"

    def test_range(self, p):
        """
        The unicode fractions are converted to fake fractions, but no space hyphen
        is inserted after the hyphen
        """
        input_sentence = "¼-½ teaspoon"
        assert p._replace_unicode_fractions(input_sentence) == " 1/4-1/2 teaspoon"

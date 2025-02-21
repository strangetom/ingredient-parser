import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".")


class TestPreProcessor_replace_html_fractions:
    def test_half(self, p):
        """
        The HTML fraction &frac12; is converted to the unicode symbol ½
        There is no space between the preceding character and the start of the html
        fraction
        """
        input_sentence = "3&frac12; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3½ potatoes"

    def test_one_third(self, p):
        """
        The HTML fraction &frac13; is converted to the unicode symbol ⅓
        There is no space between the preceding character and the start of the html
        fraction
        """
        input_sentence = "3&frac13; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3⅓ potatoes"

    def test_two_thirds(self, p):
        """
        The HTML fraction &frac23; is converted to the unicode symbol ⅔
        There is no space between the preceding character and the start of the html
        fraction
        """
        input_sentence = "3&frac23; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3⅔ potatoes"

    def test_one_quarter(self, p):
        """
        The HTML fraction &frac14; is converted to the unicode symbol ¼
        There is no space between the preceding character and the start of the html
        fraction
        """
        input_sentence = "3&frac14; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3¼ potatoes"

    def test_three_quarters(self, p):
        """
        The HTML fraction &frac34; is converted to the unicode symbol ¾
        There is no space between the preceding character and the start of the html
        fraction
        """
        input_sentence = "3&frac34; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3¾ potatoes"

    def test_fifth(self, p):
        """
        The HTML fraction &frac15; is converted to the unicode symbol ⅕
        """
        input_sentence = "3 &frac15; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅕ potatoes"

    def test_two_fifth(self, p):
        """
        The HTML fraction &frac25; is converted to the unicode symbol ⅖
        """
        input_sentence = "3 &frac25; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅖ potatoes"

    def test_three_fifth(self, p):
        """
        The HTML fraction &frac35; is converted to the unicode symbol ⅗
        """
        input_sentence = "3 &frac35; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅗ potatoes"

    def test_four_fifth(self, p):
        """
        The HTML fraction &frac45; is converted to the unicode symbol ⅘
        """
        input_sentence = "3 &frac45; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅘ potatoes"

    def test_one_sixth(self, p):
        """
        The HTML fraction &frac16; is converted to the unicode symbol ⅙
        """
        input_sentence = "3 &frac16; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅙ potatoes"

    def test_five_sixths(self, p):
        """
        The HTML fraction &frac56; is converted to the unicode symbol ⅚
        """
        input_sentence = "3 &frac56; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅚ potatoes"

    def test_one_eighth(self, p):
        """
        The HTML fraction &frac18; is converted to the unicode symbol ⅛
        """
        input_sentence = "3 &frac18; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅛ potatoes"

    def test_three_eighths(self, p):
        """
        The HTML fraction &frac38; is converted to the unicode symbol ⅜
        """
        input_sentence = "3 &frac38; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅜ potatoes"

    def test_five_eighths(self, p):
        """
        The HTML fraction &frac58; is converted to the unicode symbol ⅝
        """
        input_sentence = "3 &frac58; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅝ potatoes"

    def test_seven_eighths(self, p):
        """
        The HTML fraction &frac78; is converted to the unicode symbol ⅞
        """
        input_sentence = "3 &frac78; potatoes"
        assert p._replace_html_fractions(input_sentence) == "3 ⅞ potatoes"

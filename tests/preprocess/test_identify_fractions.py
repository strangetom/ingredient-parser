import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".", custom_units={})


class TestPreProcessor_identify_fractions:
    def test_less_than_one(self, p):
        """
        The fake fraction 1/2 is replaced with 0.5.
        """
        input_sentence = "1/2 cup sugar"
        assert p._identify_fractions(input_sentence) == "#1$2 cup sugar"

    def test_greater_than_one(self, p):
        """
        The fake fraction 3 1/3 is replaced with 3.333.
        """
        input_sentence = "1 pound melted butter, about 3 1/3 cups"
        assert (
            p._identify_fractions(input_sentence)
            == "1 pound melted butter, about 3#1$3 cups"
        )

    def test_no_fraction(self, p):
        """
        There is no fake fraction in the input.
        """
        input_sentence = "pinch of salt"
        assert p._identify_fractions(input_sentence) == input_sentence

    def test_leading_space(self, p):
        """
        The fake fraction 1/2 is replaced with 0.5.
        The input sentence starts with a space.
        """
        input_sentence = " 1/2 cup sugar"
        assert p._identify_fractions(input_sentence) == " #1$2 cup sugar"

    def test_vulgar_fraction(self, p):
        """
        The unicode vulgar fraction (using FRACTION SLASH (U+2044)) is replaced
        with #1$2.
        """
        input_sentence = "1⁄2 x 20g pack fresh thyme, leaves only"
        assert (
            p._identify_fractions(input_sentence)
            == "#1$2 x 20g pack fresh thyme, leaves only"
        )

    def test_multiple_fractions(self, p):
        """
        The integer and fraction in the prep instructions are not combined.
        """
        input_sentence = "1/2 baguette, cut diagonally into about 1/4-inch slices"
        assert (
            p._identify_fractions(input_sentence)
            == "#1$2 baguette, cut diagonally into about #1$4-inch slices"
        )

    def test_percentage_ratio_lean_grade_beef(self, p):
        """
        Lean-to-fat ratios like 80/20 sum to 100 and are not fractions; the
        slash should be left alone so downstream tokenization splits the ratio
        into its constituent tokens (e.g. ['80', '/', '20']).
        """
        input_sentence = "1 lb 80/20 ground beef"
        assert p._identify_fractions(input_sentence) == "1 lb 80/20 ground beef"

    def test_percentage_ratio_lean_grade_turkey(self, p):
        """
        93/7 (sum=100) is a turkey lean grade, not a fraction.
        """
        input_sentence = "1 lb 93/7 ground turkey"
        assert p._identify_fractions(input_sentence) == "1 lb 93/7 ground turkey"

    def test_percentage_ratio_50_50(self, p):
        """
        Boundary case: 50/50 sums to 100 and is a ratio (e.g. 50/50 blend), not
        the fraction 1.
        """
        input_sentence = "1 lb 50/50 ground beef"
        assert p._identify_fractions(input_sentence) == "1 lb 50/50 ground beef"

    def test_percentage_ratio_99_1(self, p):
        """
        99/1 (sum=100, white-meat-only ground turkey) is a ratio, not a fraction.
        """
        input_sentence = "1 lb 99/1 ground turkey"
        assert p._identify_fractions(input_sentence) == "1 lb 99/1 ground turkey"

    def test_compound_no_space_keeps_fraction_form(self, p):
        """
        Mixed fractions written without a space (e.g. '11/2 teaspoons' meaning
        '1 1/2 teaspoons') don't sum to 100 and are kept as `#X$Y` form to
        match existing corpus behaviour. This is the regression-guard against
        a simpler discriminator (n <= d) that would have broken these rows.
        """
        input_sentence = "11/2 teaspoons sea salt"
        assert p._identify_fractions(input_sentence) == "#11$2 teaspoons sea salt"

    def test_compound_no_space_thirteen_quarters(self, p):
        """
        '13/4 oz' (n+d=17) keeps its `#X$Y` form.
        """
        input_sentence = "50g/13/4oz unsalted butter, cubed"
        assert (
            p._identify_fractions(input_sentence)
            == "50g/#13$4oz unsalted butter, cubed"
        )

    def test_one_over_ninety_nine_documented_edge_case(self, p):
        """
        1/99 sums to 100 and is bypassed under the n+d==100 rule. This trades
        off the rare improper-true-fraction case in favour of catching all
        observed lean-grade ratios; no corpus row uses 1/99 as a true fraction.
        Asserting current behaviour so the trade-off is captured rather than
        implicit.
        """
        input_sentence = "1/99 cup of vinegar"
        assert p._identify_fractions(input_sentence) == "1/99 cup of vinegar"

    def test_ratio_adjacent_to_word_no_space(self, p):
        """
        '80/20ground' (no space between ratio and following word) is still
        matched by the regex and bypassed cleanly.
        """
        input_sentence = "80/20ground beef"
        assert p._identify_fractions(input_sentence) == "80/20ground beef"

    def test_two_digit_denominator_small_numerator(self, p):
        """
        '1/16 inch' has a two-digit denominator. Sums to 17, so it stays a
        fraction. Regression-guard against any future refactor that mistakenly
        rejects fractions with multi-digit denominators.
        """
        input_sentence = "1/16 inch slices"
        assert p._identify_fractions(input_sentence) == "#1$16 inch slices"

    def test_two_digit_denominator_close_to_one(self, p):
        """
        '15/16 inch' has a two-digit denominator and a numerator close to it
        (proper fraction, value just under 1). Sums to 31, so it stays a
        fraction. Regression-guard against any future refactor that narrowed
        the discriminator.
        """
        input_sentence = "15/16 inch thick"
        assert p._identify_fractions(input_sentence) == "#15$16 inch thick"

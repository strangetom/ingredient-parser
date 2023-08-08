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
        truth = """Pre-processed recipe ingedient sentence
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


class TestPreProcessor_replace_string_numbers:
    def test_spaces(self, p):
        """
        The string number, surrounded by spaces, is converted to a numeral
        """
        input_sentence = "Zest of one orange"
        assert p._replace_string_numbers(input_sentence) == "Zest of 1 orange"

    def test_start(self, p):
        """
        The string number, at the start of the sentence and followed by a space,
        is converted to a numeral
        """
        input_sentence = "Half of a lime"
        assert p._replace_string_numbers(input_sentence) == "Half of a lime"

    def test_parens(self, p):
        """
        The string number, at the beginning of a phrase inside parentheses,
        s converted to a numeral
        """
        input_sentence = "2 cups (three 12-ounce bags) frozen raspberries"
        assert (
            p._replace_string_numbers(input_sentence)
            == "2 cups (3 12-ounce bags) frozen raspberries"
        )

    def test_hyphen(self, p):
        """
        The string number, with a hyphen appended without a space,
        is converted to a numeral
        """
        input_sentence = "1 pound potatoes, peeled and cut into five-inch cubes"
        assert (
            p._replace_string_numbers(input_sentence)
            == "1 pound potatoes, peeled and cut into 5-inch cubes"
        )

    def test_substring(self, p):
        """
        The string number, appearing as a substring of another word,
        is not converted to a numeral
        """
        input_sentence = (
            "1 pound skinless, boneless monkfish fillets"  # "one" inside "boneless"
        )
        assert (
            p._replace_string_numbers(input_sentence)
            == "1 pound skinless, boneless monkfish fillets"
        )


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


class TestPreProcessor_replace_fake_fractions:
    def test_less_than_one(self, p):
        """
        The fake fraction 1/2 is replaced with 0.5
        """
        input_sentence = "1/2 cup sugar"
        assert p._replace_fake_fractions(input_sentence) == "0.5 cup sugar"

    def test_greater_than_one(self, p):
        """
        The fake fraction 3 1/3 is replaced with 3.333
        """
        input_sentence = "1 pound melted butter, about 3 1/3 cups"
        assert (
            p._replace_fake_fractions(input_sentence)
            == "1 pound melted butter, about 3.333 cups"
        )

    def test_no_fraction(self, p):
        """
        There is no fake fraction in the input
        """
        input_sentence = "pinch of salt"
        assert p._replace_fake_fractions(input_sentence) == input_sentence

    def test_leading_space(self, p):
        """
        The fake fraction 1/2 is replaced with 0.5
        The input sentence starts with a space
        """
        input_sentence = " 1/2 cup sugar"
        assert p._replace_fake_fractions(input_sentence) == " 0.5 cup sugar"


class TestPreProcessor_split_quantity_and_units:
    def test_basic(self, p):
        """
        A space is inserted between the integer quantity and the unit
        """
        input_sentence = "100g plain flour"
        assert p._split_quantity_and_units(input_sentence) == "100 g plain flour"

    def test_decimal(self, p):
        """
        A space is inserted between the decimal quantity and the unit
        """
        input_sentence = "2.5cups orange juice"
        assert p._split_quantity_and_units(input_sentence) == "2.5 cups orange juice"

    def test_inch(self, p):
        """
        No space is inserted between the quantity and the inches symbol
        """
        input_sentence = '2.5" square chocolate'
        assert p._split_quantity_and_units(input_sentence) == '2.5" square chocolate'


class TestPreProcessor_remove_unit_trailing_period:
    def test_tsp(self, p):
        """
        "tsps." is replaced by "tsps"
        """
        input_sentence = "2 tsps. ground cinnamon"
        assert (
            p._remove_unit_trailing_period(input_sentence) == "2 tsps ground cinnamon"
        )

    def test_tbsp(self, p):
        """
        "tbsp." is replaced by "tbsp"
        """
        input_sentence = "1 tbsp. tomato sauce"
        assert p._remove_unit_trailing_period(input_sentence) == "1 tbsp tomato sauce"

    def test_lb(self, p):
        """
        "lbs." is replaced by "lbs"
        """
        input_sentence = "3 lbs. minced beef"
        assert p._remove_unit_trailing_period(input_sentence) == "3 lbs minced beef"

    def test_oz(self, p):
        """
        "oz." is replaced by "oz"
        """
        input_sentence = "1 12oz. can chopped tomatoes"
        assert (
            p._remove_unit_trailing_period(input_sentence)
            == "1 12oz can chopped tomatoes"
        )


class TestPreProcessor_replace_string_range:
    def test_integers(self, p):
        """
        Test range with format <num> or <num> where <num> are integers
        """
        input_sentence = "4 9 or 10 inch flour tortillas"
        assert p._replace_string_range(input_sentence) == "4 9-10 inch flour tortillas"

    def test_decimals(self, p):
        """
        Test range with format <num> or <num> where <num> are decimals
        """
        input_sentence = "1 15.5 or 16 ounce can black beans"
        assert (
            p._replace_string_range(input_sentence) == "1 15.5-16 ounce can black beans"
        )

    def test_hyphens(self, p):
        """
        Test range where the numbers are followed by hyphens
        """
        input_sentence = "1 6- or 7-ounce can of wild salmon"
        assert (
            p._replace_string_range(input_sentence) == "1 6-7-ounce can of wild salmon"
        )


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


class TestPreProcess_follows_slash:
    def test_no_slash(self):
        """
        No / in input
        """
        input_sentence = "4 cups freshly made Mashed Potatoes"
        p = PreProcessor(input_sentence)
        assert not p._follows_slash(2)

    def test_before_slash(self):
        """
        Token index is before /
        """
        input_sentence = "4 cups/850 g freshly made Mashed Potatoes"
        p = PreProcessor(input_sentence)
        assert not p._follows_slash(1)

    def test_after_slash(self):
        """
        Token index is after "plus"
        """
        input_sentence = "4 cups/850 g freshly made Mashed Potatoes"
        p = PreProcessor(input_sentence)
        assert p._follows_slash(3)

    def test_index_is_slash(self):
        """
        Token at index is "plus"
        """
        input_sentence = "4 cups/850 g freshly made Mashed Potatoes"
        p = PreProcessor(input_sentence)
        assert not p._follows_slash(2)

    def test_index_is_slash_and_follows_slash(self):
        """
        Token at index is "plus" and follows another "plus"
        """
        input_sentence = "4 cups/850 g/30 oz freshly made Mashed Potatoes"
        p = PreProcessor(input_sentence)
        assert p._follows_slash(5)


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


class TestPreProcessor__is_stop_word:
    def test_common(self, p):
        """
        Validate common stop words
        """
        for word in ["of", "in", "the", "or", "and", "a", "an", "at", "by"]:
            assert p._is_stop_word(word)

    def test_false(self, p):
        """
        Test non-stop words
        """
        for word in ["onion", "kg", "pound", "rice", "taste"]:
            assert not p._is_stop_word(word)

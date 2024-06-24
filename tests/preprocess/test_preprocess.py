import pytest

from ingredient_parser.en import PreProcessor


class TestPreProcessor__builtins__:
    def test__str__(self):
        """
        Test PreProcessor __str__
        """
        p = PreProcessor("1/2 cup chicken broth")
        truth = """Pre-processed recipe ingredient sentence
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

    def test_debug_output(self, capsys):
        """
        Test printed debug output
        """
        _ = PreProcessor("1/2 cup chicken broth", show_debug_output=True)
        captured = capsys.readouterr()
        assert (
            captured.out
            == """_replace_en_em_dash: 1/2 cup chicken broth
_replace_string_numbers: 1/2 cup chicken broth
_replace_html_fractions: 1/2 cup chicken broth
_replace_unicode_fractions: 1/2 cup chicken broth
_combine_quantities_split_by_and: 1/2 cup chicken broth
_replace_fake_fractions: 0.5 cup chicken broth
_split_quantity_and_units: 0.5 cup chicken broth
_remove_unit_trailing_period: 0.5 cup chicken broth
_replace_string_range: 0.5 cup chicken broth
_replace_dupe_units_ranges: 0.5 cup chicken broth
_merge_quantity_x: 0.5 cup chicken broth
_collapse_ranges: 0.5 cup chicken broth
"""
        )


def normalise_test_cases() -> list[tuple[str, ...]]:
    """
    Return a list of tuples of input sentences and their normalised form.
    Many of these examples are based on the examples in docstrings for the
    PreProcessor functions.
    """
    return [
        ("&frac12; cup warm water (105°F)", "0.5 cup warm water (105°F)"),
        ("3 1/2 chilis anchos", "3.5 chilis anchos"),
        ("six eggs", "6 eggs"),
        ("thumbnail-size piece ginger", "thumbnail-size piece ginger"),
        (
            "2 cups flour – white or self-raising",
            "2 cups flour - white or self-raising",
        ),
        ("3–4 sirloin steaks", "3-4 sirloin steaks"),
        ("three large onions", "3 large onions"),
        ("twelve bonbons", "12 bonbons"),
        ("1&frac34; cups tomato ketchup", "1.75 cups tomato ketchup"),
        ("1/2 cup icing sugar", "0.5 cup icing sugar"),
        ("2 3/4 pound chickpeas", "2.75 pound chickpeas"),
        ("1 and 1/2 tsp fine grain sea salt", "1.5 tsp fine grain sea salt"),
        ("1 and 1/4 cups dark chocolate morsels", "1.25 cups dark chocolate morsels"),
        ("½ cup icing sugar", "0.5 cup icing sugar"),
        ("3⅓ cups warm water", "3.333 cups warm water"),
        ("¼-½ teaspoon", "0.25-0.5 teaspoon"),
        ("100g green beans", "100 g green beans"),
        ("2-pound red peppers, sliced", "2 pound red peppers, sliced"),
        ("2lb1oz cherry tomatoes", "2 lb 1 oz cherry tomatoes"),
        ("2lb-1oz cherry tomatoes", "2 lb - 1 oz cherry tomatoes"),
        ("1 tsp. garlic powder", "1 tsp garlic powder"),
        ("5 oz. chopped tomatoes", "5 oz chopped tomatoes"),
        ("1 to 2 mashed bananas", "1-2 mashed bananas"),
        ("5- or 6- large apples", "5-6- large apples"),
        ("227 g - 283.5 g/8-10 oz duck breast", "227-283.5 g/8-10 oz duck breast"),
        ("400-500 g/14 oz - 17 oz rhubarb", "400-500 g/14-17 oz rhubarb"),
        ("8 x 450 g/1 lb live lobsters", "8x 450 g/1 lb live lobsters"),
        ("4 x 100 g wild salmon fillet", "4x 100 g wild salmon fillet"),
        (
            "½ - ¾ cup heavy cream, plus extra for brushing the tops of the scones",
            "0.5-0.75 cup heavy cream, plus extra for brushing the tops of the scones",
        ),
    ]


class TestPreProcessor_normalise:
    @pytest.mark.parametrize("testcase", normalise_test_cases())
    def test_normalise(self, testcase):
        """
        Test that each example sentence is normalised correctly
        """
        input_sentence, normalised = testcase
        p = PreProcessor(input_sentence, defer_pos_tagging=True)
        assert p.sentence == normalised


class TestPreProcessor_sentence_features:
    def test(self):
        p = PreProcessor("1/2 cup chicken broth")
        expected = [
            {
                "bias": "",
                "pos": "CD",
                "stem": "!num",
                "is_capitalised": False,
                "is_unit": False,
                "is_punc": False,
                "is_ambiguous": False,
                "is_in_parens": False,
                "is_after_comma": False,
                "is_after_plus": False,
                "word_shape": "!xxx",
                "next_stem": "cup",
                "next_pos": "CD+NN",
                "next_is_capitalised": False,
                "next_is_unit": True,
                "next_is_punc": False,
                "next_is_ambiguous": False,
                "next_is_in_parens": False,
                "next_is_after_comma": False,
                "next_is_after_plus": False,
                "next_word_shape": "xxx",
                "next2_stem": "chicken",
                "next2_pos": "NN+NN+CD",
                "next2_is_capitalised": False,
                "next2_is_unit": False,
                "next2_is_punc": False,
                "next2_is_ambiguous": False,
                "next2_is_in_parens": False,
                "next2_is_after_comma": False,
                "next2_is_after_plus": False,
                "next2_word_shape": "xxxxxxx",
            },
            {
                "bias": "",
                "pos": "NN",
                "stem": "cup",
                "is_capitalised": False,
                "is_unit": True,
                "is_punc": False,
                "is_ambiguous": False,
                "is_in_parens": False,
                "is_after_comma": False,
                "is_after_plus": False,
                "word_shape": "xxx",
                "prev_stem": "!num",
                "prev_pos": "CD+NN",
                "prev_is_capitalised": False,
                "prev_is_unit": False,
                "prev_is_punc": False,
                "prev_is_ambiguous": False,
                "prev_is_in_parens": False,
                "prev_is_after_comma": False,
                "prev_is_after_plus": False,
                "prev_word_shape": "!xxx",
                "next_stem": "chicken",
                "next_pos": "NN+NN",
                "next_is_capitalised": False,
                "next_is_unit": False,
                "next_is_punc": False,
                "next_is_ambiguous": False,
                "next_is_in_parens": False,
                "next_is_after_comma": False,
                "next_is_after_plus": False,
                "next_word_shape": "xxxxxxx",
                "next2_stem": "broth",
                "next2_pos": "NN+NN+NN",
                "next2_is_capitalised": False,
                "next2_is_unit": False,
                "next2_is_punc": False,
                "next2_is_ambiguous": False,
                "next2_is_in_parens": False,
                "next2_is_after_comma": False,
                "next2_is_after_plus": False,
                "next2_word_shape": "xxxxx",
            },
            {
                "bias": "",
                "pos": "NN",
                "stem": "chicken",
                "is_capitalised": False,
                "is_unit": False,
                "is_punc": False,
                "is_ambiguous": False,
                "is_in_parens": False,
                "is_after_comma": False,
                "is_after_plus": False,
                "word_shape": "xxxxxxx",
                "prefix_3": "chi",
                "suffix_3": "ken",
                "prefix_4": "chic",
                "suffix_4": "cken",
                "prefix_5": "chick",
                "suffix_5": "icken",
                "prev_stem": "cup",
                "prev_pos": "NN+NN",
                "prev_is_capitalised": False,
                "prev_is_unit": True,
                "prev_is_punc": False,
                "prev_is_ambiguous": False,
                "prev_is_in_parens": False,
                "prev_is_after_comma": False,
                "prev_is_after_plus": False,
                "prev_word_shape": "xxx",
                "prev2_stem": "!num",
                "prev2_pos": "CD+NN+NN",
                "prev2_is_capitalised": False,
                "prev2_is_unit": False,
                "prev2_is_punc": False,
                "prev2_is_ambiguous": False,
                "prev2_is_in_parens": False,
                "prev2_is_after_comma": False,
                "prev2_is_after_plus": False,
                "prev2_word_shape": "!xxx",
                "next_stem": "broth",
                "next_pos": "NN+NN",
                "next_is_capitalised": False,
                "next_is_unit": False,
                "next_is_punc": False,
                "next_is_ambiguous": False,
                "next_is_in_parens": False,
                "next_is_after_comma": False,
                "next_is_after_plus": False,
                "next_word_shape": "xxxxx",
            },
            {
                "bias": "",
                "pos": "NN",
                "stem": "broth",
                "is_capitalised": False,
                "is_unit": False,
                "is_punc": False,
                "is_ambiguous": False,
                "is_in_parens": False,
                "is_after_comma": False,
                "is_after_plus": False,
                "word_shape": "xxxxx",
                "prefix_3": "bro",
                "suffix_3": "oth",
                "prefix_4": "brot",
                "suffix_4": "roth",
                "prev_stem": "chicken",
                "prev_pos": "NN+NN",
                "prev_is_capitalised": False,
                "prev_is_unit": False,
                "prev_is_punc": False,
                "prev_is_ambiguous": False,
                "prev_is_in_parens": False,
                "prev_is_after_comma": False,
                "prev_is_after_plus": False,
                "prev_word_shape": "xxxxxxx",
                "prev2_stem": "cup",
                "prev2_pos": "NN+NN+NN",
                "prev2_is_capitalised": False,
                "prev2_is_unit": True,
                "prev2_is_punc": False,
                "prev2_is_ambiguous": False,
                "prev2_is_in_parens": False,
                "prev2_is_after_comma": False,
                "prev2_is_after_plus": False,
                "prev2_word_shape": "xxx",
            },
        ]

        assert p.sentence_features() == expected

    def test_defer_pos_tagging(self):
        p = PreProcessor("100g green beans", defer_pos_tagging=True)
        expected = [
            {
                "bias": "",
                "pos": "CD",
                "stem": "!num",
                "is_capitalised": False,
                "is_unit": False,
                "is_punc": False,
                "is_ambiguous": False,
                "is_in_parens": False,
                "is_after_comma": False,
                "is_after_plus": False,
                "word_shape": "!xxx",
                "next_stem": "g",
                "next_pos": "CD+NN",
                "next_is_capitalised": False,
                "next_is_unit": True,
                "next_is_punc": False,
                "next_is_ambiguous": False,
                "next_is_in_parens": False,
                "next_is_after_comma": False,
                "next_is_after_plus": False,
                "next_word_shape": "x",
                "next2_stem": "green",
                "next2_pos": "JJ+NN+CD",
                "next2_is_capitalised": False,
                "next2_is_unit": False,
                "next2_is_punc": False,
                "next2_is_ambiguous": False,
                "next2_is_in_parens": False,
                "next2_is_after_comma": False,
                "next2_is_after_plus": False,
                "next2_word_shape": "xxxxx",
            },
            {
                "bias": "",
                "pos": "NN",
                "stem": "g",
                "is_capitalised": False,
                "is_unit": True,
                "is_punc": False,
                "is_ambiguous": False,
                "is_in_parens": False,
                "is_after_comma": False,
                "is_after_plus": False,
                "word_shape": "x",
                "prev_stem": "!num",
                "prev_pos": "CD+NN",
                "prev_is_capitalised": False,
                "prev_is_unit": False,
                "prev_is_punc": False,
                "prev_is_ambiguous": False,
                "prev_is_in_parens": False,
                "prev_is_after_comma": False,
                "prev_is_after_plus": False,
                "prev_word_shape": "!xxx",
                "next_stem": "green",
                "next_pos": "NN+JJ",
                "next_is_capitalised": False,
                "next_is_unit": False,
                "next_is_punc": False,
                "next_is_ambiguous": False,
                "next_is_in_parens": False,
                "next_is_after_comma": False,
                "next_is_after_plus": False,
                "next_word_shape": "xxxxx",
                "next2_stem": "bean",
                "next2_pos": "NNS+JJ+NN",
                "next2_is_capitalised": False,
                "next2_is_unit": False,
                "next2_is_punc": False,
                "next2_is_ambiguous": False,
                "next2_is_in_parens": False,
                "next2_is_after_comma": False,
                "next2_is_after_plus": False,
                "next2_word_shape": "xxxxx",
            },
            {
                "bias": "",
                "pos": "JJ",
                "stem": "green",
                "is_capitalised": False,
                "is_unit": False,
                "is_punc": False,
                "is_ambiguous": False,
                "is_in_parens": False,
                "is_after_comma": False,
                "is_after_plus": False,
                "word_shape": "xxxxx",
                "prefix_3": "gre",
                "suffix_3": "een",
                "prefix_4": "gree",
                "suffix_4": "reen",
                "prev_stem": "g",
                "prev_pos": "NN+JJ",
                "prev_is_capitalised": False,
                "prev_is_unit": True,
                "prev_is_punc": False,
                "prev_is_ambiguous": False,
                "prev_is_in_parens": False,
                "prev_is_after_comma": False,
                "prev_is_after_plus": False,
                "prev_word_shape": "x",
                "prev2_stem": "!num",
                "prev2_pos": "CD+NN+JJ",
                "prev2_is_capitalised": False,
                "prev2_is_unit": False,
                "prev2_is_punc": False,
                "prev2_is_ambiguous": False,
                "prev2_is_in_parens": False,
                "prev2_is_after_comma": False,
                "prev2_is_after_plus": False,
                "prev2_word_shape": "!xxx",
                "next_stem": "bean",
                "next_pos": "JJ+NNS",
                "next_is_capitalised": False,
                "next_is_unit": False,
                "next_is_punc": False,
                "next_is_ambiguous": False,
                "next_is_in_parens": False,
                "next_is_after_comma": False,
                "next_is_after_plus": False,
                "next_word_shape": "xxxxx",
            },
            {
                "bias": "",
                "pos": "NNS",
                "stem": "bean",
                "token": "beans",
                "is_capitalised": False,
                "is_unit": False,
                "is_punc": False,
                "is_ambiguous": False,
                "is_in_parens": False,
                "is_after_comma": False,
                "is_after_plus": False,
                "word_shape": "xxxxx",
                "prefix_3": "bea",
                "suffix_3": "ans",
                "prefix_4": "bean",
                "suffix_4": "eans",
                "prev_stem": "green",
                "prev_pos": "JJ+NNS",
                "prev_is_capitalised": False,
                "prev_is_unit": False,
                "prev_is_punc": False,
                "prev_is_ambiguous": False,
                "prev_is_in_parens": False,
                "prev_is_after_comma": False,
                "prev_is_after_plus": False,
                "prev_word_shape": "xxxxx",
                "prev2_stem": "g",
                "prev2_pos": "NN+JJ+NNS",
                "prev2_is_capitalised": False,
                "prev2_is_unit": True,
                "prev2_is_punc": False,
                "prev2_is_ambiguous": False,
                "prev2_is_in_parens": False,
                "prev2_is_after_comma": False,
                "prev2_is_after_plus": False,
                "prev2_word_shape": "x",
            },
        ]

        assert p.sentence_features() == expected

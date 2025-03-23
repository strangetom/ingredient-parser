import pytest

from ingredient_parser.en import PreProcessor


class TestPreProcessor__builtins__:
    def test__str__(self):
        """
        Test PreProcessor __str__
        """
        p = PreProcessor("1/2 cup chicken broth")
        truth = """Pre-processed recipe ingredient sentence
\t  Input: 1/2 cup chicken broth
\tCleaned: #1$2 cup chicken broth
\t Tokens: ['#1$2', 'cup', 'chicken', 'broth']"""
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
_replace_html_fractions: 1/2 cup chicken broth
_replace_unicode_fractions: 1/2 cup chicken broth
combine_quantities_split_by_and: 1/2 cup chicken broth
_identify_fractions: #1$2 cup chicken broth
_split_quantity_and_units: #1$2 cup chicken broth
_remove_unit_trailing_period: #1$2 cup chicken broth
replace_string_range: #1$2 cup chicken broth
_replace_dupe_units_ranges: #1$2 cup chicken broth
_merge_quantity_x: #1$2 cup chicken broth
_collapse_ranges: #1$2 cup chicken broth
"""
        )


def normalise_test_cases() -> list[tuple[str, ...]]:
    """
    Return a list of tuples of input sentences and their normalised form.
    Many of these examples are based on the examples in docstrings for the
    PreProcessor functions.
    """
    return [
        ("&frac12; cup warm water (105°F)", "#1$2 cup warm water (105°F)"),
        ("3 1/2 chilis anchos", "3#1$2 chilis anchos"),
        ("six eggs", "six eggs"),
        ("thumbnail-size piece ginger", "thumbnail-size piece ginger"),
        (
            "2 cups flour – white or self-raising",
            "2 cups flour - white or self-raising",
        ),
        ("3–4 sirloin steaks", "3-4 sirloin steaks"),
        ("three large onions", "three large onions"),
        ("twelve bonbons", "twelve bonbons"),
        ("1&frac34; cups tomato ketchup", "1#3$4 cups tomato ketchup"),
        ("1/2 cup icing sugar", "#1$2 cup icing sugar"),
        ("2 3/4 pound chickpeas", "2#3$4 pound chickpeas"),
        ("1 and 1/2 tsp fine grain sea salt", "1#1$2 tsp fine grain sea salt"),
        ("1 and 1/4 cups dark chocolate morsels", "1#1$4 cups dark chocolate morsels"),
        ("½ cup icing sugar", "#1$2 cup icing sugar"),
        ("3⅓ cups warm water", "3#1$3 cups warm water"),
        ("¼-½ teaspoon", "#1$4-#1$2 teaspoon"),
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
            "#1$2-#3$4 cup heavy cream, plus extra for brushing the tops of the scones",
        ),
    ]


class TestPreProcessor_normalise:
    @pytest.mark.parametrize("testcase", normalise_test_cases())
    def test_normalise(self, testcase):
        """
        Test that each example sentence is normalised correctly
        """
        input_sentence, normalised = testcase
        p = PreProcessor(input_sentence)
        assert p.sentence == normalised


class TestPreProcessor_sentence_features:
    def test(self):
        p = PreProcessor("1/2 cup chicken broth")
        expected = [
            {
                "bias": "",
                "sentence_length": 4,
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
                "next_v0": 5.9549036026,
                "next_v1": -10.531491279602,
                "next_v2": -19.489437103271,
                "next_v3": -7.977605342865,
                "next_v4": -4.253613948822,
                "next_v5": 7.081782817841,
                "next_v6": 0.306739658117,
                "next_v7": -8.263548851013,
                "next_v8": -11.808682441711,
                "next_v9": -1.817874312401,
                "next2_stem": "chicken",
                "next2_pos": "CD+NN+NN",
                "next2_is_capitalised": False,
                "next2_is_unit": False,
                "next2_is_punc": False,
                "next2_is_ambiguous": False,
                "next2_is_in_parens": False,
                "next2_is_after_comma": False,
                "next2_is_after_plus": False,
                "next2_word_shape": "xxxxxxx",
                "next3_stem": "broth",
                "next3_pos": "CD+NN+NN+NN",
                "next3_is_capitalised": False,
                "next3_is_unit": False,
                "next3_is_punc": False,
                "next3_is_ambiguous": False,
                "next3_is_in_parens": False,
                "next3_is_after_comma": False,
                "next3_is_after_plus": False,
                "next3_word_shape": "xxxxx",
            },
            {
                "bias": "",
                "sentence_length": 4,
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
                "v0": 5.9549036026,
                "v1": -10.531491279602,
                "v2": -19.489437103271,
                "v3": -7.977605342865,
                "v4": -4.253613948822,
                "v5": 7.081782817841,
                "v6": 0.306739658117,
                "v7": -8.263548851013,
                "v8": -11.808682441711,
                "v9": -1.817874312401,
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
                "next_v0": 2.497377872467,
                "next_v1": -0.221308916807,
                "next_v2": -0.043443627656,
                "next_v3": 2.607257604599,
                "next_v4": -6.800722122192,
                "next_v5": 6.581258773804,
                "next_v6": 5.427773952484,
                "next_v7": -7.604154109955,
                "next_v8": 10.241472244263,
                "next_v9": -1.348885774612,
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
                "sentence_length": 4,
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
                "v0": 2.497377872467,
                "v1": -0.221308916807,
                "v2": -0.043443627656,
                "v3": 2.607257604599,
                "v4": -6.800722122192,
                "v5": 6.581258773804,
                "v6": 5.427773952484,
                "v7": -7.604154109955,
                "v8": 10.241472244263,
                "v9": -1.348885774612,
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
                "prev_v0": 5.9549036026,
                "prev_v1": -10.531491279602,
                "prev_v2": -19.489437103271,
                "prev_v3": -7.977605342865,
                "prev_v4": -4.253613948822,
                "prev_v5": 7.081782817841,
                "prev_v6": 0.306739658117,
                "prev_v7": -8.263548851013,
                "prev_v8": -11.808682441711,
                "prev_v9": -1.817874312401,
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
                "next_v0": -1.002202033997,
                "next_v1": 2.979228496552,
                "next_v2": -3.606381177902,
                "next_v3": 5.614541053772,
                "next_v4": -9.655241012573,
                "next_v5": 11.16535282135,
                "next_v6": 15.829464912415,
                "next_v7": -0.127565592527,
                "next_v8": 7.074352741241,
                "next_v9": -6.181046962738,
            },
            {
                "bias": "",
                "sentence_length": 4,
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
                "v0": -1.002202033997,
                "v1": 2.979228496552,
                "v2": -3.606381177902,
                "v3": 5.614541053772,
                "v4": -9.655241012573,
                "v5": 11.16535282135,
                "v6": 15.829464912415,
                "v7": -0.127565592527,
                "v8": 7.074352741241,
                "v9": -6.181046962738,
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
                "prev_v0": 2.497377872467,
                "prev_v1": -0.221308916807,
                "prev_v2": -0.043443627656,
                "prev_v3": 2.607257604599,
                "prev_v4": -6.800722122192,
                "prev_v5": 6.581258773804,
                "prev_v6": 5.427773952484,
                "prev_v7": -7.604154109955,
                "prev_v8": 10.241472244263,
                "prev_v9": -1.348885774612,
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
                "prev3_stem": "!num",
                "prev3_pos": "CD+NN+NN+NN",
                "prev3_is_capitalised": False,
                "prev3_is_unit": False,
                "prev3_is_punc": False,
                "prev3_is_ambiguous": False,
                "prev3_is_in_parens": False,
                "prev3_is_after_comma": False,
                "prev3_is_after_plus": False,
                "prev3_word_shape": "!xxx",
            },
        ]

        assert p.sentence_features() == expected

import pytest

from ingredient_parser.dataclasses import LabelledToken
from ingredient_parser.en import PostProcessor
from ingredient_parser.en._utils import ingredient_amount_factory


@pytest.fixture
def p():
    """Define a PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    sentence = "2 14 ounce cans coconut milk"
    tokens = ["2", "14", "ounce", "can", "coconut", "milk"]
    pos_tags = ["CD", "CD", "NN", "MD", "VB", "NN"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
    scores = [
        0.9991370577083561,
        0.9725378063405858,
        0.9978510889596651,
        0.9922350007952175,
        0.9886087821704076,
        0.9969237827902526,
    ]
    labelled_tokens = [
        LabelledToken(
            index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
        )
        for i, (text, tag, label, score) in enumerate(
            zip(tokens, pos_tags, labels, scores)
        )
    ]

    return PostProcessor(sentence, labelled_tokens, custom_units={})


class TestPostProcessor_fallback_pattern:
    def test_basic(self, p):
        """
        Test that a single IngredientAmount object with quantity "3" and
        unit "large handfuls" is returned.
        """

        tokens = ["3", "large", "handful", "cherry", "tomatoes"]
        labels = ["QTY", "UNIT", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        plurals = [False, False, True, False, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="3",
                unit="large handful",
                text="3 large handful",
                confidence=0,
                starting_index=0,
            )
        ]

        assert p._fallback_pattern(labelled_tokens) == expected

    def test_imperial(self):
        """
        Test that imperial units are returned for 'cup'
        """
        p = PostProcessor("", [], custom_units={}, volumetric_units_system="imperial")
        tokens = ["About", "2", "cup", "flour"]
        labels = ["COMMENT", "QTY", "UNIT", "B_NAME_TOK"]
        plurals = [False, False, True, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="2",
                unit="cup",
                text="2 cup",
                confidence=0,
                starting_index=1,
                APPROXIMATE=True,
                volumetric_units_system="imperial",
            )
        ]

        assert p._fallback_pattern(labelled_tokens) == expected

    def test_string_units(self):
        """
        Test that the returned unit is 'cups'
        """
        p = PostProcessor("", [], custom_units={}, string_units=True)
        tokens = ["About", "2", "cup", "flour"]
        labels = ["COMMENT", "QTY", "UNIT", "B_NAME_TOK"]
        plurals = [False, False, True, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="2",
                unit="cup",
                text="2 cup",
                confidence=0,
                starting_index=1,
                APPROXIMATE=True,
                string_units=True,
            )
        ]

        assert p._fallback_pattern(labelled_tokens) == expected

    def test_approximate(self, p):
        """
        Test that a single IngredientAmount object with the APPROXIMATE flag set
        is returned
        """
        tokens = ["About", "2", "cup", "flour"]
        labels = ["COMMENT", "QTY", "UNIT", "B_NAME_TOK"]
        plurals = [False, False, True, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="2",
                unit="cup",
                text="2 cup",
                confidence=0,
                starting_index=1,
                APPROXIMATE=True,
            )
        ]

        assert p._fallback_pattern(labelled_tokens) == expected

    def test_singular(self, p):
        """
        Test that a single IngredientAmount object with the SINGULAR flag set
        is returned
        """
        tokens = ["2", "bananas", ",", "4", "ounce", "each"]
        labels = ["QTY", "B_NAME_TOK", "PUNC", "QTY", "UNIT", "COMMENT"]
        plurals = [False, False, False, False, True, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        p.consumed = [0, 1, 2, 3]

        expected = [
            ingredient_amount_factory(
                quantity="2",
                unit="",
                text="2",
                confidence=0,
                starting_index=0,
            ),
            ingredient_amount_factory(
                quantity="4",
                unit="ounce",
                text="4 ounce",
                confidence=0,
                starting_index=3,
                SINGULAR=True,
                APPROXIMATE=False,
            ),
        ]

        assert p._fallback_pattern(labelled_tokens) == expected

    def test_singular_and_approximate(self, p):
        """
        Test that a single IngredientAmount object with the APPROXIMATE and
        SINGULAR flags set is returned
        """
        tokens = ["2", "bananas", ",", "each", "about", "4", "ounce"]
        labels = ["QTY", "B_NAME_TOK", "PUNC", "COMMENT", "COMMENT", "QTY", "UNIT"]
        plurals = [False, False, False, False, False, True, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="2",
                unit="",
                text="2",
                confidence=0,
                starting_index=0,
            ),
            ingredient_amount_factory(
                quantity="4",
                unit="ounce",
                text="4 ounce",
                confidence=0,
                starting_index=5,
                SINGULAR=True,
                APPROXIMATE=True,
            ),
        ]

        assert p._fallback_pattern(labelled_tokens) == expected

    def test_prepared(self, p):
        """
        Test that a single IngredientAmount object with the APPROXIMATE and
        SINGULAR flags set is returned
        """
        tokens = [
            "2",
            "bananas",
            ",",
            "mashed",
            ",",
            "to",
            "yield",
            "1",
            "cup",
            "(",
            "200",
            "g",
            ")",
        ]
        labels = [
            "QTY",
            "B_NAME_TOK",
            "PUNC",
            "PREP",
            "PUNC",
            "COMMENT",
            "COMMENT",
            "QTY",
            "UNIT",
            "PUNC",
            "QTY",
            "UNIT",
            "PUNC",
        ]
        plurals = [
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        ]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="2",
                unit="",
                text="2",
                confidence=0,
                starting_index=0,
            ),
            ingredient_amount_factory(
                quantity="1",
                unit="cup",
                text="1 cup",
                confidence=0,
                starting_index=7,
                PREPARED_INGREDIENT=True,
            ),
            ingredient_amount_factory(
                quantity="200",
                unit="g",
                text="200 g",
                confidence=0,
                starting_index=10,
                PREPARED_INGREDIENT=True,
            ),
        ]

        assert p._fallback_pattern(labelled_tokens) == expected

    def test_dozen(self, p):
        """
        Test that the token "dozen" is combined with the preceding QTY token in a
        single IngredientAmount object.
        """
        tokens = ["2", "dozen", "bananas", ",", "each", "about", "4", "ounce"]
        labels = [
            "QTY",
            "QTY",
            "B_NAME_TOK",
            "PUNC",
            "COMMENT",
            "COMMENT",
            "QTY",
            "UNIT",
        ]
        plurals = [False, False, False, False, False, False, False, True]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="2 dozen",
                unit="",
                text="2 dozen",
                confidence=0,
                starting_index=0,
            ),
            ingredient_amount_factory(
                quantity="4",
                unit="ounce",
                text="4 ounce",
                confidence=0,
                starting_index=6,
                SINGULAR=True,
                APPROXIMATE=True,
            ),
        ]

        assert p._fallback_pattern(labelled_tokens) == expected

    def test_range(self, p):
        """
        Test that the range 1-2 is correctly parsed to set the RANGE flag and
        quantity_max fields in the IngredientAmount object
        """
        tokens = ["1-2", "tablespoon", "local", "honey"]
        labels = ["QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        plurals = [False, True, False, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="1-2",
                unit="tablespoon",
                text="1-2 tablespoon",
                confidence=0,
                starting_index=0,
            ),
        ]

        actual = p._fallback_pattern(labelled_tokens)
        assert actual == expected
        assert actual[0].RANGE
        assert actual[0].quantity == 1
        assert actual[0].quantity_max == 2

    def test_multiplier(self, p):
        """
        Test that the multiplier "1x" is correctly parsed to set the MULTIPLIER
        flag, quantity and quantity_max fields in the IngredientAmount object
        """
        tokens = ["1x", "tin", "condensed", "milk"]
        labels = ["QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        plurals = [False, False, False, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0.0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="1x",
                unit="tin",
                text="1x tin",
                confidence=0,
                starting_index=0,
            ),
        ]

        actual = p._fallback_pattern(labelled_tokens)
        assert actual == expected
        assert actual[0].MULTIPLIER
        assert actual[0].quantity == 1

    def test_implicit_quantity(self, p):
        """
        Test that the amount is given an implicit quantity of 1.
        """
        tokens = ["#1$4", "inch", "piece", "of", "ginger"]
        labels = ["SIZE", "SIZE", "UNIT", "COMMENT", "B_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0, plural=False
            )
            for i, (text, label) in enumerate(zip(tokens, labels))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="1",
                unit="piece",
                text="1 piece",
                confidence=0,
                starting_index=2,
            ),
        ]

        actual = p._fallback_pattern(labelled_tokens)
        assert actual == expected
        assert actual[0].quantity == 1

    def test_no_implicit_quantity_plural(self, p):
        """
        Test that the amount has no quantity because the unit is plural.
        """
        tokens = ["Chervil", "sprig", "(", "optional", ")"]
        labels = ["B_NAME_TOK", "UNIT", "PUNC", "COMMENT", "PUNC"]
        plurals = [False, True, False, False, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="",
                unit="sprigs",
                text="sprigs",
                confidence=0,
                starting_index=1,
            ),
        ]

        actual = p._fallback_pattern(labelled_tokens)
        assert actual == expected
        assert actual[0].quantity == ""

    def test_no_implicit_quantity_multiple_units(self, p):
        """
        Test that the amount has no quantity because the second unit token is plural.
        """
        tokens = ["Thin", "slice", "peach"]
        labels = ["UNIT", "UNIT", "B_NAME_TOK"]
        plurals = [False, True, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="",
                unit="Thin slices",
                text="Thin slices",
                confidence=0,
                starting_index=0,
            ),
        ]

        actual = p._fallback_pattern(labelled_tokens)
        assert actual == expected
        assert actual[0].quantity == ""

    def test_no_implicit_quantity_indefinite_quantifier(self, p):
        """
        Test that the amount has no quantity because the sentence contains an indefinite
        quantifier prior to the unit.
        """
        tokens = ["Several", "sprig", "fresh", "rosemary"]
        labels = ["COMMENT", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        # Note that we've set the plural flag for "sprigs" to False to test the
        # indefinite quantifier behaviour, even through it's actually plural.
        plurals = [False, False, False, False]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag="", label=label, score=0, plural=plural
            )
            for i, (text, label, plural) in enumerate(zip(tokens, labels, plurals))
        ]

        expected = [
            ingredient_amount_factory(
                quantity="",
                unit="sprig",
                text="sprig",
                confidence=0,
                starting_index=1,
            ),
        ]

        actual = p._fallback_pattern(labelled_tokens)
        assert actual == expected
        assert actual[0].quantity == ""

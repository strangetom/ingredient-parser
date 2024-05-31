import pytest

from ingredient_parser.dataclasses import CompositeIngredientAmount
from ingredient_parser.en import PostProcessor
from ingredient_parser.en._utils import ingredient_amount_factory


class TestPostProcessor_composite_amounts_pattern:
    def test_lb_oz_pattern(self):
        """
        Test that the lb-oz pair are returned as a composite amounts
        """
        sentence = "500g/1lb 2oz pecorino romano cheese (or a vegetarian alternative)"
        tokens = [
            "500",
            "g",
            "/",
            "1",
            "lb",
            "2",
            "oz",
            "pecorino",
            "romano",
            "cheese",
            "(",
            "or",
            "a",
            "vegetarian",
            "alternative",
            ")",
        ]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "NAME",
            "NAME",
            "NAME",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="1",
                        unit="lb",
                        text="1 lb",
                        confidence=0,
                        starting_index=3,
                    ),
                    ingredient_amount_factory(
                        quantity="2",
                        unit="oz",
                        text="2 oz",
                        confidence=0,
                        starting_index=5,
                    ),
                ],
                join="",
                subtractive=False,
            ),
        ]

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.amounts == expected.amounts
            assert out.join == expected.join
            assert out.confidence == expected.confidence
            assert out.starting_index == expected.starting_index
            assert out.combined() == expected.combined()

    def test_pint_fl_oz_pattern(self):
        """
        Test that the pint-fl-oz pair are returned as a composite amounts
        """
        sentence = "1.5 litres/2 pints 12¾fl oz water"
        tokens = ["1.5", "litre", "/", "2", "pint", "12.75", "fl", "oz", "water"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
            "NAME",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="2",
                        unit="pint",
                        text="2 pints",
                        confidence=0,
                        starting_index=3,
                    ),
                    ingredient_amount_factory(
                        quantity="12.75",
                        unit="floz",
                        text="12.75 fl oz",
                        confidence=0,
                        starting_index=5,
                    ),
                ],
                join="",
                subtractive=False,
            ),
        ]

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.amounts == expected.amounts
            assert out.join == expected.join
            assert out.confidence == expected.confidence
            assert out.starting_index == expected.starting_index
            assert out.combined() == expected.combined()

    def test_imperial_pint_fl_oz_pattern(self):
        """
        Test that the pint-fl-oz pair are returned as a composite amounts
        in imperial units.
        """
        sentence = "1.5 litres/2 pints 12¾fl oz water"
        tokens = ["1.5", "litre", "/", "2", "pint", "12.75", "fl", "oz", "water"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
            "NAME",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores, imperial_units=True)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="2",
                        unit="pint",
                        text="2 pints",
                        confidence=0,
                        starting_index=3,
                        imperial_units=True,
                    ),
                    ingredient_amount_factory(
                        quantity="12.75",
                        unit="fluid ounce",
                        text="12.75 fl oz",
                        confidence=0,
                        starting_index=5,
                        imperial_units=True,
                    ),
                ],
                join="",
                subtractive=False,
            ),
        ]

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.amounts == expected.amounts
            assert out.join == expected.join
            assert out.confidence == expected.confidence
            assert out.starting_index == expected.starting_index
            assert out.combined() == expected.combined()

    def test_string_pint_fl_oz_pattern(self):
        """
        Test that the pint-fl-oz pair are returned as strings in the units fields
        """
        sentence = "1.5 litres/2 pints 12¾fl oz water"
        tokens = ["1.5", "litre", "/", "2", "pint", "12.75", "fl", "oz", "water"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
            "NAME",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores, string_units=True)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="2",
                        unit="pints",
                        text="2 pints",
                        confidence=0,
                        starting_index=3,
                        string_units=True,
                    ),
                    ingredient_amount_factory(
                        quantity="12.75",
                        unit="fl oz",
                        text="12.75 fl oz",
                        confidence=0,
                        starting_index=5,
                        string_units=True,
                    ),
                ],
                join="",
                subtractive=False,
            ),
        ]

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.amounts == expected.amounts
            assert out.join == expected.join
            assert out.confidence == expected.confidence
            assert out.starting_index == expected.starting_index
            with pytest.raises(TypeError):
                # Can't combine amounts if units are strings
                out.combined()

    def test_plus_pattern(self):
        """
        Test that the amounts either side of "plus" are returned as a composite amounts
        """
        sentence = "1 cup plus 2 tablespoons (about 5 ounces) all-purpose flour"
        tokens = [
            "1",
            "cup",
            "plus",
            "2",
            "tablespoon",
            "(",
            "about",
            "5",
            "ounce",
            ")",
            "all-purpose",
            "flour",
        ]

        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "PUNC",
            "COMMENT",
            "QTY",
            "UNIT",
            "PUNC",
            "NAME",
            "NAME",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="1",
                        unit="cup",
                        text="1 cup",
                        confidence=0,
                        starting_index=0,
                    ),
                    ingredient_amount_factory(
                        quantity="2",
                        unit="tablespoon",
                        text="2 tablespoons",
                        confidence=0,
                        starting_index=3,
                    ),
                ],
                join=" plus ",
                subtractive=False,
            )
        ]

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.amounts == expected.amounts
            assert out.join == expected.join
            assert out.confidence == expected.confidence
            assert out.starting_index == expected.starting_index
            assert out.combined() == expected.combined()

    def test_minus_pattern(self):
        """
        Test that the amounts either side of "minus" are returned as a composite amounts
        """
        sentence = "1 cup minus 2 tablespoons (about 5 ounces) all-purpose flour"
        tokens = [
            "1",
            "cup",
            "minus",
            "2",
            "tablespoon",
            "(",
            "about",
            "5",
            "ounce",
            ")",
            "all-purpose",
            "flour",
        ]

        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "PUNC",
            "COMMENT",
            "QTY",
            "UNIT",
            "PUNC",
            "NAME",
            "NAME",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="1",
                        unit="cup",
                        text="1 cup",
                        confidence=0,
                        starting_index=0,
                    ),
                    ingredient_amount_factory(
                        quantity="2",
                        unit="tablespoon",
                        text="2 tablespoons",
                        confidence=0,
                        starting_index=3,
                    ),
                ],
                join=" minus ",
                subtractive=True,
            )
        ]

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.amounts == expected.amounts
            assert out.join == expected.join
            assert out.confidence == expected.confidence
            assert out.starting_index == expected.starting_index
            assert out.combined() == expected.combined()

    def test_no_pattern(self):
        """
        Test that the no composite amounts are returned if the pattern is not matched
        """
        sentence = "2 pints or  40 fl oz water"
        tokens = ["2", "pint", "or", "40", "fl", "oz", "water"]
        labels = [
            "QTY",
            "UNIT" "COMMENT",
            "QTY",
            "UNIT",
            "UNIT",
            "NAME",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert output == []

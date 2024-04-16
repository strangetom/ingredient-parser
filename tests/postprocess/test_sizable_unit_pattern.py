import pint

from ingredient_parser.dataclasses import (
    IngredientAmount,
)
from ingredient_parser.en import PostProcessor


class TestPostProcessor_sizable_unit_pattern:
    def test_long_pattern(self):
        """
        Test that 4 quantity and unit amounts are returned, with the first
        made up of the first quantity and last unit.
        """
        sentence = "1 28 ounce (400 g / 2 cups) can chickpeas"
        tokens = [
            "1",
            "28",
            "ounce",
            "(",
            "400",
            "g",
            "/",
            "2",
            "cup",
            ")",
            "can",
            "chickpeas",
        ]
        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "COMMENT",
            "UNIT",
            "NAME",
        ]
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            IngredientAmount(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=0
            ),
            IngredientAmount(
                quantity="28",
                unit=pint.Unit("ounces"),
                text="28 ounces",
                confidence=0,
                SINGULAR=True,
                starting_index=1,
            ),
            IngredientAmount(
                quantity="400",
                unit=pint.Unit("g"),
                text="400 g",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
            ),
            IngredientAmount(
                quantity="2",
                unit=pint.Unit("cups"),
                text="2 cups",
                confidence=0,
                starting_index=7,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out._starting_index == expected._starting_index
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

    def test_medium_pattern(self):
        """
        Test that 3 quantity and unit amounts are returned, with the first
        made up of the first quantity and last unit.
        """
        sentence = "1 28 ounce (400 g) can chickpeas"
        tokens = [
            "1",
            "28",
            "ounce",
            "(",
            "400",
            "g",
            ")",
            "can",
            "chickpeas",
        ]
        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "COMMENT",
            "UNIT",
            "NAME",
        ]
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            IngredientAmount(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=0
            ),
            IngredientAmount(
                quantity="28",
                unit=pint.Unit("ounces"),
                text="28 ounces",
                confidence=0,
                starting_index=1,
                SINGULAR=True,
            ),
            IngredientAmount(
                quantity="400",
                unit=pint.Unit("g"),
                text="400 g",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out._starting_index == expected._starting_index
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

    def test_short_pattern(self):
        """
        Test that 4 quantity and unit amounts are returned, with the first
        made up of the first quantity and last unit.
        """
        sentence = "1 28 ounce can chickpeas"
        tokens = [
            "1",
            "28",
            "ounce",
            "can",
            "chickpeas",
        ]
        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
            "NAME",
        ]
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            IngredientAmount(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=0
            ),
            IngredientAmount(
                quantity="28",
                unit=pint.Unit("ounces"),
                text="28 ounces",
                confidence=0,
                starting_index=1,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out._starting_index == expected._starting_index
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

    def test_no_pattern(self):
        """
        Test that None is return if pattern is not matched
        """
        sentence = "400 g chickpeas or black beans"
        tokens = ["400", "g", "chickpeas", "or", "black", "beans"]
        labels = ["QTY", "UNIT", "NAME", "NAME", "NAME", "NAME"]
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        # Don't check scores
        assert p._sizable_unit_pattern(idx, tokens, labels, scores) == []

    def test_mixed_pattern(self):
        """
        Test that 3 quantity and unit amounts are returned, with the first
        made up of the first quantity and last unit.
        """
        sentence = "2 cups or 1 28 ounce can chickpeas"
        tokens = ["2", "cup", "or", "1", "28", "ounce", "can", "chickpeas"]
        labels = ["QTY", "UNIT", "COMMENT", "QTY", "QTY", "UNIT", "UNIT", "NAME"]
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            IngredientAmount(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=3
            ),
            IngredientAmount(
                quantity="28",
                unit=pint.Unit("ounces"),
                text="28 ounces",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out._starting_index == expected._starting_index
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

    def test_mixed_pattern_imperial(self):
        """
        Test that 3 quantity and unit amounts are returned, with the first
        made up of the first quantity and last unit.
        Imperial units should be returned where the US customary and imperial
        units differ.
        """
        sentence = "2 cups or 1 28 ounce can chickpeas"
        tokens = ["2", "cup", "or", "1", "28", "ounce", "can", "chickpeas"]
        labels = ["QTY", "UNIT", "COMMENT", "QTY", "QTY", "UNIT", "UNIT", "NAME"]
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores, imperial_units=True)

        expected = [
            IngredientAmount(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=3
            ),
            IngredientAmount(
                quantity="28",
                unit=pint.Unit("ounces"),
                text="28 ounces",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out._starting_index == expected._starting_index
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

    def test_mixed_pattern_string_units(self):
        """
        Test that 3 quantity and unit amounts are returned, with the first
        made up of the first quantity and last unit.
        Imperial units should be returned where the US customary and imperial
        units differ.
        """
        sentence = "2 cups or 1 28 ounce can chickpeas"
        tokens = ["2", "cup", "or", "1", "28", "ounce", "can", "chickpeas"]
        labels = ["QTY", "UNIT", "COMMENT", "QTY", "QTY", "UNIT", "UNIT", "NAME"]
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores, string_units=True)

        expected = [
            IngredientAmount(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=3
            ),
            IngredientAmount(
                quantity="28",
                unit="ounces",
                text="28 ounces",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out._starting_index == expected._starting_index
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

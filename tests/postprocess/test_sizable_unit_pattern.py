from ingredient_parser import PostProcessor
from ingredient_parser.postprocess import (
    IngredientAmount,
)


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
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            IngredientAmount(quantity="1", unit="can", confidence=0),
            IngredientAmount(quantity="28", unit="ounces", confidence=0, SINGULAR=True),
            IngredientAmount(quantity="400", unit="g", confidence=0, SINGULAR=True),
            IngredientAmount(quantity="2", unit="cups", confidence=0, SINGULAR=True),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
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
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            IngredientAmount(quantity="1", unit="can", confidence=0),
            IngredientAmount(quantity="28", unit="ounces", confidence=0, SINGULAR=True),
            IngredientAmount(quantity="400", unit="g", confidence=0, SINGULAR=True),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
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
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            IngredientAmount(quantity="1", unit="can", confidence=0),
            IngredientAmount(quantity="28", unit="ounces", confidence=0, SINGULAR=True),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
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
        p = PostProcessor(sentence, tokens, labels, scores)

        # Don't check scores
        assert p._sizable_unit_pattern(tokens, labels, scores) == []

    def test_mixed_pattern(self):
        """
        Test that 3 quantity and unit amounts are returned, with the first
        made up of the first quantity and last unit.
        """
        sentence = "2 cups or 1 28 ounce can chickpeas"
        tokens = ["2", "cup", "or", "1", "28", "ounce", "can", "chickpeas"]
        labels = ["QTY", "UNIT", "COMMENT", "QTY", "QTY", "UNIT", "UNIT", "NAME"]
        scores = [0] * len(tokens)
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            IngredientAmount(quantity="1", unit="can", confidence=0),
            IngredientAmount(quantity="28", unit="ounces", confidence=0, SINGULAR=True),
        ]

        # Don't check scores
        output = p._sizable_unit_pattern(tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

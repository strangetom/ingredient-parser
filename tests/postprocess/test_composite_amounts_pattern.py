from ingredient_parser import PostProcessor
from ingredient_parser.postprocess import (
    CompositeIngredientAmount,
    IngredientAmount,
)


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
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    IngredientAmount(
                        quantity="1", unit="lb", confidence=0, starting_index=3
                    ),
                    IngredientAmount(
                        quantity="2", unit="oz", confidence=0, starting_index=5
                    ),
                ],
                join="",
            ),
        ]

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.amounts == expected.amounts
            assert out.join == expected.join
            assert out.confidence == expected.confidence
            assert out._starting_index == expected._starting_index

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
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    IngredientAmount(
                        quantity="2", unit="pints", confidence=0, starting_index=3
                    ),
                    IngredientAmount(
                        quantity="12.75", unit="fl oz", confidence=0, starting_index=5
                    ),
                ],
                join="",
            ),
        ]

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.amounts == expected.amounts
            assert out.join == expected.join
            assert out.confidence == expected.confidence
            assert out._starting_index == expected._starting_index

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
        scores = [0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, labels, scores)

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert output == []

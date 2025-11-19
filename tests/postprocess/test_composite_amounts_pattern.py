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
        pos_tags = [
            "CD",
            "JJ",
            "$",
            "CD",
            "JJ",
            "CD",
            "NN",
            "NN",
            "NN",
            "NN",
            "(",
            "CC",
            "DT",
            "JJ",
            "NN",
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
            "B_NAME_TOK",
            "I_NAME_TOK",
            "I_NAME_TOK",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

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
        pos_tags = ["CD", "JJ", "$", "CD", "NN", "CD", "NN", "NN", "NN"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
            "B_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

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
        pos_tags = ["CD", "JJ", "$", "CD", "NN", "CD", "NN", "NN", "NN"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
            "B_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(
            sentence,
            tokens,
            pos_tags,
            labels,
            scores,
            volumetric_units_system="imperial",
        )

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="2",
                        unit="pint",
                        text="2 pints",
                        confidence=0,
                        starting_index=3,
                        volumetric_units_system="imperial",
                    ),
                    ingredient_amount_factory(
                        quantity="12.75",
                        unit="fluid ounce",
                        text="12.75 fl oz",
                        confidence=0,
                        starting_index=5,
                        volumetric_units_system="imperial",
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
        pos_tags = ["CD", "JJ", "$", "CD", "NN", "CD", "NN", "NN", "NN"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
            "B_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores, string_units=True)

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
        pos_tags = [
            "CD",
            "NN",
            "CC",
            "CD",
            "NN",
            "(",
            "IN",
            "CD",
            "NN",
            ")",
            "JJ",
            "NN",
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
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

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

    def test_plus_punc_pattern(self):
        """
        Test that the amounts either side of "+" are returned as a composite amounts
        """
        sentence = "1 cup + 2 tablespoons (about 5 ounces) all-purpose flour"
        tokens = [
            "1",
            "cup",
            "+",
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
        pos_tags = [
            "CD",
            "NN",
            "VBD",
            "CD",
            "NN",
            "(",
            "IN",
            "CD",
            "NN",
            ")",
            "JJ",
            "NN",
        ]
        labels = [
            "QTY",
            "UNIT",
            "PUNC",
            "QTY",
            "UNIT",
            "PUNC",
            "COMMENT",
            "QTY",
            "UNIT",
            "PUNC",
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

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
                join=" + ",
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

    def test_and_pattern(self):
        """
        Test that the amounts either side of "and" are returned as a composite amounts
        """
        sentence = "1 cup and 2 tablespoons (about 5 ounces) all-purpose flour"
        tokens = [
            "1",
            "cup",
            "and",
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
        pos_tags = [
            "CD",
            "NN",
            "CC",
            "CD",
            "NN",
            "(",
            "IN",
            "CD",
            "NN",
            ")",
            "JJ",
            "NN",
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
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

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
                join=" and ",
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
        pos_tags = [
            "CD",
            "NN",
            "CC",
            "CD",
            "NN",
            "(",
            "IN",
            "CD",
            "NN",
            ")",
            "JJ",
            "NN",
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
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

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
        pos_tags = ["CD", "NN", "CC", "CD", "JJ", "JJ", "NN"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "UNIT",
            "B_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

        # Don't check scores
        output = p._composite_amounts_pattern(idx, tokens, labels, scores)
        assert output == []

    def test_plus_punc_comment_pattern(self):
        """
        Test that the amounts either side of "plus" are returned as a composite amounts
        """
        sentence = "1 cup, plus 2 tablespoons (about 5 ounces) all-purpose flour"
        tokens = [
            "1",
            "cup",
            ",",
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
        pos_tags = [
            "CD",
            "NN",
            ",",
            "CC",
            "CD",
            "NN",
            "(",
            "IN",
            "CD",
            "NN",
            ")",
            "JJ",
            "NN",
        ]
        labels = [
            "QTY",
            "UNIT",
            "PUNC",
            "COMMENT",
            "QTY",
            "UNIT",
            "PUNC",
            "COMMENT",
            "QTY",
            "UNIT",
            "PUNC",
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

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
                        starting_index=4,
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

    def test_approximate_lb_oz_pattern(self):
        """
        Test that the lb-oz pair are returned as a composite amounts marked as
        approximate.
        """
        sentence = "About 1lb 2oz pecorino romano cheese (or a vegetarian alternative)"
        tokens = [
            "About",
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
        pos_tags = [
            "RB",
            "CD",
            "JJ",
            "CD",
            "NN",
            "NN",
            "NN",
            "NN",
            "(",
            "CC",
            "DT",
            "JJ",
            "NN",
            ")",
        ]
        labels = [
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "I_NAME_TOK",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
            "COMMENT",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="1",
                        unit="lb",
                        text="1 lb",
                        confidence=0,
                        starting_index=1,
                        APPROXIMATE=True,
                    ),
                    ingredient_amount_factory(
                        quantity="2",
                        unit="oz",
                        text="2 oz",
                        confidence=0,
                        starting_index=3,
                        APPROXIMATE=True,
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
            for amount in out.amounts:
                assert amount.APPROXIMATE

    def test_singular_lb_oz_pattern(self):
        """
        Test that the lb-oz pair are returned as a composite amounts marked as
        singular.
        """
        sentence = "1lb 2oz each pecorino romano and parmesan cheese"
        tokens = [
            "1",
            "lb",
            "2",
            "oz",
            "each",
            "pecorino",
            "romano",
            "and",
            "parmesan",
            "cheese",
        ]
        pos_tags = ["CD", "JJ", "CD", "IN", "DT", "NN", "NN", "CC", "NN", "NN"]
        labels = [
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "COMMENT",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="1",
                        unit="lb",
                        text="1 lb",
                        confidence=0,
                        starting_index=0,
                        SINGULAR=True,
                    ),
                    ingredient_amount_factory(
                        quantity="2",
                        unit="oz",
                        text="2 oz",
                        confidence=0,
                        starting_index=2,
                        SINGULAR=True,
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
            for amount in out.amounts:
                assert amount.SINGULAR

    def test_singular_and_approximate_lb_oz_pattern(self):
        """
        Test that the lb-oz pair are returned as a composite amounts marked as
        approximate and singular.
        """
        sentence = "2 large butternut squash, each about 1lb 1 oz"
        tokens = [
            "2",
            "large",
            "butternut",
            "squash",
            ",",
            "each",
            "about",
            "1",
            "lb",
            "1",
            "oz",
        ]
        pos_tags = ["CD", "JJ", "NN", "NN", ",", "DT", "RB", "CD", "JJ", "CD", "NN"]
        labels = [
            "QTY",
            "SIZE",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "PUNC",
            "COMMENT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="1",
                        unit="lb",
                        text="1 lb",
                        confidence=0,
                        starting_index=7,
                        APPROXIMATE=True,
                        SINGULAR=True,
                    ),
                    ingredient_amount_factory(
                        quantity="1",
                        unit="oz",
                        text="1 oz",
                        confidence=0,
                        starting_index=9,
                        APPROXIMATE=True,
                        SINGULAR=True,
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
            for amount in out.amounts:
                assert amount.APPROXIMATE
                assert amount.SINGULAR

    def test_prepared_lb_oz_pattern(self):
        """
        Test that the lb-oz pair are returned as a composite amounts marked as
        approximate and singular.
        """
        sentence = "Strained homemade chicken stock, to yield 1 pint 3 fl oz"
        tokens = [
            "Strained",
            "homemade",
            "chicken",
            "stock",
            ",",
            "to",
            "yield",
            "1",
            "pint",
            "3",
            "fl",
            "oz",
        ]

        pos_tags = [
            "VBN",
            "JJ",
            "NN",
            "NN",
            ",",
            "TO",
            "VB",
            "CD",
            "NN",
            "CD",
            "NN",
            "NN",
        ]
        labels = [
            "PREP",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "I_NAME_TOK",
            "PUNC",
            "COMMENT",
            "COMMENT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        scores = [0.0] * len(tokens)
        idx = list(range(len(tokens)))
        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)

        expected = [
            CompositeIngredientAmount(
                amounts=[
                    ingredient_amount_factory(
                        quantity="1",
                        unit="pint",
                        text="1 pint",
                        confidence=0,
                        starting_index=7,
                        PREPARED_INGREDIENT=True,
                    ),
                    ingredient_amount_factory(
                        quantity="3",
                        unit="fl oz",
                        text="3 fl oz",
                        confidence=0,
                        starting_index=9,
                        PREPARED_INGREDIENT=True,
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
            for amount in out.amounts:
                assert amount.PREPARED_INGREDIENT

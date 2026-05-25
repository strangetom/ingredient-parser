from ingredient_parser.dataclasses import LabelledToken
from ingredient_parser.en import PostProcessor
from ingredient_parser.en._utils import ingredient_amount_factory


class TestPostProcessor_sizeable_unit_pattern:
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
        pos_tags = [
            "CD",
            "CD",
            "NN",
            "(",
            "CD",
            "NN",
            "VBD",
            "CD",
            "NN",
            ")",
            "MD",
            "VB",
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
            "B_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(sentence, labelled_tokens, custom_units={})

        expected = [
            ingredient_amount_factory(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=0
            ),
            ingredient_amount_factory(
                quantity="28",
                unit="ounce",
                text="28 ounces",
                confidence=0,
                SINGULAR=True,
                starting_index=1,
            ),
            ingredient_amount_factory(
                quantity="400",
                unit="g",
                text="400 g",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
            ),
            ingredient_amount_factory(
                quantity="2",
                unit="cup",
                text="2 cups",
                confidence=0,
                starting_index=7,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizeable_unit_pattern(labelled_tokens)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out.starting_index == expected.starting_index
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
        pos_tags = ["CD", "CD", "NN", "(", "CD", "NN", ")", "MD", "VB"]
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
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(sentence, labelled_tokens, custom_units={})

        expected = [
            ingredient_amount_factory(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=0
            ),
            ingredient_amount_factory(
                quantity="28",
                unit="ounce",
                text="28 ounces",
                confidence=0,
                starting_index=1,
                SINGULAR=True,
            ),
            ingredient_amount_factory(
                quantity="400",
                unit="g",
                text="400 g",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizeable_unit_pattern(labelled_tokens)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out.starting_index == expected.starting_index
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
        pos_tags = ["CD", "CD", "NN", "MD", "VB"]
        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
            "NAME",
        ]
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(sentence, labelled_tokens, custom_units={})

        expected = [
            ingredient_amount_factory(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=0
            ),
            ingredient_amount_factory(
                quantity="28",
                unit="ounce",
                text="28 ounces",
                confidence=0,
                starting_index=1,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizeable_unit_pattern(labelled_tokens)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out.starting_index == expected.starting_index
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

    def test_no_pattern(self):
        """
        Test that None is return if pattern is not matched
        """
        sentence = "400 g chickpeas or black beans"
        tokens = ["400", "g", "chickpeas", "or", "black", "beans"]
        pos_tags = ["CD", "JJ", "NNS", "CC", "JJ", "NNS"]
        labels = ["QTY", "UNIT", "NAME", "NAME", "NAME", "NAME"]
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(sentence, labelled_tokens, custom_units={})

        # Don't check scores
        assert p._sizeable_unit_pattern(labelled_tokens) == []

    def test_mixed_pattern(self):
        """
        Test that 3 quantity and unit amounts are returned, with the first
        made up of the first quantity and last unit.
        """
        sentence = "2 cups or 1 28 ounce can chickpeas"
        tokens = ["2", "cup", "or", "1", "28", "ounce", "can", "chickpeas"]
        pos_tags = ["CD", "NN", "CC", "CD", "CD", "NN", "MD", "VB"]
        labels = ["QTY", "UNIT", "COMMENT", "QTY", "QTY", "UNIT", "UNIT", "NAME"]
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(sentence, labelled_tokens, custom_units={})

        expected = [
            ingredient_amount_factory(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=3
            ),
            ingredient_amount_factory(
                quantity="28",
                unit="ounce",
                text="28 ounces",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
            ),
        ]

        # Don't check scores
        output = p._sizeable_unit_pattern(labelled_tokens)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out.starting_index == expected.starting_index
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
        pos_tags = ["CD", "NN", "CC", "CD", "CD", "NN", "MD", "VB"]
        labels = ["QTY", "UNIT", "COMMENT", "QTY", "QTY", "UNIT", "UNIT", "NAME"]
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(
            sentence,
            labelled_tokens,
            custom_units={},
            volumetric_units_system="imperial",
        )

        expected = [
            ingredient_amount_factory(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=3
            ),
            ingredient_amount_factory(
                quantity="28",
                unit="ounce",
                text="28 ounces",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
                volumetric_units_system="imperial",
            ),
        ]

        # Don't check scores
        output = p._sizeable_unit_pattern(labelled_tokens)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out.starting_index == expected.starting_index
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
        pos_tags = ["CD", "NN", "CC", "CD", "CD", "NN", "MD", "VB"]
        labels = ["QTY", "UNIT", "COMMENT", "QTY", "QTY", "UNIT", "UNIT", "NAME"]
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(sentence, labelled_tokens, custom_units={}, string_units=True)

        expected = [
            ingredient_amount_factory(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=3
            ),
            ingredient_amount_factory(
                quantity="28",
                unit="ounce",
                text="28 ounces",
                confidence=0,
                starting_index=4,
                SINGULAR=True,
                string_units=True,
            ),
        ]

        # Don't check scores
        output = p._sizeable_unit_pattern(labelled_tokens)
        assert len(output) == len(expected)
        for out, expected in zip(output, expected):
            assert out.quantity == expected.quantity
            assert out.unit == expected.unit
            assert out.starting_index == expected.starting_index
            assert out.SINGULAR == expected.SINGULAR
            assert out.APPROXIMATE == expected.APPROXIMATE

    def test_no_count_pattern(self):
        """
        Test [QTY, UNIT, UNIT] pattern where there is no leading count.
        E.g., "15 ounce can chickpeas" should produce an implied-count
        container amount and a weight amount.
        """
        sentence = "15 ounce can chickpeas"
        tokens = ["15", "ounce", "can", "chickpeas"]
        pos_tags = ["CD", "NN", "MD", "VB"]
        labels = ["QTY", "UNIT", "UNIT", "B_NAME_TOK"]
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(sentence, labelled_tokens, custom_units={})

        expected = [
            ingredient_amount_factory(
                quantity="1", unit="can", text="1 can", confidence=0, starting_index=0
            ),
            ingredient_amount_factory(
                quantity="15",
                unit="ounce",
                text="15 ounces",
                confidence=0,
                starting_index=0,
                SINGULAR=True,
            ),
        ]

        output = p._sizeable_unit_pattern(labelled_tokens)
        assert len(output) == len(expected)
        for out, exp in zip(output, expected):
            assert out.quantity == exp.quantity
            assert out.unit == exp.unit
            assert out.text == exp.text
            assert out.starting_index == exp.starting_index
            assert out.SINGULAR == exp.SINGULAR
            assert out.APPROXIMATE == exp.APPROXIMATE

    def test_no_count_pattern_non_container_end(self):
        """
        Test that [QTY, UNIT, UNIT] does not match when the end unit is not
        in the end_units list (e.g., "cup" is not a container).
        """
        sentence = "15 ounce cup chickpeas"
        tokens = ["15", "ounce", "cup", "chickpeas"]
        pos_tags = ["CD", "NN", "NN", "NNS"]
        labels = ["QTY", "UNIT", "UNIT", "B_NAME_TOK"]
        scores = [0.0] * len(tokens)
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=score, plural=False
            )
            for i, (text, tag, label, score) in enumerate(
                zip(tokens, pos_tags, labels, scores)
            )
        ]
        p = PostProcessor(sentence, labelled_tokens, custom_units={})

        assert p._sizeable_unit_pattern(labelled_tokens) == []

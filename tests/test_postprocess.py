import pytest

from ingredient_parser import PostProcessor
from ingredient_parser.postprocess import (
    IngredientAmount,
    IngredientText,
    ParsedIngredient,
    consume,
)


@pytest.fixture
def p():
    """Define a PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    sentence = "2 14 ounce cans coconut milk"
    tokens = ["2", "14", "ounce", "can", "coconut", "milk"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "NAME", "NAME"]
    scores = [
        0.9991370577083561,
        0.9725378063405858,
        0.9978510889596651,
        0.9922350007952175,
        0.9886087821704076,
        0.9969237827902526,
    ]

    return PostProcessor(sentence, tokens, labels, scores)


class Test_consume:
    def test_conume(self):
        """
        Test iterator advances by specified amount
        """
        it = iter(range(0, 10))
        assert next(it) == 0
        consume(it, 2)
        assert next(it) == 3

    def test_consume_all(self):
        """
        Test iterator is consumed completely
        """
        it = iter(range(0, 10))
        assert next(it) == 0
        consume(it, None)
        with pytest.raises(StopIteration):
            next(it)


class TestPostProcessor__builtins__:
    def test__str__(self, p):
        """
        Test PostProcessor __str__
        """
        truth = """Post-processed recipe ingredient sentence
\t[('2', 'QTY'), ('14', 'QTY'), ('ounce', 'UNIT'), ('can', 'UNIT'), \
('coconut', 'NAME'), ('milk', 'NAME')]"""
        assert str(p) == truth

    def test__repr__(self, p):
        """
        Test PostProessor __repr__
        """
        assert repr(p) == 'PostProcessor("2 14 ounce cans coconut milk")'


class TestPostProcessor_parsed:
    def test(self, p):
        """
        Test fixture returns expected ParsedIngredient object
        """
        expected = ParsedIngredient(
            name=IngredientText(text="coconut milk", confidence=0.992766),
            amount=[
                IngredientAmount(
                    quantity="2",
                    unit="cans",
                    confidence=0.9956860292517868,
                    APPROXIMATE=False,
                    SINGULAR=False,
                ),
                IngredientAmount(
                    quantity="14",
                    unit="ounces",
                    confidence=0.9725378063405858,
                    APPROXIMATE=False,
                    SINGULAR=True,
                ),
            ],
            comment=None,
            other=None,
            sentence="2 14 ounce cans coconut milk",
        )
        assert p.parsed() == expected


class TestPostProcessor_fix_punctuation:
    def test_leading_comma(self, p):
        """
        Test leading comma and space are removed
        """
        input_sentence = ", finely chopped"
        assert p._fix_punctuation(input_sentence) == "finely chopped"

    def test_trailing_comma(self, p):
        """
        Test trailing comma is removed
        """
        input_sentence = "finely chopped,"
        assert p._fix_punctuation(input_sentence) == "finely chopped"

    def test_space_following_open_parens(self, p):
        """
        Test space following open parenthesis is removed
        """
        input_sentence = "finely chopped ( diced)"
        assert p._fix_punctuation(input_sentence) == "finely chopped (diced)"

    def test_space_leading_close_parens(self, p):
        """
        Test space before close parenthesis is removed
        """
        input_sentence = "finely chopped (diced )"
        assert p._fix_punctuation(input_sentence) == "finely chopped (diced)"

    def test_unpaired_open_parenthesis(self, p):
        """
        Test unpaired open parenthesis is removed
        """
        input_sentence = "finely chopped diced)"
        assert p._fix_punctuation(input_sentence) == "finely chopped diced"

    def test_unpaired_close_parenthesis(self, p):
        """
        Test unpaired close parenthesis is removed
        """
        input_sentence = "finely chopped (diced"
        assert p._fix_punctuation(input_sentence) == "finely chopped diced"

    def test_multiple_unpaired_parentheses(self, p):
        """
        Test unmatched open and unmatched close parentheses are removed, but
        matched pair are kept.
        """
        input_sentence = "finely) (chopped) (diced"
        assert p._fix_punctuation(input_sentence) == "finely (chopped) diced"


class TestPostProcessor_remove_isolated_punctuation_and_duplicate_indices:
    def test_isolated_punctuation(self, p):
        """
        Test that index of "(" element is not returned
        """
        input_list = ["finely", "(", "chopped"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            2,
        ]

    def test_no_isolated_punctuation(self, p):
        """
        Test all indices are returned
        """
        input_list = ["finely", "chopped", "or", "diced"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            1,
            2,
            3,
        ]

    def test_adjacent_duplicate(self, p):
        """
        Test that index of second "finely" is not returned
        """
        input_list = ["finely", "finely", "chopped"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            2,
        ]

    def test_non_adjacent_duplicate(self, p):
        """
        Test that index of non-adjacent duplicate is returned
        """
        input_list = ["finely", "chopped", "finely"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            1,
            2,
        ]

    def test_isolated_punc_and_duplicates(self, p):
        """
        Test that index of "(" and second "finely" elements are not returned
        """
        input_list = ["finely", "finely", "(", "chopped"]
        assert p._remove_isolated_punctuation_and_duplicate_indices(input_list) == [
            0,
            3,
        ]


class TestUtils_group_consecutive_indices:
    def test_single_group(self, p):
        """
        Return single group
        """
        input_indices = [0, 1, 2, 3, 4]
        groups = p._group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [input_indices]

    def test_multiple_groups(self, p):
        """
        Return groups of consecutive indices
        """
        input_indices = [0, 1, 2, 4, 5, 6, 8, 9]
        groups = p._group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [[0, 1, 2], [4, 5, 6], [8, 9]]


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
        assert len(p._sizable_unit_pattern()) == len(expected)
        for output, expected in zip(p._sizable_unit_pattern(), expected):
            assert output.quantity == expected.quantity
            assert output.unit == expected.unit
            assert output.SINGULAR == expected.SINGULAR
            assert output.APPROXIMATE == expected.APPROXIMATE

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
        assert len(p._sizable_unit_pattern()) == len(expected)
        for output, expected in zip(p._sizable_unit_pattern(), expected):
            assert output.quantity == expected.quantity
            assert output.unit == expected.unit
            assert output.SINGULAR == expected.SINGULAR
            assert output.APPROXIMATE == expected.APPROXIMATE

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
        assert len(p._sizable_unit_pattern()) == len(expected)
        for output, expected in zip(p._sizable_unit_pattern(), expected):
            assert output.quantity == expected.quantity
            assert output.unit == expected.unit
            assert output.SINGULAR == expected.SINGULAR
            assert output.APPROXIMATE == expected.APPROXIMATE

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
        assert p._sizable_unit_pattern() is None

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
            IngredientAmount(quantity="2", unit="cups", confidence=0),
            IngredientAmount(quantity="1", unit="can", confidence=0),
            IngredientAmount(quantity="28", unit="ounces", confidence=0, SINGULAR=True),
        ]

        # Don't check scores
        assert len(p._sizable_unit_pattern()) == len(expected)
        for output, expected in zip(p._sizable_unit_pattern(), expected):
            assert output.quantity == expected.quantity
            assert output.unit == expected.unit
            assert output.SINGULAR == expected.SINGULAR
            assert output.APPROXIMATE == expected.APPROXIMATE


class TestPostProcessor_match_pattern:
    def test_long_pattern_match(self):
        """
        Test that correct start and stop indices are returned for long pattern
        """
        pattern = ["QTY", "QTY", "UNIT", "QTY", "UNIT", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "UNIT",
            "QTY",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], labels, [])

        assert p._match_pattern(pattern) == [[2, 3, 4, 5, 6, 7, 8, 9]]

    def test_medium_pattern_match(self):
        """
        Test that correct start and stop indices are returned for medium pattern
        """
        pattern = ["QTY", "QTY", "UNIT", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], labels, [])

        assert p._match_pattern(pattern) == [[0, 1, 2, 3, 4, 5]]

    def test_short_pattern_match(self):
        """
        Test that correct start and stop indices are returned for long pattern
        """
        pattern = ["QTY", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "UNIT",
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], labels, [])

        assert p._match_pattern(pattern) == [[2, 3, 4, 5]]

    def test_impossible_match(self):
        """
        Test that empty list is returned when match is impossible beacause pattern
        is longer than list of labels
        """
        pattern = ["QTY", "QTY", "UNIT", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], labels, [])

        assert p._match_pattern(pattern) == []

    def test_multiple_matches(self):
        """
        Test that multiple non-overlapping matches are returned
        """
        pattern = ["QTY", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
            "QTY",
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], labels, [])

        assert p._match_pattern(pattern) == [[0, 1, 2, 3], [5, 6, 7, 8]]


class TestPostProcessor_fallback_pattern:
    def test_basic(self, p):
        """
        Test that a single IngredientAmount object with quantity "3" and
        unit "large handfuls" is returned.
        """

        tokens = ["3", "large", "handful", "cherry", "tomatoes"]
        labels = ["QTY", "UNIT", "UNIT", "NAME", "NAME"]
        scores = [0] * len(tokens)

        expected = [IngredientAmount(quantity="3", unit="large handfuls", confidence=0)]

        assert p._fallback_pattern(tokens, labels, scores) == expected

    def test_no_quantity(self, p):
        """
        Test that a single IngredientAmount object with no quantity and
        unit "large handfuls" is returned.
        """

        tokens = ["1", "green", ",", "large", "pepper"]
        labels = ["QTY", "NAME", "COMMA", "UNIT", "NAME"]
        scores = [0] * len(tokens)

        expected = [IngredientAmount(quantity="1", unit=", large", confidence=0)]

        assert p._fallback_pattern(tokens, labels, scores) == expected

    def test_comma_before_unit(self, p):
        """
        Test that a single IngredientAmount object with no quantity and
        unit "large handfuls" is returned.
        """

        tokens = ["bunch", "of", "basil", "leaves"]
        labels = ["UNIT", "COMMENT", "NAME", "NAME"]
        scores = [0] * len(tokens)

        expected = [IngredientAmount(quantity="", unit="bunch", confidence=0)]

        assert p._fallback_pattern(tokens, labels, scores) == expected

    def test_approximate(self, p):
        """
        Test that a single IngredientAmount object with the APPROXIMATE flag set
        is returned
        """
        tokens = ["About", "2", "cup", "flour"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME"]
        scores = [0] * len(tokens)

        expected = [
            IngredientAmount(
                quantity="2",
                unit="cups",
                confidence=0,
                APPROXIMATE=True,
            )
        ]

        assert p._fallback_pattern(tokens, labels, scores) == expected

    def test_singular(self, p):
        """
        Test that a single IngredientAmount object with the SINGULAR flag set
        is returned
        """
        tokens = ["2", "bananas", ",", "4", "ounce", "each"]
        labels = ["QTY", "NAME", "COMMA", "QTY", "UNIT", "COMMENT"]
        scores = [0] * len(tokens)

        expected = [
            IngredientAmount(
                quantity="2",
                unit="",
                confidence=0,
            ),
            IngredientAmount(
                quantity="4",
                unit="ounces",
                confidence=0,
                SINGULAR=True,
            ),
        ]

        assert p._fallback_pattern(tokens, labels, scores) == expected

    def test_singular_and_approximate(self, p):
        """
        Test that a single IngredientAmount object with the APPROXIMATE and
        SINGULAR flags set is returned
        """
        tokens = ["2", "bananas", ",", "each", "about", "4", "ounce"]
        labels = ["QTY", "NAME", "COMMA", "COMMENT", "COMMENT", "QTY", "UNIT"]
        scores = [0] * len(tokens)

        expected = [
            IngredientAmount(
                quantity="2",
                unit="",
                confidence=0,
            ),
            IngredientAmount(
                quantity="4",
                unit="ounces",
                confidence=0,
                SINGULAR=True,
                APPROXIMATE=True,
            ),
        ]

        assert p._fallback_pattern(tokens, labels, scores) == expected

    def test_dozen(self, p):
        """
        Test that the token "dozen" is combined with the preceding QTY token in a
        single IngredientAmount object.
        """
        tokens = ["2", "dozen", "bananas", ",", "each", "about", "4", "ounce"]
        labels = ["QTY", "QTY", "NAME", "COMMA", "COMMENT", "COMMENT", "QTY", "UNIT"]
        scores = [0] * len(tokens)

        expected = [
            IngredientAmount(
                quantity="2 dozen",
                unit="",
                confidence=0,
            ),
            IngredientAmount(
                quantity="4",
                unit="ounces",
                confidence=0,
                SINGULAR=True,
                APPROXIMATE=True,
            ),
        ]

        assert p._fallback_pattern(tokens, labels, scores) == expected


class TestPostProcessor_is_approximate:
    def test_is_approximate_about(self, p):
        """
        Test that QTY at index is indicated as approximate
        """
        tokens = ["about", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert p._is_approximate(1, tokens, labels)

    def test_is_approximate_approx(self, p):
        """
        Test that QTY at index is indicated as approximate
        """
        tokens = ["approx.", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert p._is_approximate(1, tokens, labels)

    def test_is_approximate_approximately(self, p):
        """
        Test that QTY at index is indicated as approximate
        """
        tokens = ["approximately", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert p._is_approximate(1, tokens, labels)

    def test_is_approximate_nearly(self, p):
        """
        Test that QTY at index is indicated as approximate
        """
        tokens = ["nearly", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert p._is_approximate(1, tokens, labels)

    def test_not_approximate(self, p):
        """
        Test that QTY at index is not indicated as approximate
        """
        tokens = ["maximum", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        assert not p._is_approximate(1, tokens, labels)


class TestPostProcessor_is_singular:
    def test_is_singular(self, p):
        """
        Test that UNIT at index is indicated as singular
        """
        tokens = ["4", "salmon", "fillets", "2", "pounds", "each"]
        labels = ["QTY", "NAME", "NAME", "QTY", "UNIT", "COMMENT"]
        assert p._is_singular(4, tokens, labels)

    def test_not_singular(self, p):
        """
        Test that UNIT at index is not indicated as singular
        """
        tokens = ["4", "salmon", "fillets", "2", "pounds", "minimum"]
        labels = ["QTY", "NAME", "NAME", "QTY", "UNIT", "COMMENT"]
        assert not p._is_singular(4, tokens, labels)


class TestPostProcessor_is_singular_and_approximate:
    def test_is_singular_and_approximate(self, p):
        """
        Test that QTY at index is indicated as approximate and singular
        """
        tokens = ["each", "nearly", "2", "kg"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT"]
        assert p._is_singular_and_approximate(2, tokens, labels)

    def test_not_singular_and_approximate(self, p):
        """
        Test that QTY at index is not indicated as approximate and singular
        """
        tokens = ["both", "about", "2", "kg"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT"]
        assert not p._is_singular_and_approximate(2, tokens, labels)

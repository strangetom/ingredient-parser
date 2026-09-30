from fractions import Fraction

import pytest

from ingredient_parser import parse_ingredient


class TestParser_compound_units_no_count:
    """
    Test parsing of "X ounce/oz can/jar/bottle" patterns where there is no
    leading count. The weight (e.g. "15 ounce") describes the container size,
    not the primary measurement.

    These depend on the CRF model producing [QTY, UNIT, UNIT] labels for the
    weight+container pattern. If the model is retrained and labeling changes,
    these tests may need updating even if the postprocessor logic is correct.
    """

    @pytest.mark.parametrize(
        ("sentence", "expected_container", "expected_weight_qty", "expected_name"),
        [
            ("15 ounce can black beans", "can", 15, "black beans"),
            ("15 oz can chickpeas", "can", 15, "chickpeas"),
            ("28 ounce can crushed tomatoes", "can", 28, "crushed tomatoes"),
            ("6 ounce can tomato paste", "can", 6, "tomato paste"),
            ("10 ounce can tomato sauce", "can", 10, "tomato sauce"),
            ("8 ounce can tomato sauce", "can", 8, "tomato sauce"),
            ("12-ounce jar apricot preserves", "jar", 12, "apricot preserves"),
            ("16-ounce bag baby spinach", "bag", 16, "baby spinach"),
        ],
    )
    def test_no_count_compound_unit(
        self, sentence, expected_container, expected_weight_qty, expected_name
    ):
        parsed = parse_ingredient(sentence)

        assert len(parsed.amount) == 2
        # Primary amount: quantity of 1, container unit
        assert parsed.amount[0].quantity == 1
        assert str(parsed.amount[0].unit) == expected_container
        # Secondary amount: weight
        assert parsed.amount[1].quantity == expected_weight_qty
        assert str(parsed.amount[1].unit) == "ounce"
        assert parsed.name[0].text == expected_name


class TestParser_compound_units_regression:
    """
    Regression tests ensuring that patterns with an explicit leading count
    still work correctly after adding the no-count pattern.
    """

    @pytest.mark.parametrize(
        (
            "sentence",
            "expected_primary_quantity",
            "expected_primary_unit",
            "expected_equivalent_quantity",
            "expected_name",
        ),
        [
            (
                "2 1/2 (250 g) cups old-fashioned rolled oats",
                Fraction(5, 2),
                "cups",
                250,
                "old-fashioned rolled oats",
            ),
            (
                "2/3 (237 g) cup honey",
                Fraction(2, 3),
                "cups",
                237,
                "honey",
            ),
        ],
    )
    def test_parenthesized_equivalent_precedes_primary_unit(
        self,
        sentence,
        expected_primary_quantity,
        expected_primary_unit,
        expected_equivalent_quantity,
        expected_name,
    ):
        parsed = parse_ingredient(sentence, string_units=True)

        assert len(parsed.amount) == 2
        assert parsed.amount[0].quantity == expected_primary_quantity
        assert str(parsed.amount[0].unit) == expected_primary_unit
        assert parsed.amount[1].quantity == expected_equivalent_quantity
        assert str(parsed.amount[1].unit) == "g"
        assert parsed.name[0].text == expected_name

    def test_primary_unit_precedes_parenthesized_equivalent(self):
        parsed = parse_ingredient(
            "2 1/2 cups (250 g) old-fashioned rolled oats", string_units=True
        )

        assert len(parsed.amount) == 2
        assert parsed.amount[0].quantity == Fraction(5, 2)
        assert str(parsed.amount[0].unit) == "cups"
        assert parsed.amount[1].quantity == 250
        assert str(parsed.amount[1].unit) == "g"
        assert parsed.name[0].text == "old-fashioned rolled oats"

    def test_1_parenthesized_15oz_can(self):
        parsed = parse_ingredient("1 (15 oz) can black beans")

        assert len(parsed.amount) == 2
        assert parsed.amount[0].quantity == 1
        assert str(parsed.amount[0].unit) == "can"
        assert parsed.amount[1].quantity == 15
        assert str(parsed.amount[1].unit) == "ounce"
        assert parsed.name[0].text == "black beans"

    def test_2_parenthesized_6oz_cans(self):
        parsed = parse_ingredient("2 (6-oz) cans tomato paste")

        assert len(parsed.amount) == 2
        assert parsed.amount[0].quantity == 2
        assert str(parsed.amount[0].unit) == "cans"
        assert parsed.amount[1].quantity == 6
        assert str(parsed.amount[1].unit) == "ounce"
        assert parsed.name[0].text == "tomato paste"

    def test_1_28_ounce_can(self):
        parsed = parse_ingredient("1 28-ounce can crushed tomatoes")

        assert len(parsed.amount) == 2
        assert parsed.amount[0].quantity == 1
        assert str(parsed.amount[0].unit) == "can"
        assert parsed.amount[1].quantity == 28
        assert str(parsed.amount[1].unit) == "ounce"
        assert parsed.name[0].text == "crushed tomatoes"

    def test_simple_15_ounces_butter(self):
        """15 ounces of a simple ingredient should not trigger the container pattern."""
        parsed = parse_ingredient("15 ounces butter")

        assert len(parsed.amount) == 1
        assert parsed.amount[0].quantity == 15
        assert str(parsed.amount[0].unit) == "ounce"
        assert parsed.name[0].text == "butter"

    def test_simple_2_cups_flour(self):
        parsed = parse_ingredient("2 cups flour")

        assert len(parsed.amount) == 1
        assert parsed.amount[0].quantity == 2
        assert parsed.name[0].text == "flour"

    def test_simple_1_clove_garlic(self):
        parsed = parse_ingredient("1 clove garlic")

        assert len(parsed.amount) == 1
        assert parsed.amount[0].quantity == 1
        assert str(parsed.amount[0].unit) == "clove"
        assert parsed.name[0].text == "garlic"

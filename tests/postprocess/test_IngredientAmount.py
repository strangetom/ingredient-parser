from fractions import Fraction

import pytest

from ingredient_parser.dataclasses import CompositeIngredientAmount, UnitSystem
from ingredient_parser.en._utils import UREG, ingredient_amount_factory


class TestPostProcessor_IngredientAmount:
    def test_float_quantity(self):
        """
        Test that the string quantity is correctly converted to a float
        and that quantity_max is set to the same value
        """
        amount = ingredient_amount_factory(
            quantity="25",
            unit="g",
            text="25 g",
            confidence=0,
            starting_index=0,
        )

        assert amount.quantity == 25
        assert amount.quantity_max == 25
        assert amount.unit_system == UnitSystem.METRIC

    def test_range_quantity(self):
        """
        Test that the string quantity is correctly identified as a range
        and that quantity and quantity_max are set correctly, and the RANGE
        flag is also set.
        """
        amount = ingredient_amount_factory(
            quantity="25-30",
            unit="g",
            text="25 g",
            confidence=0,
            starting_index=0,
        )

        assert amount.quantity == 25
        assert amount.quantity_max == 30
        assert amount.RANGE
        assert amount.unit_system == UnitSystem.METRIC

    def test_multiplier_quantity(self):
        """
        Test the string quantity is correctly identified as a multiplier and
        that the quantity and quantity_max field as set the same value, and the
        MULTIPLIER flag is also set.
        """
        amount = ingredient_amount_factory(
            quantity="1x", unit="can", text="1x can", confidence=0, starting_index=0
        )

        assert amount.quantity == 1
        assert amount.quantity_max == 1
        assert amount.MULTIPLIER
        assert amount.unit_system == UnitSystem.OTHER

    def test_pluralisation_string_unit(self):
        """
        Test that the unit in the string in the unit and text fields
        are pluralised correctly.
        """
        amount = ingredient_amount_factory(
            quantity="2", unit="can", text="2 can", confidence=0, starting_index=0
        )

        assert amount.unit == "cans"
        assert amount.text == "2 cans"
        assert amount.unit_system == UnitSystem.OTHER

    def test_pluralisation_pint_unit(self):
        """
        Test that the unit in the string in the text field is pluralised correctly.
        """
        amount = ingredient_amount_factory(
            quantity="200",
            unit="gram",
            text="200 grams",
            confidence=0,
            starting_index=0,
        )

        assert amount.unit == UREG("gram").units
        assert amount.text == "200 grams"
        assert amount.unit_system == UnitSystem.METRIC

    def test_fraction_range_quantity(self):
        """
        Test that the string quantity is correctly identified as a range
        and that quantity and quantity_max are set correctly, and the RANGE
        flag is also set.
        """
        amount = ingredient_amount_factory(
            quantity="#1$4-#1$2",
            unit="tsp",
            text="1/4-1/2 tsp",
            confidence=0,
            starting_index=0,
        )

        assert amount.quantity == 0.25
        assert amount.quantity_max == 0.5
        assert amount.text == "1/4-1/2 tsp"
        assert amount.RANGE
        assert amount.unit_system == UnitSystem.US_CUSTOMARY


class TestPostProcessor_CompositeIngredientAmount:
    def test_composite_ingredient_amount_us_customary(self):
        """
        Test that the unit system for a composite ingredient amount is correct set.
        """
        am1 = ingredient_amount_factory("2", "cups", "2 cups", 0, 0)
        am2 = ingredient_amount_factory("2", "tbsp", "2 tbsp", 0, 0)

        amount = CompositeIngredientAmount(
            amounts=[am1, am2], join="", subtractive=False
        )

        assert amount.unit_system == UnitSystem.US_CUSTOMARY

    def test_composite_ingredient_amount_imperial(self):
        """
        Test that the unit system for a composite ingredient amount is correct set when
        one of the units is imperial and the other US customary.
        """
        am1 = ingredient_amount_factory(
            "1", "cup", "1 cup", 0, 0, volumetric_units_system="imperial"
        )
        am2 = ingredient_amount_factory("2", "tbsp", "2 tbsp", 0, 0)

        amount = CompositeIngredientAmount(
            amounts=[am1, am2], join="", subtractive=False
        )

        assert amount.unit_system == UnitSystem.IMPERIAL


class Test_IngredientAmount_convert_to:
    def test_convert(self):
        """
        Test that 1.2 kg is convert to 1,200 g
        """
        amount = ingredient_amount_factory(
            quantity="1.2",
            unit="kg",
            text="1.2 kg",
            confidence=0,
            starting_index=0,
        )

        converted = amount.convert_to("g")

        assert converted.quantity == 1000 * amount.quantity
        assert converted.quantity_max == 1000 * amount.quantity_max
        assert converted.unit == UREG("gram").units
        assert converted.text == "1200 gram"
        assert converted.unit_system == UnitSystem.METRIC

    def test_convert_metric_to_us_customary(self):
        """
        Test that 500 ml is converted to ... cups
        """
        amount = ingredient_amount_factory(
            quantity="500",
            unit="ml",
            text="500 ml",
            confidence=0,
            starting_index=0,
        )

        converted = amount.convert_to("cup")

        assert converted.quantity == Fraction(4226752837730377, 2000000000000000)
        assert converted.quantity_max == Fraction(4226752837730377, 2000000000000000)
        assert converted.unit == UREG("cup").units
        assert converted.text == "2.11338 cup"
        assert converted.unit_system == UnitSystem.US_CUSTOMARY

    def test_convert_metric_to_imperial(self):
        """
        Test that 500 ml is converted to ... cups
        """
        amount = ingredient_amount_factory(
            quantity="500",
            unit="ml",
            text="500 ml",
            confidence=0,
            starting_index=0,
        )

        converted = amount.convert_to("imperial_cup")

        assert converted.quantity == Fraction(879876993196351, 500000000000000)
        assert converted.quantity_max == Fraction(879876993196351, 500000000000000)
        assert converted.unit == UREG("imperial_cup").units
        assert converted.text == "1.75975 imperial_cup"
        assert converted.unit_system == UnitSystem.IMPERIAL

    def test_string_unit(self):
        """
        Test that TypeError is raised when unit is a string
        """
        amount = ingredient_amount_factory(
            quantity="1",
            unit="can",
            text="1 can",
            confidence=0,
            starting_index=0,
        )

        with pytest.raises(TypeError):
            _ = amount.convert_to("ml")

    def test_string_quantity(self):
        """
        Test that TypeError is raised when quantity is a string
        """
        amount = ingredient_amount_factory(
            quantity="dozen",
            unit="ml",
            text="dozen ml",
            confidence=0,
            starting_index=0,
        )

        with pytest.raises(TypeError):
            _ = amount.convert_to("ml")

    def test_composite_ingredient_amount(self):
        """
        Test composite ingredient amount conversion to metric.
        """
        am1 = ingredient_amount_factory("2", "lbs", "2 lb", 0, 0)
        am2 = ingredient_amount_factory("2", "oz", "2 oz", 0, 0)

        amount = CompositeIngredientAmount(
            amounts=[am1, am2], join="", subtractive=False
        )
        converted = amount.convert_to("kg")

        assert converted.magnitude == Fraction(77110702900000017, 80000000000000000)
        assert converted.units == UREG("kg").units

from fractions import Fraction

from ingredient_parser.dataclasses import CompositeIngredientAmount, UnitSystem
from ingredient_parser.en._utils import UREG, ingredient_amount_factory


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
        am2 = ingredient_amount_factory(
            "2", "tbsp", "2 tbsp", 0, 0, volumetric_units_system="imperial"
        )

        amount = CompositeIngredientAmount(
            amounts=[am1, am2], join="", subtractive=False
        )

        assert amount.unit_system == UnitSystem.IMPERIAL


class TestPostProcessor_CompositeIngredientAmount_convert_to:
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

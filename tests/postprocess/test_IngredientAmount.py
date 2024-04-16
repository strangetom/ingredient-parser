import pint

from ingredient_parser.dataclasses import IngredientAmount


class TestPostProcessor_IngredientAmount:
    def test_float_quantity(self):
        """
        Test that the string quantity is correctly converted to a float
        and that quantity_max is set to the same value
        """
        amount = IngredientAmount(
            quantity="25",
            unit=pint.Unit("g"),
            text="25 g",
            confidence=0,
            starting_index=0,
        )

        assert amount.quantity == 25
        assert amount.quantity_max == 25

    def test_range_quantity(self):
        """
        Test that the string quantity is correctly identified as a range
        and that quantity and quantity_max are set correctly, and the RANGE
        flag is also set.
        """
        amount = IngredientAmount(
            quantity="25-30",
            unit=pint.Unit("g"),
            text="25 g",
            confidence=0,
            starting_index=0,
        )

        assert amount.quantity == 25
        assert amount.quantity_max == 30
        assert amount.RANGE

    def test_multiplier_quantity(self):
        """
        Test the string quantity is correctly identified as a multiplier and
        that the quantity and quantity_max field as set the same value, and the
        MULTIPLIER flag is also set.
        """
        amount = IngredientAmount(
            quantity="1x", unit="can", text="1x can", confidence=0, starting_index=0
        )

        assert amount.quantity == 1
        assert amount.quantity_max == 1
        assert amount.MULTIPLIER

    def test_pluralisation_string_unit(self):
        """
        Test that the unit in the string in the unit and text fields
        are pluralised correctly.
        """
        amount = IngredientAmount(
            quantity="2", unit="can", text="2 can", confidence=0, starting_index=0
        )

        assert amount.unit == "cans"
        assert amount.text == "2 cans"

    def test_pluralisation_pint_unit(self):
        """
        Test that the unit in the string in the text field is pluralised correctly.
        """
        amount = IngredientAmount(
            quantity="200",
            unit=pint.Unit("gram"),
            text="200 grams",
            confidence=0,
            starting_index=0,
        )

        assert amount.unit == pint.Unit("gram")
        assert amount.text == "200 grams"

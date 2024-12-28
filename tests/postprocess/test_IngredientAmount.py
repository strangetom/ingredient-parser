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

from ingredient_parser.en._utils import (
    UREG,
    convert_to_pint_unit,
    pluralise_units,
)


class TestUtils_pluralise_units:
    def test_single(self):
        """
        Each singular unit gets pluralised
        """
        assert pluralise_units("teaspoon") == "teaspoons"
        assert pluralise_units("cup") == "cups"
        assert pluralise_units("loaf") == "loaves"
        assert pluralise_units("leaf") == "leaves"
        assert pluralise_units("chunk") == "chunks"
        assert pluralise_units("Box") == "Boxes"
        assert pluralise_units("Wedge") == "Wedges"

    def test_embedded(self):
        """
        The unit embedded in each sentence gets pluralised
        """
        assert pluralise_units("2 tablespoon olive oil") == "2 tablespoons olive oil"
        assert (
            pluralise_units("3 cup (750 milliliter) milk")
            == "3 cups (750 milliliters) milk"
        )


class Test_convert_to_pint_unit:
    def test_empty_string(self):
        """
        Test an empty string is returned if input
        """
        assert convert_to_pint_unit("") == ""

    def test_simple_cases(self):
        """
        Test simple cases of units and plural variations are correctly
        matched to pint.Unit objects.
        This doesn't need to be comprehensive because we don't need to test
        pint works.
        """
        assert convert_to_pint_unit("g") == UREG("g").units
        assert convert_to_pint_unit("gram") == UREG("g").units
        assert convert_to_pint_unit("grams") == UREG("g").units
        assert convert_to_pint_unit("oz") == UREG("oz").units
        assert convert_to_pint_unit("ounce") == UREG("oz").units
        assert convert_to_pint_unit("ounces") == UREG("oz").units

    def test_modified_cases(self):
        """
        Test cases where we need to swap to unit to a version pint recognises
        """
        assert convert_to_pint_unit("fl oz") == UREG("fluid_ounce").units
        assert convert_to_pint_unit("fluid oz") == UREG("fluid_ounce").units
        assert convert_to_pint_unit("fl ounce") == UREG("fluid_ounce").units
        assert convert_to_pint_unit("fluid ounce") == UREG("fluid_ounce").units
        assert convert_to_pint_unit("Cl") == UREG("centiliter").units
        assert convert_to_pint_unit("G") == UREG("gram").units
        assert convert_to_pint_unit("Ml") == UREG("milliliter").units
        assert convert_to_pint_unit("Pt") == UREG("pint").units
        assert convert_to_pint_unit("Tb") == UREG("tablespoon").units

    def test_imperial_units(self):
        """
        Test that imperial units are returned where appropriate
        """
        assert (
            convert_to_pint_unit("fl oz", imperial_units=True)
            == UREG("imperial_fluid_ounce").units
        )
        assert (
            convert_to_pint_unit("cup", imperial_units=True)
            == UREG("imperial_cup").units
        )
        assert (
            convert_to_pint_unit("quart", imperial_units=True)
            == UREG("imperial_quart").units
        )
        assert (
            convert_to_pint_unit("pint", imperial_units=True)
            == UREG("imperial_pint").units
        )
        assert (
            convert_to_pint_unit("gallon", imperial_units=True)
            == UREG("imperial_gallon").units
        )

    def test_unit_with_hypen(self):
        """
        Test that units containing hyphens always return string.
        This example isn't actually a unit, but can be mislablled as one, so
        we need to check this case.
        """
        assert convert_to_pint_unit("medium-size") == "medium-size"

    def test_misinterpretted_units(self):
        """
        Test cases that pint would misinterpret as a different, incorrect unit
        """
        assert convert_to_pint_unit("pinch") == "pinch"
        # Plural
        assert convert_to_pint_unit("bars") == "bars"
        # Title case
        assert convert_to_pint_unit("Tin") == "Tin"
        # Title case + plural
        assert convert_to_pint_unit("Links") == "Links"
        assert convert_to_pint_unit("shake") == "shake"

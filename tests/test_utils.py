import pint
import pytest

from ingredient_parser._utils import consume, convert_to_pint_unit, pluralise_units


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
        assert convert_to_pint_unit("g") == pint.Unit("g")
        assert convert_to_pint_unit("gram") == pint.Unit("g")
        assert convert_to_pint_unit("grams") == pint.Unit("g")
        assert convert_to_pint_unit("oz") == pint.Unit("oz")
        assert convert_to_pint_unit("ounce") == pint.Unit("oz")
        assert convert_to_pint_unit("ounces") == pint.Unit("oz")

    def test_modified_cases(self):
        """
        Test fluid ounce variations are correctly matched to pint.Unit("fluid ounce")
        """
        assert convert_to_pint_unit("fl oz") == pint.Unit("fluid_ounce")
        assert convert_to_pint_unit("fluid oz") == pint.Unit("fluid_ounce")
        assert convert_to_pint_unit("fl ounce") == pint.Unit("fluid_ounce")
        assert convert_to_pint_unit("fluid ounce") == pint.Unit("fluid_ounce")

    def test_imperial_units(self):
        """
        Test that imperial units are returned where appropriate
        """
        assert convert_to_pint_unit("fl oz", imperial_units=True) == pint.Unit(
            "imperial_fluid_ounce"
        )
        assert convert_to_pint_unit("cup", imperial_units=True) == pint.Unit(
            "imperial_cup"
        )
        assert convert_to_pint_unit("quart", imperial_units=True) == pint.Unit(
            "imperial_quart"
        )
        assert convert_to_pint_unit("pint", imperial_units=True) == pint.Unit(
            "imperial_pint"
        )
        assert convert_to_pint_unit("gallon", imperial_units=True) == pint.Unit(
            "imperial_gallon"
        )

from ingredient_parser.en._utils import (
    UREG,
    combine_quantities_split_by_and,
    convert_to_pint_unit,
    is_unit_synonym,
    pluralise_units,
    replace_string_range,
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
        assert convert_to_pint_unit("C") == UREG("cup").units
        assert convert_to_pint_unit("c") == UREG("cup").units

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


class Testcombine_quantities_split_by_and:
    def test_half(self):
        """
        "1 and 1/2" is replaced by 1.5
        """
        input_sentence = "1 and 1/2 tsp salt"
        assert combine_quantities_split_by_and(input_sentence) == "1.5 tsp salt"

    def test_quarter(self):
        """
        "1 and 1/4" is replaced by 1.25
        """
        input_sentence = "1 and 1/4 tsp salt"
        assert combine_quantities_split_by_and(input_sentence) == "1.25 tsp salt"

    def test_three_quarters(self):
        """
        "1 and 3/4" is replaced by 1.75
        """
        input_sentence = "1 and 3/4 tsp salt"
        assert combine_quantities_split_by_and(input_sentence) == "1.75 tsp salt"

    def test_third(self):
        """
        "1 and 1/3" is replaced by 1.333
        """
        input_sentence = "1 and 1/3 tsp salt"
        assert combine_quantities_split_by_and(input_sentence) == "1.333 tsp salt"


class Test_replace_string_range:
    def test_integers(self):
        """
        Test range with format <num> or <num> where <num> are integers
        """
        input_sentence = "4 9 or 10 inch flour tortillas"
        assert replace_string_range(input_sentence) == "4 9-10 inch flour tortillas"

    def test_decimals(self):
        """
        Test range with format <num> or <num> where <num> are decimals
        """
        input_sentence = "1 15.5 or 16 ounce can black beans"
        assert replace_string_range(input_sentence) == "1 15.5-16 ounce can black beans"

    def test_decimals_less_than_one(self):
        """
        Test range with format <num> or <num> where <num> are decimals
        """
        input_sentence = "0.5 to 0.75 teaspoon hot Hungarian paprika"
        assert (
            replace_string_range(input_sentence)
            == "0.5-0.75 teaspoon hot Hungarian paprika"
        )

    def test_hyphens(self):
        """
        Test range where the numbers are followed by hyphens
        """
        input_sentence = "1 6- or 7-ounce can of wild salmon"
        assert replace_string_range(input_sentence) == "1 6-7-ounce can of wild salmon"

    def test_hyphens_with_spaces(self):
        """
        Test range where the numbers are followed by hyphens, where the hyphens are
        surrounded by spaces.
        """
        input_sentence = "1 6 - or 7 - ounce can of wild salmon"
        assert (
            replace_string_range(input_sentence) == "1 6-7 - ounce can of wild salmon"
        )

    def test_first_starts_with_zero(self):
        """
        Test (false) range where the first of the numbers starts with 0
        """
        input_sentence = "Type 00 or 1 flour"
        assert replace_string_range(input_sentence) == "Type 00 or 1 flour"

    def test_second_starts_with_zero(self):
        """
        Test (false) range where the second of the numbers starts with 0
        """
        input_sentence = "Type 1 or 00 flour"
        assert replace_string_range(input_sentence) == "Type 1 or 00 flour"


class Test_is_unit_synonym:
    def test_singular(self):
        assert is_unit_synonym("oz", "ounce")

    def test_plural_singular(self):
        assert is_unit_synonym("cups", "c")

    def test_plural(self):
        assert is_unit_synonym("lbs", "pounds")

    def test_not_synonym(self):
        assert not is_unit_synonym("kg", "gram")

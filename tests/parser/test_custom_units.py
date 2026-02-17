from ingredient_parser import parse_ingredient


class TestParser_custom_units:
    def test_unrecognised_units(self):
        """
        Test that the word "brillig" is not identified as a unit.
        """
        p = parse_ingredient("2 brillig sausages")
        assert p.amount[0].unit == ""
        assert p.amount[0].text == "2"

    def test_custom_units(self):
        """
        Test that brillig is recognised as a unit when provided as part of a custom
        units dict.
        """
        p = parse_ingredient("2 brillig sausages", custom_units={"brilligs": "brillig"})
        assert p.amount[0].unit == "brilligs"
        assert p.amount[0].text == "2 brilligs"

    def test_custom_unit_capitalised(self):
        """
        Test that Brillig is recognised as a unit when provided as part of a custom
        units dict, even though the capitalized version is not present in the custom
        units dict.
        """
        p = parse_ingredient("2 Brillig sausages", custom_units={"brilligs": "brillig"})
        assert p.amount[0].unit == "Brilligs"
        assert p.amount[0].text == "2 Brilligs"

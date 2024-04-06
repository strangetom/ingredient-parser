from ingredient_parser import parse_ingredient


class TestParser_cloves:
    """
    Cloves can be a unit or an ingredient, but the parser struggled to get it right.
    """

    def test_clove_ingredient_singular(self):
        """
        "clove" is marked as a name
        """
        parsed = parse_ingredient("1 clove")

        assert "clove" in parsed.name.text
        assert "clove" not in parsed.amount[0].unit

    def test_clove_ingredient_plural(self):
        """
        "cloves" is marked as a name
        """
        parsed = parse_ingredient("1 tsp cloves")

        assert "cloves" in parsed.name.text
        assert "cloves" != parsed.amount[0].unit

    def test_clove_unit_singular(self):
        """
        "clove" is marked as a unit
        """
        parsed = parse_ingredient("1 garlic clove")

        assert "clove" not in parsed.name.text
        assert "clove" in parsed.amount[0].unit

    def test_clove_unit_singular_switched_order(self):
        """
        "clove" is marked as a unit
        """
        parsed = parse_ingredient("1 clove garlic")

        assert "clove" not in parsed.name.text
        assert "clove" in parsed.amount[0].unit

    def test_clove_unit_plural(self):
        """
        "cloves" is marked as a unit
        """
        parsed = parse_ingredient("2 garlic cloves")

        assert "cloves" not in parsed.name.text
        assert "cloves" in parsed.amount[0].unit

    def test_clove_unit_plural_switched_order(self):
        """
        "cloves" is marked as a unit
        """
        parsed = parse_ingredient("2 cloves garlic")

        assert "cloves" not in parsed.name.text
        assert "cloves" in parsed.amount[0].unit

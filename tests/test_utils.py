from ingredient_parser._utils import pluralise_units


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

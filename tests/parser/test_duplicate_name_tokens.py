from ingredient_parser import parse_ingredient


class TestParser_names_with_duplicate_words:
    def test_mahi_mahi(self):
        parsed = parse_ingredient("3/4 pound mahi mahi fillets ")
        assert parsed.name[0].text == "mahi mahi fillets"

    def test_agar_agar(self):
        parsed = parse_ingredient("1/2 tsp agar agar")
        assert parsed.name[0].text == "agar agar"

    def test_cara_cara(self):
        parsed = parse_ingredient("1 Cara Cara orange, cut into 8 slices")
        assert parsed.name[0].text == "Cara Cara orange"

    def test_chow_chow(self):
        parsed = parse_ingredient("2 tablespoons mild Tennessee chow chow (optional")
        assert parsed.name[0].text == "mild Tennessee chow chow"

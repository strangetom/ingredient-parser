from ingredient_parser import parse_ingredient


class Test_guess_ingredient_name:
    def test_enabled(self):
        """
        Test that the return name is not None
        """
        sentence = "1/4 teaspoon toasted anise seed"
        parsed = parse_ingredient(sentence, guess_name_fallback=True)
        assert parsed.name is not None

    def test_disabled(self):
        """
        Test that the returned name is None
        """
        sentence = "1/4 teaspoon toasted anise seed"
        parsed = parse_ingredient(sentence, guess_name_fallback=False)
        assert parsed.name is None

    def test_enabled_but_no_name(self):
        """
        Test that the return name is None even though guess_name_fallback is enabled.
        """
        sentence = "2 tablespoons"
        parsed = parse_ingredient(sentence, guess_name_fallback=True)
        assert parsed.name is None

from ingredient_parser import parse_ingredient


class Test_expect_name_in_output:
    def test_enabled(self):
        """
        Test that the return name is not []
        """
        sentence = "½ cup or so flour in a plate"
        parsed = parse_ingredient(sentence, expect_name_in_output=True)
        assert parsed.name != []

    def test_disabled(self):
        """
        Test that the returned name is []
        """
        sentence = "1 can (14 fluid ounces, or 425 ml) coconut milk"
        parsed = parse_ingredient(sentence, expect_name_in_output=False)
        assert parsed.name == []

    def test_disabled_name_not_separate(self):
        """
        Test that the returned name is [] when not separating names
        """
        sentence = "1 can (14 fluid ounces, or 425 ml) coconut milk"
        parsed = parse_ingredient(
            sentence, expect_name_in_output=False, separate_names=False
        )
        assert parsed.name == []

    def test_enabled_but_no_name(self):
        """
        Test that the return name is None even though guess_name_fallback is enabled.
        """
        sentence = "2 tablespoons"
        parsed = parse_ingredient(sentence, expect_name_in_output=True)
        assert parsed.name == []

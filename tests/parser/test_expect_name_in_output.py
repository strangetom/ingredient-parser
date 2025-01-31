from ingredient_parser import parse_ingredient


class Test_expect_name_in_output:
    def test_enabled(self):
        """
        Test that the return name is not None
        """
        sentence = "4 Heath bars (1 1/8 ounces each)"
        parsed = parse_ingredient(sentence, expect_name_in_output=True)
        assert parsed.name != []

    def test_disabled(self):
        """
        Test that the returned name is None
        """
        sentence = "4 Heath bars (1 1/8 ounces each)"
        parsed = parse_ingredient(sentence, expect_name_in_output=False)
        assert parsed.name == []

    def test_enabled_but_no_name(self):
        """
        Test that the return name is None even though guess_name_fallback is enabled.
        """
        sentence = "2 tablespoons"
        parsed = parse_ingredient(sentence, expect_name_in_output=True)
        assert parsed.name == []

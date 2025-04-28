from ingredient_parser import parse_ingredient


class Test_separate_names:
    def test_separate_names(self):
        """
        Test that the two ingredient names are returned.
        """
        sentence = "200 ml beef or chicken stock"
        parsed = parse_ingredient(sentence, separate_names=True)
        assert len(parsed.name) == 2

    def test_not_separate_names(self):
        """
        Test that the one ingredient name is returned.
        """
        sentence = "200 ml beef of chicken stock"
        parsed = parse_ingredient(sentence, separate_names=False)
        assert len(parsed.name) == 1

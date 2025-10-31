from ingredient_parser.en.foundationfoods._foundationfoods import normalise_spelling


class TestNormaliseSpelling:
    def test_phrase(self):
        """
        Test "double cream" is normalised to "heavy cream"
        """
        tokens = ["doubl", "cream"]
        normalised_tokens = normalise_spelling(tokens)
        assert len(tokens) == len(normalised_tokens)
        assert normalised_tokens == ["heavi", "cream"]

    def test_token_chilli(self):
        """
        Test "chilli" is normalised to "chili"
        """
        tokens = ["red", "hot", "chilli"]
        normalised_tokens = normalise_spelling(tokens)
        assert len(tokens) == len(normalised_tokens)
        assert normalised_tokens == ["red", "hot", "chili"]

    def test_token_chile(self):
        """
        Test "chile" is normalised to "chili"
        """
        tokens = ["red", "hot", "chile"]
        normalised_tokens = normalise_spelling(tokens)
        assert len(tokens) == len(normalised_tokens)
        assert normalised_tokens == ["red", "hot", "chili"]

    def test_token_rocket(self):
        """
        Test "rocket" is normalised to "arugula"
        """
        tokens = ["rocket"]
        normalised_tokens = normalise_spelling(tokens)
        assert len(tokens) == len(normalised_tokens)
        assert normalised_tokens == ["arugula"]

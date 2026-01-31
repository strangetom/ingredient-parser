from ingredient_parser.en.foundationfoods._ff_dataclasses import IngredientToken
from ingredient_parser.en.foundationfoods._ff_utils import normalise_spelling


class TestNormaliseSpelling:
    def test_phrase(self):
        """
        Test "double cream" is normalised to "heavy cream"
        """
        tokens = ["doubl", "cream"]
        pos_tags = ["", ""]
        ing_tokens = [IngredientToken(t, p) for t, p in zip(tokens, pos_tags)]
        normalised_tokens = normalise_spelling(ing_tokens)
        assert len(tokens) == len(normalised_tokens)
        assert [t.token for t in normalised_tokens] == ["heavi", "cream"]

    def test_token_chilli(self):
        """
        Test "chilli" is normalised to "chili"
        """
        tokens = ["red", "hot", "chilli"]
        pos_tags = ["", "", ""]
        ing_tokens = [IngredientToken(t, p) for t, p in zip(tokens, pos_tags)]
        normalised_tokens = normalise_spelling(ing_tokens)
        assert len(tokens) == len(normalised_tokens)
        assert [t.token for t in normalised_tokens] == ["red", "hot", "chili"]

    def test_token_chile(self):
        """
        Test "chile" is normalised to "chili"
        """
        tokens = ["red", "hot", "chile"]
        pos_tags = ["", "", ""]
        ing_tokens = [IngredientToken(t, p) for t, p in zip(tokens, pos_tags)]
        normalised_tokens = normalise_spelling(ing_tokens)
        assert len(tokens) == len(normalised_tokens)
        assert [t.token for t in normalised_tokens] == ["red", "hot", "chili"]

    def test_token_rocket(self):
        """
        Test "rocket" is normalised to "arugula"
        """
        tokens = ["rocket"]
        pos_tags = [""]
        ing_tokens = [IngredientToken(t, p) for t, p in zip(tokens, pos_tags)]
        normalised_tokens = normalise_spelling(ing_tokens)
        assert len(tokens) == len(normalised_tokens)
        assert [t.token for t in normalised_tokens] == ["arugula"]

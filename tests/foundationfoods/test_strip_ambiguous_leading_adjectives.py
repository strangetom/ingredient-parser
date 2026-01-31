from ingredient_parser.en.foundationfoods._ff_dataclasses import IngredientToken
from ingredient_parser.en.foundationfoods._ff_utils import (
    strip_ambiguous_leading_adjectives,
)


class TestStripAmbiguousLeadingAdjectievs:
    def test_leading_ambiguous_adjective(self):
        """
        Test that "hot" is stripped from the start of tokens.
        """
        tokens = ["hot", "chicken", "stock"]
        pos_tags = ["JJ", "NN", "NN"]
        ing_tokens = [IngredientToken(t, p) for t, p in zip(tokens, pos_tags)]
        assert strip_ambiguous_leading_adjectives(ing_tokens) == ing_tokens[1:]

    def test_ambiguous_adjective_but_not_first(self):
        """
        Test that "hot" is not removed from okens.
        """
        tokens = ["red", "hot", "chilli"]
        pos_tags = ["JJ", "JJ", "NN"]
        ing_tokens = [IngredientToken(t, p) for t, p in zip(tokens, pos_tags)]
        assert strip_ambiguous_leading_adjectives(ing_tokens) == ing_tokens

    def test_all_ambiguous_adjectives(self):
        """
        Test that the input tokens are returned because they are all ambiguous
        adjectives.
        """
        tokens = ["hot", "hot", "hot"]
        pos_tags = ["JJ", "JJ", "JJ"]
        ing_tokens = [IngredientToken(t, p) for t, p in zip(tokens, pos_tags)]
        assert strip_ambiguous_leading_adjectives(ing_tokens) == ing_tokens

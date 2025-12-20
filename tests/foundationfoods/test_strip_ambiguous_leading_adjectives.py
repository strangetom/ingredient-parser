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
        assert strip_ambiguous_leading_adjectives(tokens, pos_tags) == tokens[1:]

    def test_ambiguous_adjective_but_not_first(self):
        """
        Test that "hot" is not removed from okens.
        """
        tokens = ["red", "hot", "chilli"]
        pos_tags = ["JJ", "JJ", "NN"]
        assert strip_ambiguous_leading_adjectives(tokens, pos_tags) == tokens

    def test_all_ambiguous_adjectives(self):
        """
        Test that the input tokens are returned because they are all ambiguous
        adjectives.
        """
        tokens = ["hot", "hot", "hot"]
        pos_tags = ["JJ", "JJ", "JJ"]
        assert strip_ambiguous_leading_adjectives(tokens, pos_tags) == tokens

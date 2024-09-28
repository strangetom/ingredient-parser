from ingredient_parser.dataclasses import FoudationFood
from ingredient_parser.en._foundationfoods import join_adjacent_FF_tokens


class TestFF_join_adjacent_FF_tokens:
    def test_single_FF_token(self):
        """
        Test 'milk' is only token returned
        """
        tokens = ["organic", "milk"]
        labels = ["NF", "FF"]
        scores = [0] * len(tokens)

        assert join_adjacent_FF_tokens(labels, tokens, scores) == [
            FoudationFood("milk", 0),
        ]

    def test_multiple_FF_token(self):
        """
        Test 'soy milk' tokens are joined and returned
        """
        tokens = ["organic", "soy", "milk"]
        labels = ["NF", "FF", "FF"]
        scores = [0] * len(tokens)

        assert join_adjacent_FF_tokens(labels, tokens, scores) == [
            FoudationFood("soy milk", 0),
        ]

    def test_split_FF_tokens(self):
        """
        Test 'milk' and "soy milk" are returned
        """
        tokens = ["organic", "milk", "and", "soy", "milk"]
        labels = ["NF", "FF", "NF", "FF", "FF"]
        scores = [0] * len(tokens)

        assert join_adjacent_FF_tokens(labels, tokens, scores) == [
            FoudationFood("milk", 0),
            FoudationFood("soy milk", 0),
        ]

    def test_no_FF_token(self):
        """
        Test empty list is returned
        """
        tokens = ["organic", "milk"]
        labels = ["NF", "NF"]
        scores = [0] * len(tokens)

        assert join_adjacent_FF_tokens(labels, tokens, scores) == []

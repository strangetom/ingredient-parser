from ingredient_parser.en._foundationfoods import join_adjacent_FF_tokens


class TestFF_join_adjacent_FF_tokens:
    def test_single_FF_token(self):
        """
        Test 'milk' is only token returned
        """
        tokens = ["organic", "milk"]
        labels = ["NF", "FF"]
        assert join_adjacent_FF_tokens(labels, tokens) == ["milk"]

    def test_multiple_FF_token(self):
        """
        Test 'soy milk' tokens are joined and returned
        """
        tokens = ["organic", "soy", "milk"]
        labels = ["NF", "FF", "FF"]
        assert join_adjacent_FF_tokens(labels, tokens) == ["soy milk"]

    def test_split_FF_tokens(self):
        """
        Test 'milk' and "soy milk" are returned
        """
        tokens = ["organic", "milk", "and", "soy", "milk"]
        labels = ["NF", "FF", "NF", "FF", "FF"]
        assert join_adjacent_FF_tokens(labels, tokens) == ["milk", "soy milk"]

    def test_no_FF_token(self):
        """
        Test empty list is returned
        """
        tokens = ["organic", "milk"]
        labels = ["NF", "NF"]
        assert join_adjacent_FF_tokens(labels, tokens) == []

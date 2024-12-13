from ingredient_parser.en import PostProcessor


class TestPostProcessor_is_singular:
    def test_is_singular(self):
        """
        Test that UNIT at index is indicated as singular
        """
        sentence = "4 salmon fillets 2 pounds each"
        tokens = ["4", "salmon", "fillets", "2", "pounds", "each"]
        token_labels = ["QTY", "NAME", "NAME", "QTY", "UNIT", "COMMENT"]
        name_labels = ["O", "B_NAME", "I_NAME", "O", "O", "O"]
        idx = [0, 1, 2, 3, 4, 5]

        p = PostProcessor(
            sentence, tokens, token_labels, name_labels, [0] * len(tokens)
        )
        assert p._is_singular(4, tokens, token_labels, idx)
        assert p.consumed == [5]

    def test_is_singular_in_brackets(self):
        """
        Test that UNIT at index is indicated as singular
        """
        sentence = "4 salmon fillets 2 pounds (900 g) each"
        tokens = ["4", "salmon", "fillets", "2", "pounds", "(", "900", "g", ")", "each"]
        token_labels = [
            "QTY",
            "NAME",
            "NAME",
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "COMMENT",
            "COMMENT",
        ]
        name_labels = ["O", "B_NAME", "I_NAME", "O", "O", "O", "O", "O", "O", "O"]
        idx = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        p = PostProcessor(
            sentence, tokens, token_labels, name_labels, [0] * len(tokens)
        )
        assert p._is_singular(7, tokens, token_labels, idx)
        assert p.consumed == [9]

    def test_not_singular(self):
        """
        Test that UNIT at index is not indicated as singular
        """
        sentence = "4 salmon fillets 2 pounds minimum"
        tokens = ["4", "salmon", "fillets", "2", "pounds", "minimum"]
        token_labels = ["QTY", "NAME", "NAME", "QTY", "UNIT", "COMMENT"]
        name_labels = ["O", "B_NAME", "I_NAME", "O", "O", "O"]
        idx = [0, 1, 2, 3, 4, 5]

        p = PostProcessor(
            sentence, tokens, token_labels, name_labels, [0] * len(tokens)
        )
        assert not p._is_singular(4, tokens, token_labels, idx)
        assert p.consumed == []

from ingredient_parser.en import PostProcessor


class TestPostProcessor_is_singular:
    def test_is_singular(self):
        """
        Test that UNIT at index is indicated as singular
        """
        sentence = "4 salmon fillets 2 pounds each"
        tokens = ["4", "salmon", "fillets", "2", "pounds", "each"]
        pos_tags = ["CD", "JJ", "NNS", "CD", "NNS", "DT"]
        labels = ["QTY", "B_NAME_TOK", "I_NAME_TOK", "QTY", "UNIT", "COMMENT"]
        idx = [0, 1, 2, 3, 4, 5]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert p._is_singular(4, tokens, labels, idx)
        assert p.consumed == [5]

    def test_is_singular_in_brackets(self):
        """
        Test that UNIT at index is indicated as singular
        """
        sentence = "4 salmon fillets 2 pounds (900 g) each"
        tokens = ["4", "salmon", "fillets", "2", "pounds", "(", "900", "g", ")", "each"]
        pos_tags = ["CD", "JJ", "NNS", "CD", "NNS", "(", "CD", "NN", ")", "DT"]
        labels = [
            "QTY",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "QTY",
            "UNIT",
            "COMMENT",
            "QTY",
            "UNIT",
            "COMMENT",
            "COMMENT",
        ]
        idx = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert p._is_singular(7, tokens, labels, idx)
        assert p.consumed == [9]

    def test_not_singular(self):
        """
        Test that UNIT at index is not indicated as singular
        """
        sentence = "4 salmon fillets 2 pounds minimum"
        tokens = ["4", "salmon", "fillets", "2", "pounds", "minimum"]
        pos_tags = ["CD", "JJ", "NNS", "CD", "NNS", "JJ"]
        labels = ["QTY", "B_NAME_TOK", "I_NAME_TOK", "QTY", "UNIT", "COMMENT"]
        idx = [0, 1, 2, 3, 4, 5]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert not p._is_singular(4, tokens, labels, idx)
        assert p.consumed == []

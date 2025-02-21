from ingredient_parser.en import PostProcessor


class TestPostProcessor_is_prepared:
    def test_is_prepared_to_make(self):
        """
        Test that QTY at index is indicated as prepared
        """
        sentence = "to make 5 cups orange juice"
        tokens = ["to", "make", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        idx = [0, 1, 2, 3, 4, 5]

        p = PostProcessor(sentence, tokens, labels, [0] * len(tokens))
        assert p._is_prepared(2, tokens, labels, idx)
        assert p.consumed == [1, 0]

    def test_is_prepared_to_yield(self):
        """
        Test that QTY at index is indicated as prepared
        """
        sentence = "to yield 5 cups orange juice"
        tokens = ["to", "yield", "5", "cups", "orange", "juice"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        idx = [0, 1, 2, 3, 4, 5]

        p = PostProcessor(sentence, tokens, labels, [0] * len(tokens))
        assert p._is_prepared(2, tokens, labels, idx)
        assert p.consumed == [1, 0]

    def test_is_prepared_and_approximate(self):
        """
        Test that QTY at index is indicated as prepared and approximate
        """
        sentence = "to yield about 250 g"
        tokens = ["to", "yield", "about", "250", "g"]
        labels = ["COMMENT", "COMMENT", "COMMENT", "QTY", "UNIT"]
        idx = [0, 1, 2, 3, 4, 5]

        p = PostProcessor(sentence, tokens, labels, [0] * len(tokens))
        assert p._is_prepared(3, tokens, labels, idx)
        assert p.consumed == [1, 0]

from ingredient_parser.en import PostProcessor


class TestPostProcessor_is_singular_and_approximate:
    def test_is_singular_and_approximate(self):
        """
        Test that QTY at index is indicated as approximate and singular
        """
        sentence = "each nearly 2 kg"
        tokens = ["each", "nearly", "2", "kg"]
        pos_tags = ["DT", "RB", "CD", "NN"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT"]
        idx = [0, 1, 2, 3]

        p = PostProcessor(
            sentence, tokens, pos_tags, labels, [0] * len(tokens), custom_units={}
        )
        assert p._is_singular_and_approximate(2, tokens, labels, idx)
        assert p.consumed == [1, 0]

    def test_is_singular_and_approximate_or_so(self):
        """
        Test that QTY at index is indicated as approximate and singular
        """
        sentence = "2 kg or so each"
        tokens = ["2", "kg", "or", "so", "each"]
        pos_tags = ["CD", "ND", "CC", "RB", "DT"]
        labels = ["QTY", "UNIT", "COMMENT", "COMMENT", "COMMENT"]
        idx = [0, 1, 2, 3, 4]

        p = PostProcessor(
            sentence, tokens, pos_tags, labels, [0] * len(tokens), custom_units={}
        )
        assert p._is_singular_and_approximate(1, tokens, labels, idx)
        assert p.consumed == [2, 3, 4]

    def test_not_singular_and_approximate(self):
        """
        Test that QTY at index is not indicated as approximate and singular
        """
        sentence = "both about 2 kg"
        tokens = ["both", "about", "2", "kg"]
        pos_tags = ["DT", "IN", "CD", "NNS"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT"]
        idx = [0, 1, 2, 3]

        p = PostProcessor(
            sentence, tokens, pos_tags, labels, [0] * len(tokens), custom_units={}
        )
        assert not p._is_singular_and_approximate(2, tokens, labels, idx)
        assert p.consumed == []

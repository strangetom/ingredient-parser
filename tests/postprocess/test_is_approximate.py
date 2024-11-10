from ingredient_parser.en import PostProcessor


class TestPostProcessor_is_approximate:
    def test_is_approximate_about(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "about 5 cups orange juice"
        tokens = ["about", "5", "cups", "orange", "juice"]
        pos_tags = ["IN", "CD", "NNS", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        idx = [0, 1, 2, 3, 4]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert p._is_approximate(1, tokens, labels, idx)
        assert p.consumed == [0]

    def test_is_approximate_approx_period(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "approx. 5 cups orange juice"
        tokens = ["approx", ".", "5", "cups", "orange", "juice"]
        pos_tags = ["NN", ".", "CD", "NN", "NN", "NN"]
        labels = ["COMMENT", "PUNC", "QTY", "UNIT", "NAME", "NAME"]
        idx = [0, 1, 2, 3, 4, 5]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert p._is_approximate(2, tokens, labels, idx)
        assert p.consumed == [1, 0]

    def test_is_approximate_approx(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "approx 5 cups orange juice"
        tokens = ["approx", "5", "cups", "orange", "juice"]
        pos_tags = ["RB", "CD", "NN", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        idx = [0, 1, 2, 3, 4]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert p._is_approximate(1, tokens, labels, idx)
        assert p.consumed == [0]

    def test_is_approximate_approximately(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "approximately 5 cups orange juice"
        tokens = ["approximately", "5", "cups", "orange", "juice"]
        pos_tags = ["RB", "CD", "NN", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        idx = [0, 1, 2, 3, 4]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert p._is_approximate(1, tokens, labels, idx)
        assert p.consumed == [0]

    def test_is_approximate_nearly(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "nearly 5 cups orange juice"
        tokens = ["nearly", "5", "cups", "orange", "juice"]
        pos_tags = ["RB", "CD", "JJ", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        idx = [0, 1, 2, 3, 4]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert p._is_approximate(1, tokens, labels, idx)
        assert p.consumed == [0]

    def test_not_approximate(self):
        """
        Test that QTY at index is not indicated as approximate
        """
        sentence = "maximum 5 cups orange juice"
        tokens = ["maximum", "5", "cups", "orange", "juice"]
        pos_tags = ["JJ", "CD", "NN", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "NAME", "NAME"]
        idx = [0, 1, 2, 3, 4]

        p = PostProcessor(sentence, tokens, pos_tags, labels, [0] * len(tokens))
        assert not p._is_approximate(1, tokens, labels, idx)
        assert p.consumed == []

from ingredient_parser.dataclasses import LabelledToken
from ingredient_parser.en import PostProcessor


class TestPostProcessor_is_approximate:
    def test_is_approximate_about(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "about 5 cups orange juice"
        tokens = ["about", "5", "cups", "orange", "juice"]
        pos_tags = ["IN", "CD", "NNS", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_approximate(1, labelled_tokens)
        assert p.consumed == [0]

    def test_is_approximate_approx_period(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "approx. 5 cups orange juice"
        tokens = ["approx", ".", "5", "cups", "orange", "juice"]
        pos_tags = ["NN", ".", "CD", "NNS", "NN", "NN"]
        labels = ["COMMENT", "PUNC", "QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_approximate(2, labelled_tokens)
        assert p.consumed == [1, 0]

    def test_is_approximate_approx(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "approx 5 cups orange juice"
        tokens = ["approx", "5", "cups", "orange", "juice"]
        pos_tags = ["RB", "CD", "NNS", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_approximate(1, labelled_tokens)
        assert p.consumed == [0]

    def test_is_approximate_approximately(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "approximately 5 cups orange juice"
        tokens = ["approximately", "5", "cups", "orange", "juice"]
        pos_tags = ["RB", "CD", "NNS", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_approximate(1, labelled_tokens)
        assert p.consumed == [0]

    def test_is_approximate_nearly(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "nearly 5 cups orange juice"
        tokens = ["nearly", "5", "cups", "orange", "juice"]
        pos_tags = ["RB", "CD", "NNS", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_approximate(1, labelled_tokens)
        assert p.consumed == [0]

    def test_is_approximate_generous(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "6 generous cups orange juice"
        tokens = ["6", "generous", "cups", "orange", "juice"]
        pos_tags = ["CD", "JJ", "NNS", "NN", "NN"]
        labels = ["QTY", "UNIT", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_approximate(2, labelled_tokens)
        assert p.consumed == [1]

    def test_is_approximate_or_so_quantity(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "48 or so small black and green olives"
        tokens = ["48", "or", "so", "small", "black", "and", "green", "olives"]
        pos_tags = ["CD", "CC", "RB", "JJ", "JJ", "CC", "JJ", "NNS"]
        labels = [
            "QTY",
            "COMMENT",
            "COMMENT",
            "SIZE",
            "NAME_VAR",
            "NAME_SEP",
            "NAME_VAR",
            "B_NAME_TOK",
        ]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_approximate(0, labelled_tokens)
        assert p.consumed == [1, 2]

    def test_is_approximate_or_so_unit(self):
        """
        Test that QTY at index is indicated as approximate
        """
        sentence = "2/3 cup or so low-fat milk"
        tokens = ["#2$3", "cup", "or", "so", "low-fat", "milk"]
        pos_tags = ["CD", "NN", "CC", "RB", "JJ", "NN"]
        labels = ["QTY", "UNIT", "COMMENT", "COMMENT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_approximate(1, labelled_tokens)
        assert p.consumed == [2, 3]

    def test_not_approximate(self):
        """
        Test that QTY at index is not indicated as approximate
        """
        sentence = "maximum 5 cups orange juice"
        tokens = ["maximum", "5", "cups", "orange", "juice"]
        pos_tags = ["JJ", "CD", "NNS", "NN", "NN"]
        labels = ["COMMENT", "QTY", "UNIT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert not p._is_approximate(1, labelled_tokens)
        assert p.consumed == []

from ingredient_parser.dataclasses import LabelledToken
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
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_singular_and_approximate(2, labelled_tokens)
        assert p.consumed == [1, 0]

    def test_is_singular_and_approximate_or_so(self):
        """
        Test that QTY at index is indicated as approximate and singular
        """
        sentence = "2 kg or so each"
        tokens = ["2", "kg", "or", "so", "each"]
        pos_tags = ["CD", "ND", "CC", "RB", "DT"]
        labels = ["QTY", "UNIT", "COMMENT", "COMMENT", "COMMENT"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_singular_and_approximate(1, labelled_tokens)
        assert p.consumed == [2, 3, 4]

    def test_not_singular_and_approximate(self):
        """
        Test that QTY at index is not indicated as approximate and singular
        """
        sentence = "both about 2 kg"
        tokens = ["both", "about", "2", "kg"]
        pos_tags = ["DT", "IN", "CD", "NNS"]
        labels = ["COMMENT", "COMMENT", "QTY", "UNIT"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert not p._is_singular_and_approximate(2, labelled_tokens)
        assert p.consumed == []

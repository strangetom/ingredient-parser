from ingredient_parser.dataclasses import LabelledToken
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
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_singular(4, labelled_tokens)
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
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert p._is_singular(7, labelled_tokens)
        assert p.consumed == [9]

    def test_not_singular(self):
        """
        Test that UNIT at index is not indicated as singular
        """
        sentence = "4 salmon fillets 2 pounds minimum"
        tokens = ["4", "salmon", "fillets", "2", "pounds", "minimum"]
        pos_tags = ["CD", "JJ", "NNS", "CD", "NNS", "JJ"]
        labels = ["QTY", "B_NAME_TOK", "I_NAME_TOK", "QTY", "UNIT", "COMMENT"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        assert not p._is_singular(4, labelled_tokens)
        assert p.consumed == []

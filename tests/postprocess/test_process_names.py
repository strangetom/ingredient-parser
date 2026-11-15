from ingredient_parser.dataclasses import IngredientText, LabelledToken
from ingredient_parser.en import PostProcessor


class TestPostProcessor_postprocess_names:
    def test_single_name(self):
        """
        Test that a list containing a single IngredientText object is returned
        """
        sentence = "2 14 ounce cans of coconut milk"
        tokens = ["2", "14", "ounce", "can", "of", "coconut", "milk"]
        pos_tags = ["CD", "CD", "NN", "MD", "IN", "NN", "NN"]
        labels = ["QTY", "QTY", "UNIT", "UNIT", "COMMENT", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        expected = [
            IngredientText(text="coconut milk", confidence=0, starting_index=5),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

    def test_multiple_independent_names(self):
        """
        Test that a list containing two IngredientText objects is returned
        """
        sentence = "2 tbsp butter or olive oil"
        tokens = ["2", "tbsp", "butter", "or", "olive", "oil"]
        pos_tags = ["CD", "JJ", "NN", "CC", "JJ", "NN"]
        labels = ["QTY", "UNIT", "B_NAME_TOK", "NAME_SEP", "B_NAME_TOK", "I_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        expected = [
            IngredientText(text="butter", confidence=0, starting_index=2),
            IngredientText(text="olive oil", confidence=0, starting_index=4),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

    def test_multiple_variant_names(self):
        """
        Test that a list containing two IngredientText objects is returned
        """
        sentence = "2 cups beef or vegetable stock"
        tokens = ["2", "cup", "beef", "or", "vegetable", "stock"]
        pos_tags = ["CD", "NN", "NN", "CC", "JJ", "NN"]
        labels = ["QTY", "UNIT", "NAME_VAR", "NAME_SEP", "NAME_VAR", "B_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        expected = [
            IngredientText(text="beef stock", confidence=0, starting_index=2),
            IngredientText(text="vegetable stock", confidence=0, starting_index=4),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

    def test_multiple_modified_names(self):
        """
        Test that a list containing two IngredientText objects is returned
        """
        sentence = "1 handful of fresh basil or coriander"
        tokens = ["1", "handful", "of", "fresh", "basil", "or", "coriander"]
        pos_tags = ["CD", "NN", "IN", "JJ", "NN", "CC", "NN"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "NAME_MOD",
            "B_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
        ]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        expected = [
            IngredientText(text="fresh basil", confidence=0, starting_index=3),
            IngredientText(text="fresh coriander", confidence=0, starting_index=3),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

    def test_multiple_modified_variant_names(self):
        """
        Test that a list containing two IngredientText objects is returned
        """
        sentence = "2 cups hot beef or vegetable stock"
        tokens = ["2", "cup", "hot", "beef", "or", "vegetable", "stock"]
        pos_tags = ["CD", "NN", "JJ", "NN", "CC", "JJ", "NN"]
        labels = [
            "QTY",
            "UNIT",
            "NAME_MOD",
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

        expected = [
            IngredientText(text="hot beef stock", confidence=0, starting_index=2),
            IngredientText(text="hot vegetable stock", confidence=0, starting_index=2),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

    def test_deuplicate_ingredient_names(self):
        """
        Test that a list containing one IngredientText objects is returned
        """
        sentence = "1/2 cup sugar plus 1 1/2 tablespoons sugar"
        tokens = ["#1$2", "cup", "sugar", "plus", "1#1$2", "tablespoon", "sugar"]
        pos_tags = ["CD", "NN", "NN", "CC", "CD", "NN", "NN"]
        labels = ["QTY", "UNIT", "B_NAME_TOK", "COMMENT", "QTY", "UNIT", "B_NAME_TOK"]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        expected = [
            IngredientText(text="sugar", confidence=0, starting_index=2),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

    def test_or_a_mixture(self):
        """
        Test that a list containing one IngredientText objects is returned
        """
        sentence = "3 pounds bone-in chicken thighs or drumsticks (or a mixture)"
        tokens = [
            "3",
            "pound",
            "bone-in",
            "chicken",
            "thighs",
            "or",
            "drumsticks",
            "(",
            "or",
            "a",
            "mixture",
            ")",
        ]
        pos_tags = [
            "CD",
            "NNS",
            "JJ",
            "NN",
            "NNS",
            "CC",
            "NNS",
            "(",
            "CC",
            "DT",
            "NN",
            ")",
        ]
        labels = [
            "QTY",
            "UNIT",
            "NAME_MOD",
            "NAME_MOD",
            "B_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
            "PUNC",
            "NAME_SEP",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "PUNC",
        ]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=False
            )
            for i, (text, tag, label) in enumerate(zip(tokens, pos_tags, labels))
        ]

        expected = [
            IngredientText(
                text="bone-in chicken thighs", confidence=0, starting_index=2
            ),
            IngredientText(
                text="bone-in chicken drumsticks", confidence=0, starting_index=2
            ),
            IngredientText(text="a mixture", confidence=0, starting_index=9),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

    def test_multiple_modified_and_multiple_variant_names(self):
        """
        Test that a list containing one IngredientText objects is returned
        """
        sentence = "6 fresh or dry Indian or regular bay leaves"
        tokens = ["6", "fresh", "or", "dry", "Indian", "or", "regular", "bay", "leaf"]
        pos_tags = ["CD", "JJ", "CC", "JJ", "JJ", "CC", "JJ", "NN", "NNS"]
        labels = [
            "QTY",
            "NAME_MOD",
            "NAME_SEP",
            "NAME_MOD",
            "NAME_VAR",
            "NAME_SEP",
            "NAME_VAR",
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        plurals = [False, False, False, False, False, False, False, False, True]
        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=plural
            )
            for i, (text, tag, label, plural) in enumerate(
                zip(tokens, pos_tags, labels, plurals)
            )
        ]

        expected = [
            IngredientText(
                text="fresh Indian bay leaves", confidence=0, starting_index=1
            ),
            IngredientText(
                text="fresh regular bay leaves", confidence=0, starting_index=1
            ),
            IngredientText(
                text="dry Indian bay leaves", confidence=0, starting_index=3
            ),
            IngredientText(
                text="dry regular bay leaves", confidence=0, starting_index=3
            ),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

    def test_multiple_modified_and_multiple_variant_names_with_mixture(self):
        """
        Test that a list containing one IngredientText objects is returned
        """
        sentence = (
            "2 cups cooked medium-grain or long-grain white or brown rice or a mix"
        )
        tokens = [
            "2",
            "cup",
            "cooked",
            "medium-grain",
            "or",
            "long-grain",
            "white",
            "or",
            "brown",
            "rice",
            "or",
            "a",
            "mix",
        ]
        pos_tags = [
            "CD",
            "NNS",
            "VBD",
            "NN",
            "CC",
            "JJ",
            "JJ",
            "CC",
            "JJ",
            "NN",
            "CC",
            "DT",
            "NN",
        ]
        labels = [
            "QTY",
            "UNIT",
            "PREP",
            "NAME_MOD",
            "NAME_SEP",
            "NAME_MOD",
            "NAME_VAR",
            "NAME_SEP",
            "NAME_VAR",
            "B_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]

        plurals = [
            False,
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        ]

        labelled_tokens = [
            LabelledToken(
                index=i, text=text, pos_tag=tag, label=label, score=0, plural=plural
            )
            for i, (text, tag, label, plural) in enumerate(
                zip(tokens, pos_tags, labels, plurals)
            )
        ]

        expected = [
            IngredientText(
                text="medium-grain white rice", confidence=0, starting_index=3
            ),
            IngredientText(
                text="medium-grain brown rice", confidence=0, starting_index=3
            ),
            IngredientText(
                text="long-grain white rice", confidence=0, starting_index=5
            ),
            IngredientText(
                text="long-grain brown rice", confidence=0, starting_index=5
            ),
            IngredientText(text="a mix", confidence=0, starting_index=11),
        ]

        p = PostProcessor(sentence, labelled_tokens, custom_units={})
        names, _ = p._postprocess_names()
        assert names == expected

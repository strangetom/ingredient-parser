from ingredient_parser.dataclasses import IngredientText
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
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="coconut milk", confidence=0, starting_index=5),
        ]

        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)
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
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="butter", confidence=0, starting_index=2),
            IngredientText(text="olive oil", confidence=0, starting_index=4),
        ]

        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)
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
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="beef stock", confidence=0, starting_index=2),
            IngredientText(text="vegetable stock", confidence=0, starting_index=4),
        ]

        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)
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
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="fresh basil", confidence=0, starting_index=3),
            IngredientText(text="fresh coriander", confidence=0, starting_index=3),
        ]

        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)
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
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="hot beef stock", confidence=0, starting_index=2),
            IngredientText(text="hot vegetable stock", confidence=0, starting_index=2),
        ]

        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)
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
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="sugar", confidence=0, starting_index=2),
        ]

        p = PostProcessor(sentence, tokens, pos_tags, labels, scores)
        names, _ = p._postprocess_names()
        assert names == expected

from ingredient_parser.dataclasses import IngredientText
from ingredient_parser.en import PostProcessor


class TestPostProcessor_postprocess_names:
    def test_single_name(self):
        """
        Test that a list containing a single IngredientText object is returned
        """
        sentence = "2 14 ounce cans of coconut milk"
        tokens = ["2", "14", "ounce", "can", "of", "coconut", "milk"]
        labels = ["QTY", "QTY", "UNIT", "UNIT", "COMMENT", "B_NAME_TOK", "I_NAME_TOK"]
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="coconut milk", confidence=0, starting_index=5),
        ]

        p = PostProcessor(sentence, tokens, labels, scores)
        assert p._postprocess_names() == expected

    def test_multiple_independent_names(self):
        """
        Test that a list containing two IngredientText objects is returned
        """
        sentence = "2 tbsp butter or olive oil"
        tokens = ["2", "tbsp", "butter", "or", "olive", "oil"]
        labels = ["QTY", "UNIT", "B_NAME_TOK", "NAME_SEP", "B_NAME_TOK", "I_NAME_TOK"]
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="butter", confidence=0, starting_index=2),
            IngredientText(text="olive oil", confidence=0, starting_index=4),
        ]

        p = PostProcessor(sentence, tokens, labels, scores)
        assert p._postprocess_names() == expected

    def test_multiple_variant_names(self):
        """
        Test that a list containing two IngredientText objects is returned
        """
        sentence = "2 cups beef or vegetable stock"
        tokens = ["2", "cup", "beef", "or", "vegetable", "stock"]
        labels = ["QTY", "UNIT", "B_NAME_VAR", "NAME_SEP", "B_NAME_VAR", "B_NAME_TOK"]
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="beef stock", confidence=0, starting_index=2),
            IngredientText(text="vegetable stock", confidence=0, starting_index=4),
        ]

        p = PostProcessor(sentence, tokens, labels, scores)
        assert p._postprocess_names() == expected

    def test_multiple_modified_names(self):
        """
        Test that a list containing two IngredientText objects is returned
        """
        sentence = "1 handful of fresh basil or coriander"
        tokens = ["1", "handful", "of", "fresh", "basil", "or", "coriander"]
        labels = [
            "QTY",
            "UNIT",
            "COMMENT",
            "B_NAME_MOD",
            "B_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="fresh basil", confidence=0, starting_index=3),
            IngredientText(text="fresh coriander", confidence=0, starting_index=3),
        ]

        p = PostProcessor(sentence, tokens, labels, scores)
        assert p._postprocess_names() == expected

    def test_multiple_modified_variant_names(self):
        """
        Test that a list containing two IngredientText objects is returned
        """
        sentence = "2 cups hot beef or vegetable stock"
        tokens = ["2", "cup", "hot", "beef", "or", "vegetable", "stock"]
        labels = [
            "QTY",
            "UNIT",
            "B_NAME_MOD",
            "B_NAME_VAR",
            "NAME_SEP",
            "B_NAME_VAR",
            "B_NAME_TOK",
        ]
        scores = [0.0] * len(tokens)

        expected = [
            IngredientText(text="hot beef stock", confidence=0, starting_index=2),
            IngredientText(text="hot vegetable stock", confidence=0, starting_index=2),
        ]

        p = PostProcessor(sentence, tokens, labels, scores)
        assert p._postprocess_names() == expected

from ingredient_parser.en._loaders import load_pos_tagger_model
from ingredient_parser.en.foundationfoods._ff_utils import (
    TokenizedFDCDescription,
    tokenize_fdc_description,
)


class TestTokenizeFDCDescription:
    def test_simple_description(self):
        """
        Test that the description is tokenized and stemmed and all tokens have weight 1.
        """
        tagger = load_pos_tagger_model()

        description = "Vegetable chips"

        expected_tokens = ["veget", "chip"]
        expected_pos_tags = ["JJ", "NNS"]
        expected_weights = [1.0, 1.0]
        with tagger.cache_context() as t:
            assert tokenize_fdc_description(
                description, t.tag_with_cache
            ) == TokenizedFDCDescription(
                tokens=expected_tokens,
                pos_tags=expected_pos_tags,
                embedding_tokens=expected_tokens,
                embedding_pos_tags=expected_pos_tags,
                embedding_weights=expected_weights,
            )

    def test_multiple_phrase_weights(self):
        """
        Test that the weights for tokens in each phrase decrease with each phrase.
        """
        tagger = load_pos_tagger_model()

        description = "Chicken, thigh, meat and skin, raw"

        expected_tokens = ["chicken", "thigh", "meat", "and", "skin", "raw"]
        expected_pos_tags = ["NN", "NN", "NN", "CC", "NN", "JJ"]
        expected_weights = [
            1.0,
            1.0 - 1e-3,
            1.0 - 2e-3,
            1.0 - 2e-3,
            1.0 - 2e-3,
            1.0 - 3e-3,
        ]
        with tagger.cache_context() as t:
            assert tokenize_fdc_description(
                description, t.tag_with_cache
            ) == TokenizedFDCDescription(
                tokens=expected_tokens,
                pos_tags=expected_pos_tags,
                embedding_tokens=expected_tokens,
                embedding_pos_tags=expected_pos_tags,
                embedding_weights=expected_weights,
            )

    def test_negated_tokens(self):
        """
        Test that negated tokens and the following tokens within the same phrase have 0
        weight.
        """
        tagger = load_pos_tagger_model()

        description = "Chicken, canned, no broth"

        expected_tokens = ["chicken", "can", "no", "broth"]
        expected_pos_tags = ["NN", "VBN", "DT", "NN"]
        expected_weights = [1.0, 1.0 - 1e-3, 0, 0]
        with tagger.cache_context() as t:
            assert tokenize_fdc_description(
                description, t.tag_with_cache
            ) == TokenizedFDCDescription(
                tokens=expected_tokens,
                pos_tags=expected_pos_tags,
                embedding_tokens=expected_tokens,
                embedding_pos_tags=expected_pos_tags,
                embedding_weights=expected_weights,
            )

    def test_reduced_relevance_tokens(self):
        """
        Test that reduced relevance tokens and the following tokens within the same
        phrase have reduced weight.
        """
        tagger = load_pos_tagger_model()

        description = "Chicken, canned, with broth"

        expected_tokens = ["chicken", "can", "with", "broth"]
        expected_pos_tags = ["NN", "VBN", "IN", "NN"]
        expected_weights = [1.0, 1.0 - 1e-3, 1 - 0.5 - 2e-3, 1 - 0.5 - 2e-3]
        with tagger.cache_context() as t:
            assert tokenize_fdc_description(
                description, t.tag_with_cache
            ) == TokenizedFDCDescription(
                tokens=expected_tokens,
                pos_tags=expected_pos_tags,
                embedding_tokens=expected_tokens,
                embedding_pos_tags=expected_pos_tags,
                embedding_weights=expected_weights,
            )

    def test_percentage_range(self):
        """
        Test that the upper and lower limits of a percentage range are retained with the
        percentage sign.
        """
        tagger = load_pos_tagger_model()

        description = "Chocolate, dark, 60-69% cacao solids"

        expected_tokens = ["chocol", "dark", "60%", "69%", "cacao", "solid"]
        expected_pos_tags = ["NN", "JJ", "NN", "NN", "NN", "NNS"]
        expected_weights = [1.0, 1.0 - 1e-3, 1 - 2e-3, 1 - 2e-3, 1 - 2e-3, 1 - 2e-3]
        with tagger.cache_context() as t:
            assert tokenize_fdc_description(
                description, t.tag_with_cache
            ) == TokenizedFDCDescription(
                tokens=expected_tokens,
                pos_tags=expected_pos_tags,
                embedding_tokens=expected_tokens,
                embedding_pos_tags=expected_pos_tags,
                embedding_weights=expected_weights,
            )

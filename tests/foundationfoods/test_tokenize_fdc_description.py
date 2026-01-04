from ingredient_parser.en.foundationfoods._ff_utils import (
    TokenizedFDCDescription,
    tokenize_fdc_description,
)


class TestTokenizeFDCDescription:
    def test_simple_description(self):
        """
        Test that the description is tokenized and stemmed and all tokens have wieght 1.
        """
        description = "Vegetable chips"

        expected_tokens = ["veget", "chip"]
        expected_weights = [1.0, 1.0]
        assert tokenize_fdc_description(description) == TokenizedFDCDescription(
            tokens=expected_tokens,
            embedding_tokens=expected_tokens,
            embedding_weights=expected_weights,
        )

    def test_multiple_phrase_weights(self):
        """
        Test that the weights for tokens in each phrase descrease with each phrase.
        """
        description = "Chicken, thigh, meat and skin, raw"

        expected_tokens = ["chicken", "thigh", "meat", "and", "skin", "raw"]
        expected_weights = [
            1.0,
            1.0 - 1e-3,
            1.0 - 2e-3,
            1.0 - 2e-3,
            1.0 - 2e-3,
            1.0 - 3e-3,
        ]
        assert tokenize_fdc_description(description) == TokenizedFDCDescription(
            tokens=expected_tokens,
            embedding_tokens=expected_tokens,
            embedding_weights=expected_weights,
        )

    def test_negated_tokens(self):
        """
        Test that negated tokens and the following tokens within the same phrase have 0
        weight.
        """
        description = "Chicken, canned, no broth"

        expected_tokens = ["chicken", "can", "no", "broth"]
        expected_weights = [1.0, 1.0 - 1e-3, 0, 0]
        assert tokenize_fdc_description(description) == TokenizedFDCDescription(
            tokens=expected_tokens,
            embedding_tokens=expected_tokens,
            embedding_weights=expected_weights,
        )

    def test_reduced_relevance_tokens(self):
        """
        Test that reduced relevance tokens and the following tokens within the same
        phrase have reduced weight.
        """
        description = "Chicken, canned, with broth"

        expected_tokens = ["chicken", "can", "with", "broth"]
        expected_weights = [1.0, 1.0 - 1e-3, 1 - 0.5 - 2e-3, 1 - 0.5 - 2e-3]
        assert tokenize_fdc_description(description) == TokenizedFDCDescription(
            tokens=expected_tokens,
            embedding_tokens=expected_tokens,
            embedding_weights=expected_weights,
        )

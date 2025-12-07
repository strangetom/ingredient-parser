#!/usr/bin/env python3

from collections import defaultdict
from functools import lru_cache

import numpy as np

from .._embeddings import GloVeModel
from .._loaders import load_embeddings_model
from ._ff_dataclasses import FDCIngredient, FDCIngredientMatch
from ._ff_utils import load_fdc_ingredients, prepare_embeddings_tokens


class uSIF:
    """Modified implementation of Unsupervised Smooth Inverse Frequency [1]_ weighting
    scheme for calculation of sentence embedding vectors.

    This implementation is modified from the reference to not implement the piecewise
    common component removal, primarily to avoid introducing a new dependency.

    References
    ----------
    .. [1] Kawin Ethayarajh. 2018. Unsupervised Random Walk Sentence Embeddings: A
       Strong but Simple Baseline. In Proceedings of the Third Workshop on
       Representation Learning for NLP, pages 91–100, Melbourne, Australia. Association
       for Computational Linguistics. https://aclanthology.org/W18-3012/

    Attributes
    ----------
    a : float
        'a' parameter.
    embeddings : GloVeModel
        GloVe embeddings model.
    embeddings_dimension : int
        Dimension of embeddings model.
    fdc_ingredients : list[FDCIngredient]
        Lists of FDC ingredients.
    fdc_vectors : dict[str, list[FDCIngredient]]
        Lists of embedding vectors for FDC ingredients, grouped by data type.
    min_prob : float
        Minimum token probability.
    token_prob : dict[str, float]
        Dictionary of token probabilities.
    """

    def __init__(self, embeddings: GloVeModel, fdc_ingredients: list[FDCIngredient]):
        """Initialize.

        Parameters
        ----------
        embeddings : GloVeModel
            GloVe embeddings model.
        fdc_ingredients : list[FDCIngredient]
            List of FDC ingredients.
        """
        self.embeddings = embeddings
        self.embeddings_dimension: int = embeddings.dimension

        self.fdc_ingredients: list[FDCIngredient] = fdc_ingredients
        self.token_prob: dict[str, float] = self._estimate_token_probability(
            self.fdc_ingredients
        )
        self.min_prob: float = min(self.token_prob.values())
        self.a: float = self._calculate_a_factor()

        self.fdc_vectors = self._embed_fdc_ingredients()

    def _estimate_token_probability(
        self, fdc_ingredients: list[FDCIngredient]
    ) -> dict[str, float]:
        """Estimate word probability from the frequency of occurrence of token in FDC
        ingredient descriptions.

        Parameters
        ----------
        fdc_ingredients : list[FDCIngredient]
            List of FDC ingredient objects.

        Returns
        -------
        dict[str, float]
            Dict of token: probability.
        """
        token_counts = defaultdict(int)
        for ingredient in fdc_ingredients:
            for token in ingredient.tokens:
                token_counts[token] += 1

        total = sum(token_counts.values())
        return {token: count / total for token, count in token_counts.items()}

    def _average_sentence_length(self) -> int:
        """Calculate average sentence length for FDC ingredient descriptions.

        Returns
        -------
        int
            Average sentence length.
        """
        token_count = 0
        sentence_count = 0
        for fdc in self.fdc_ingredients:
            token_count += len(fdc.tokens)
            sentence_count += 1

        return int(token_count / sentence_count)

    def _calculate_a_factor(self) -> float:
        """Calculate 'a' factor used in token weight calculations.

        Returns
        -------
        float
            'a' factor.
        """
        average_sentence_length = self._average_sentence_length()

        vocab_size = float(len(self.token_prob))
        threshold = 1 - (1 - 1 / vocab_size) ** average_sentence_length
        alpha = (
            len([token for token, prob in self.token_prob.items() if prob > threshold])
            / vocab_size
        )
        Z = 0.5 * vocab_size
        return (1 - alpha) / (alpha * Z)

    def _weight(self, token: str) -> float:
        """Return weight for token.

        Parameters
        ----------
        token : str
            Token.

        Returns
        -------
        float
            Token weight.
        """
        return self.a / (0.5 * self.a + self.token_prob.get(token, self.min_prob))

    def _embed_fdc_ingredients(self) -> list[np.ndarray]:
        """Calculate embedding vectors for all FDC ingredients.

        Returns
        -------
        list[np.ndarray]
            List of embedding vectors for FDC ingredients.
        """
        return [self._embed(fdc.tokens) for fdc in self.fdc_ingredients]

    def _embed(self, tokens: list[str]) -> np.ndarray:
        """Return single embedding vector for input tokens calculated from the weighted
        mean of the embeddings for each token.

        Parameters
        ----------
        tokens : list[str]
            List of input tokens.

        Returns
        -------
        np.ndarray
            Embedding vector for input.
        """
        tokens_in_vocab = [t for t in tokens if t in self.embeddings]

        if not tokens_in_vocab:
            return np.zeros(self.embeddings_dimension) + self.a
        else:
            token_vectors = np.array(
                [self.embeddings[token] for token in tokens_in_vocab]
            )
            normalised = token_vectors * (1.0 / np.linalg.norm(token_vectors, axis=0))
            weighted = np.array(
                [
                    self._weight(token) * normalised[i, :]
                    for i, token in enumerate(tokens_in_vocab)
                ]
            )
            return np.mean(weighted, axis=0)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Return cosine similarity score for input vectors.

        Parameters
        ----------
        vec1 : np.ndarray
            Input vector 1.
        vec2 : np.ndarray
            Input vector 2.

        Returns
        -------
        float
            Cosine similarity score.
        """
        return 1 - float(
            np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        )

    def score_matches(self, tokens: list[str]) -> list[FDCIngredientMatch]:
        """Find best candidate matches between input token and FDC ingredients with a
        cosine similarity of no more than cutoff.

        Parameters
        ----------
        tokens : list[str]
            List of tokens.

        Returns
        -------
        list[FDCIngredientMatch]
            List of best n candidate matching FDC ingredients.
        """
        prepared_tokens = prepare_embeddings_tokens(tuple(tokens))
        input_token_vector = self._embed(prepared_tokens)

        candidates = []
        for idx, vec in enumerate(self.fdc_vectors):
            score = self._cosine_similarity(input_token_vector, vec)
            candidates.append(
                FDCIngredientMatch(
                    fdc=self.fdc_ingredients[idx],
                    score=score,
                )
            )

        sorted_candidates = sorted(candidates, key=lambda x: x.score)
        return sorted_candidates


@lru_cache
def get_usif_matcher() -> uSIF:
    """Cached function for returning instantiated uSIF object.

    Returns
    -------
    uSIF
        Instantiation uSIF object.
    """
    embeddings = load_embeddings_model()
    fdc_ingredients = load_fdc_ingredients()
    return uSIF(embeddings, fdc_ingredients)

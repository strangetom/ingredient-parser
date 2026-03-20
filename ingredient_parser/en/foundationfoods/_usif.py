#!/usr/bin/env python3

import logging
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .._embeddings import GloVeModel
from .._loaders import load_embeddings_model
from ._ff_dataclasses import FDCIngredient, FDCIngredientMatch, IngredientToken
from ._ff_utils import load_fdc_ingredients

logger = logging.getLogger("ingredient-parser.foundation-foods.usif")


@dataclass
class Embedding:
    """Dataclass for holding an embedding vector and it's norm."""

    vec: np.ndarray
    norm: np.floating


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
            for token in ingredient.embedding_tokens:
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
            token_count += len(fdc.embedding_tokens)
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

    def _weight(self, token: str, pos_tag: str) -> float:
        """Return weight for token.

        This calculation is modified from the original papers [1]_ to add a multiplier
        to the weight based on the part of speech tag.
        The weight of a token is related to it's frequency in the corpus used to
        calculate the "a" factor - the idea being that more frequent tokens convey less
        useful meaning than lower frequency tokens.
        In this particular application, that isn't stictly true. The name of an
        ingredient conveys a lot of meaning but often occurs frequently in multiple
        entries in the FDC data. Therefore, we include a multiplier to the weight to
        increase the weight for nouns (i.e. ingredient names) and decrease it for verbs
        and adjectives (i.e. descriptive tokens).

        Parameters
        ----------
        token : str
            Token.
        pos_tag : str
            Part of speech of token.

        Returns
        -------
        float
            Token weight.
        """
        weight = self.a / (0.5 * self.a + self.token_prob.get(token, self.min_prob))
        if pos_tag.startswith("NN"):
            return 1.2 * weight
        elif pos_tag.startswith("JJ"):
            return 1.05 * weight
        elif pos_tag.startswith("VB"):
            return 0.7 * weight
        else:
            return weight

    def _embed_fdc_ingredients(self) -> list[Embedding]:
        """Calculate embedding vectors for all FDC ingredients.

        Returns
        -------
        list[Embedding]
            List of embedding vectors for FDC ingredients.
        """
        embedded = []
        for fdc in self.fdc_ingredients:
            vec = self._embed(
                fdc.embedding_tokens, fdc.embedding_pos_tags, fdc.embedding_weights
            )
            norm = np.linalg.norm(vec)
            embedded.append(
                Embedding(
                    vec=vec,
                    norm=norm,
                )
            )

        return embedded

    def _embed(
        self, tokens: list[str], pos_tags: list[str], phrase_weight: list[float]
    ) -> np.ndarray:
        """Return single embedding vector for input tokens calculated from the weighted
        mean of the embeddings for each token.

        Parameters
        ----------
        tokens : list[str]
            List of input tokens.
        pos_tags : list[str]
            List of part of speech tags for tokens.
        phrase_weight : list[float]
            List of weight based on phrase position.

        Returns
        -------
        np.ndarray
            Embedding vector for input.
        """
        tokens_in_vocab = [
            (t, p, w)
            for t, p, w in zip(tokens, pos_tags, phrase_weight)
            if t in self.embeddings
        ]

        if not tokens_in_vocab:
            return np.zeros(self.embeddings_dimension) + self.a
        else:
            token_vectors = np.array(
                [self.embeddings[token] for token, _, _ in tokens_in_vocab]
            )
            normalised = token_vectors * (1.0 / np.linalg.norm(token_vectors, axis=0))
            weighted = np.array(
                [
                    phrase_weight * self._weight(token, pos_tag) * normalised[i, :]
                    for i, (token, pos_tag, phrase_weight) in enumerate(tokens_in_vocab)
                ]
            )
            return np.mean(weighted, axis=0)

    def _cosine_similarity(self, vec1: Embedding, vec2: Embedding) -> float:
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
        return 1 - float(np.dot(vec1.vec, vec2.vec) / (vec1.norm * vec2.norm))

    def rank_matches(self, tokens: list[IngredientToken]) -> list[FDCIngredientMatch]:
        """Rank and score FDC Ingredients according to closest match to tokens.

        Parameters
        ----------
        tokens : list[str]
            List of tokens.

        Returns
        -------
        list[FDCIngredientMatch]
            Scored FDC ingredients, sorted by best first.
        """
        vec = self._embed(
            [t.token for t in tokens], [t.pos_tag for t in tokens], [1] * len(tokens)
        )
        input_token_vector = Embedding(vec=vec, norm=np.linalg.norm(vec))

        candidates = []
        for idx, vec in enumerate(self.fdc_vectors):
            score = self._cosine_similarity(input_token_vector, vec)
            candidates.append(
                FDCIngredientMatch(
                    fdc=self.fdc_ingredients[idx],
                    score=float(score),
                )
            )

        sorted_candidates = sorted(candidates, key=lambda x: x.score)
        return sorted_candidates


@lru_cache
def get_usif_ranker() -> uSIF:
    """Cached function for returning instantiated uSIF object.

    Returns
    -------
    uSIF
        Instantiation uSIF object.
    """
    logger.debug("Initializing uSIF ranker.")
    embeddings = load_embeddings_model()
    fdc_ingredients = load_fdc_ingredients()
    return uSIF(embeddings, fdc_ingredients)

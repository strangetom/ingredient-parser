#!/usr/bin/env python3

import logging
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .._embeddings import GloVeModel
from .._loaders import load_embeddings_model
from ._ff_dataclasses import FDCIngredient, FDCIngredientMatch
from ._ff_utils import load_fdc_ingredients

logger = logging.getLogger("ingredient-parser.foundation-foods.fuzzy")


@dataclass
class FDCIngredientEmbedding:
    fdc: FDCIngredient
    vectors: np.ndarray


class FuzzyEmbeddingMatcher:
    """Implementation of fuzzy document distance metric [1]_ used to determine the most
    similar FDC ingredient to a given ingredient name.

    References
    ----------
    .. [1] Morales-Garzón, A., Gómez-Romero, J., Martin-Bautista, M.J. (2020). A Word
           Embedding Model for Mapping Food Composition Databases Using Fuzzy Logic. In:
           Lesot, MJ., et al. Information Processing and Management of Uncertainty in
           Knowledge-Based Systems. IPMU 2020. Communications in Computer and
           Information Science, vol 1238. Springer, Cham.
           https://doi.org/10.1007/978-3-030-50143-3_50

    Attributes
    ----------
    embeddings : GloVeModel
        GloVe embeddings model.
    """

    def __init__(self, embeddings: GloVeModel, fdc_ingredients: list[FDCIngredient]):
        """Initialize.

        Parameters
        ----------
        embeddings : GloVeModel
            GloVe embeddings model.
        """
        self.embeddings = embeddings

        # Pre-cache FDC token embedding so they aren't regenerated every time
        # `score_matches` is called.
        self.fdc_vector_cache = {}
        for fdc in fdc_ingredients:
            self.fdc_vector_cache[fdc.fdc_id] = FDCIngredientEmbedding(
                fdc=fdc, vectors=np.array([self._get_vector(t) for t in fdc.tokens])
            )

    @lru_cache
    def _get_vector(self, token: str) -> np.ndarray:
        """Get embedding vector for token.

        This function exists solely so this operation can be LRU cached.

        Parameters
        ----------
        token : str
            Token to return embedding vector for.

        Returns
        -------
        np.ndarray
            Embedding vector for token.
        """
        return self.embeddings[token]

    def _fuzzy_document_distance(
        self,
        ingredient_tokens: list[str],
        fdc_tokens: list[str],
        ingredient_vectors: np.ndarray,
        fdc_vectors: np.ndarray,
    ) -> float:
        """Calculate fuzzy document distance metric between ingredient name and FDC
        ingredient description.

        Parameters
        ----------
        ingredient_tokens : list[str]
            Tokens for ingredient name.
        fdc_tokens : list[str]
            Tokens for FDC ingredient description.
        ingredient_vectors : np.ndarray
            Embedding vectors for ingredient tokens.
        fdc_vectors : np.ndarray
            Embedding vectors for FDC tokens.

        Returns
        -------
        float
            Fuzzy document distance.
            Smaller values mean closer match.
        """
        # Pre-calculate distances between all pairs of ingredient and FDC token vectors.
        # This is a matrix with shape (len(ingredient_tokens), len(fdc_tokens)).
        distances = np.linalg.norm(
            ingredient_vectors[:, np.newaxis, :] - fdc_vectors[np.newaxis, :, :], axis=2
        )

        # Apply sigmoid transformation, forcing a value of 1 where the distance = 0, to
        # get the similarity scores between all pairs of ingredient and FDC tokens.
        # This is a matrix with shape (len(ingredient_tokens), len(fdc_tokens)).
        with np.errstate(divide="ignore"):
            similarities = np.where(
                distances == 0, 1.0, 1 / (1 + np.exp(-1 / distances))
            )

        # Calculate fuzzy intersection from the tokens that are similar in both the
        # ingredient and FDC ingredient name, to the tokens that are similar to only
        # one of the ingredient or FDC name.
        union_membership = 0.0
        ingred_membership = 0.0
        fdc_membership = 0.0

        token_union = set(ingredient_tokens) | set(fdc_tokens)
        for token in token_union:
            token_ingred_score = 0.0
            token_fdc_score = 0.0
            if token in ingredient_tokens and token in fdc_tokens:
                # Exact match for token in both ingredient and FDC tokens.
                token_ingred_score = 1.0
                token_fdc_score = 1.0
            elif token in ingredient_tokens and token not in fdc_tokens:
                # Exact match for token in ingredient tokens.
                token_ingred_score = 1.0
                # Select the best match in the FDC tokens.
                ingred_idx = [i for i, t in enumerate(ingredient_tokens) if t == token]
                token_fdc_score = max(similarities[ingred_idx[0], :])
            elif token not in ingredient_tokens and token in fdc_tokens:
                # Exact match for token in FDC tokens.
                token_fdc_score = 1.0
                # Select the best match in the ingredient tokens.
                fdc_idx = [i for i, t in enumerate(fdc_tokens) if t == token]
                token_ingred_score = max(similarities[:, fdc_idx[0]])

            union_membership += token_ingred_score * token_fdc_score
            ingred_membership += token_ingred_score
            fdc_membership += token_fdc_score

        # Protect against divide by zero errors
        if (ingred_membership + fdc_membership - union_membership) > 0:
            res = union_membership / (
                ingred_membership + fdc_membership - union_membership
            )
        else:
            res = 0

        return 1 - res

    def score_matches(
        self, tokens: list[str], fdc_ids: set[int] | None
    ) -> list[FDCIngredientMatch]:
        """Score FDC Ingredients according to closest match to tokens.

        Parameters
        ----------
        tokens : list[str]
            Tokens for ingredient name, prepared for use with embeddings.

        Returns
        -------
        FDCIngredientMatch
            Scored FDC ingredients, sorted by best first.
        """
        token_vectors = np.array([self._get_vector(t) for t in tokens])

        if fdc_ids is None:
            fdc_ids = set(self.fdc_vector_cache.keys())

        scored = []
        for fdc_id in fdc_ids:
            fdc_embedding = self.fdc_vector_cache[fdc_id]
            score = self._fuzzy_document_distance(
                tokens,
                fdc_embedding.fdc.tokens,
                token_vectors,
                fdc_embedding.vectors,
            )
            scored.append(FDCIngredientMatch(fdc=fdc_embedding.fdc, score=score))

        return sorted(scored, key=lambda x: x.score)


@lru_cache
def get_fuzzy_matcher() -> FuzzyEmbeddingMatcher:
    """Cached function for returning instantiated FuzzyEmbeddingMatcher object.

    Returns
    -------
    FuzzyEmbeddingMatcher
        Instantiation FuzzyEmbeddingMatcher object.
    """
    logger.debug("Initializing Fuzzy matcher.")
    embeddings = load_embeddings_model()
    fdc_ingredients = load_fdc_ingredients()
    return FuzzyEmbeddingMatcher(embeddings, fdc_ingredients)

#!/usr/bin/env python3

import logging
from functools import lru_cache

import numpy as np

from .._loaders import load_bert_embeddings_model
from ._ff_dataclasses import FDCIngredient, FDCIngredientMatch
from ._ff_utils import load_fdc_ingredients

logger = logging.getLogger("ingredient-parser.foundation-foods.semantic")


class SemanticRanker:
    """Implementation of ATIRE BM25 ranking function [1]_.

    References
    ----------
    .. [1] Trotman, A., Jia, X.F., Crane, M.: Towards an efficient and effective search
           engine. In: SIGIR 2012 Workshop on Open Source Information Retrieval,
           pp. 40–47, Portland (2012)

    Attributes
    ----------
    corpus : list[list[str]]
        FDC ingredient corpus.
    """

    def __init__(self, fdc_ingredients: list[FDCIngredient]):
        """
        Parameters
        ----------
        fdc_ingredients : list[FDCIngredient]
            Lists of FDC ingredients.
        """
        self.embedding_model = load_bert_embeddings_model()
        self.corpus = fdc_ingredients
        self._embed_fdc_ingredients(fdc_ingredients)

    def _embed_fdc_ingredients(self, fdc_ingredients: list[FDCIngredient]):
        """Calculate embedding vectors for FDC ingredient descriptions and the vector
        norms.

        The vectors (and norms) are stored as a dense matrix with dimensions
        (len(corpus), embedding_dimension).

        Parameters
        ----------
        fdc_ingredients : list[FDCIngredient]
            List of FDC ingredients.
        """
        self.fdc_vectors = np.zeros((len(self.corpus), self.embedding_model.dimensions))
        for idx, fdc in enumerate(self.corpus):
            self.fdc_vectors[idx, :] = self.embedding_model.get_vector(
                fdc.description
            ).vectors

        self.fdc_vectors_norm = np.linalg.norm(self.fdc_vectors, axis=1)

    def _fdc_cosine_similarity(self, ingredient_vector: np.ndarray) -> np.ndarray:
        """Return cosine similarity score for input vectors.

        Parameters
        ----------


        Returns
        -------
        float
            Cosine similarity score.
        """
        ingredient_vector = ingredient_vector.reshape(-1)
        ingredient_vector_norm = np.linalg.norm(ingredient_vector)
        dot_product = np.dot(self.fdc_vectors, ingredient_vector)
        return 1 - dot_product / (self.fdc_vectors_norm * ingredient_vector_norm)

    def rank_matches(self, text: str) -> list[FDCIngredientMatch]:
        """Rank and score FDC Ingredients according to closest match to tokens.

        Parameters
        ----------
        text : str
            Ingredient name as string.

        Returns
        -------
        list[FDCIngredientMatch]
            Scored FDC ingredients, sorted by best first.
        """
        ingredient_vector = self.embedding_model.get_vector(text).vectors
        similarity_scores = self._fdc_cosine_similarity(ingredient_vector)

        return [
            FDCIngredientMatch(
                score=1 - float(similarity_scores[idx]), fdc=self.corpus[idx]
            )
            for idx in np.argsort(similarity_scores)
        ]


@lru_cache
def get_semantic_ranker() -> SemanticRanker:
    """Cached function for returning instantiated SemanticRanker object.

    Returns
    -------
    SemanticRanker
        Instantiation SemanticRanker object.
    """
    logger.debug("Initializing SemanticRanker ranker.")
    fdc_ingredients = load_fdc_ingredients()
    return SemanticRanker(fdc_ingredients)

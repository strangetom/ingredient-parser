#!/usr/bin/env python3

from functools import lru_cache

import numpy as np

from .._embeddings import GloVeModel
from .._loaders import load_embeddings_model
from ._ff_constants import NON_RAW_FOOD_VERB_STEMS
from ._ff_dataclasses import FDCIngredient, FDCIngredientMatch


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

    def __init__(self, embeddings: GloVeModel):
        """Initialize.

        Parameters
        ----------
        embeddings : GloVeModel
            GloVe embeddings model.
        """
        self.embeddings = embeddings

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

    @lru_cache(maxsize=512)
    def _token_similarity(self, token1: str, token2: str) -> float:
        """Calculate similarity between two word embeddings.

        This uses the reciprocal euclidean distance transformed by a sigmoid function to
        return a value between 0 and 1.
        1 indicates an exact match (i.e. token1 and token2 are the same).
        0 indicates no match whatsoever.

        Parameters
        ----------
        token1 : str
            First token.
        token2 : str
            Second token.

        Returns
        -------
        float
            Value between 0 and 1.
        """
        euclidean_dist = np.linalg.norm(
            self._get_vector(token1) - self._get_vector(token2)
        )

        if euclidean_dist == 0:
            return 1
        elif euclidean_dist == np.inf:
            return 0
        else:
            sigmoid = 1 / (1 + np.exp(-1 / euclidean_dist))
            return float(sigmoid)

    @lru_cache(maxsize=512)
    def _max_token_similarity(
        self, token: str, fdc_ingredient_tokens: tuple[str, ...]
    ) -> float:
        """Calculate the maximum similarity of token to FDC ingredient description
        tokens.

        Similarity score is calculated from the euclidean distance between token and
        all tokens that make up the FDC ingredient description.
        The reciprocal of this distance if transformed using a sigmoid function to
        return the score between 0 and 1.
        A score of 1 indicates that token is found exactly in fdc_ingredient.

        Parameters
        ----------
        token : str
            Token to calculate similarity of.
        fdc_ingredient_tokens : tuple[str, ...]
            FDC ingredient description tokens to calculate maximum token similarity to.

        Returns
        -------
        float
            Membership score between 0 and 1, where 1 indicates exact match.
        """
        return max(self._token_similarity(token, t) for t in fdc_ingredient_tokens)

    def _fuzzy_document_distance(
        self,
        ingredient_name_tokens: list[str],
        fdc_ingredient_tokens: list[str],
    ) -> float:
        """Calculate fuzzy document distance metric between ingredient name and FDC
        ingredient description.

        Parameters
        ----------
        ingredient_name_tokens : list[str]
            Tokens for ingredient name.
        fdc_ingredient_tokens : list[str]
            Tokens for FDC ingredient description.

        Returns
        -------
        float
            Fuzzy document distance.
            Smaller values mean closer match.
        """
        # Calculate fuzzy intersection from the tokens that are similar in both the
        # ingredient and FDC ingredient name, to the tokens that are similar to only
        # one of the ingredient or FDC name.
        union_membership = 0.0
        ingred_membership = 0.0
        fdc_membership = 0.0

        token_union = set(ingredient_name_tokens) | set(fdc_ingredient_tokens)
        for token in token_union:
            token_ingred_score = self._max_token_similarity(
                token, tuple(ingredient_name_tokens)
            )
            token_fdc_score = self._max_token_similarity(
                token, tuple(fdc_ingredient_tokens)
            )

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

    def find_best_match(
        self, ingredient_name_tokens: list[str], fdc_ingredients: list[FDCIngredient]
    ) -> FDCIngredientMatch:
        """Find the FDC ingredient that best matches the ingredient name tokens from the
        list of FDC ingredients.

        If the ingredient name tokens do not contain a verb indicating that the
        ingredient name is not raw (e.g. cooked), then the token "raw" is added as an
        additional token to bias the results towards a "raw" FDC ingredient.

        Parameters
        ----------
        ingredient_name_tokens : list[str]
            Tokens for ingredient name, prepared for use with embeddings.
        fdc_ingredients : list[FDCIngredient]
            List of candidate FDC ingredients.

        Returns
        -------
        FDCIngredientMatch
            Best matching FDC ingredient.
        """
        # Bias the results towards selecting the raw version of a FDC ingredient, but
        # only if the ingredient name tokens don't already include a verb that indicates
        # the food is not raw (e.g. cooked)
        if len(set(ingredient_name_tokens) & NON_RAW_FOOD_VERB_STEMS) == 0:
            ingredient_name_tokens.append("raw")

        scored: list[FDCIngredientMatch] = []
        for fdc in fdc_ingredients:
            score = self._fuzzy_document_distance(ingredient_name_tokens, fdc.tokens)
            scored.append(FDCIngredientMatch(fdc=fdc, score=score))

        sorted_matches = sorted(scored, key=lambda x: x.score)
        return sorted_matches[0]


@lru_cache
def get_fuzzy_matcher() -> FuzzyEmbeddingMatcher:
    """Cached function for returning instantiated FuzzyEmbeddingMatcher object.

    Returns
    -------
    FuzzyEmbeddingMatcher
        Instantiation FuzzyEmbeddingMatcher object.
    """
    embeddings = load_embeddings_model()
    return FuzzyEmbeddingMatcher(embeddings)

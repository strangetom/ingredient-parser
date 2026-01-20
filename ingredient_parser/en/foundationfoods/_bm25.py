#!/usr/bin/env python3

import logging
import math
from collections import defaultdict
from functools import lru_cache
from statistics import mean

from ._ff_dataclasses import FDCIngredient, FDCIngredientMatch, IngredientToken
from ._ff_utils import load_fdc_ingredients

logger = logging.getLogger("ingredient-parser.foundation-foods.bm25")


class BM25:
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
    t2d : dict[str, dict[int, int]]
        Dictionary with terms frequencies.
        The keys are tokens, the values are a dict of ingredient index in corpus and the
        frequency of the term in that ingredient.
    idf : dict[str, float]
        Pre computed inverse document frequency score for every term i.e. the inverse of
        the number of ingredients containing the term.
    doc_len : list[int]
        List of ingredient lengths.
    avgdl : float
        Average length of ingredient in `corpus`.
    """

    def __init__(
        self,
        fdc_ingredients: list[FDCIngredient],
        k1: float,
        b: float,
    ):
        """
        Parameters
        ----------
        fdc_ingredients : list[FDCIngredient]
            Lists of FDC ingredients.
        k1 : float
            Constant used for influencing the term frequency saturation. After
            saturation is reached, additional presence for the term adds a significantly
            less additional score. According to [1]_, experiments suggest that
            1.2 < k1 < 2 yields reasonably good results, although the optimal value
            depends on factors such as the type of documents or queries.
        b : float
            Constant used for influencing the effects of different document lengths
            relative to average document length. When b is bigger, lengthier documents
            (compared to average) have more impact on its effect. According to [1]_,
            experiments suggest that 0.5 < b < 0.8 yields reasonably good results,
            although the optimal value depends on factors such as the type of documents
            or queries.
        """
        self.k1 = k1
        self.b = b

        self.avgdl = 0
        self.t2d = {}
        self.idf = {}
        self.doc_len = []
        self.corpus = []
        self._initialize(fdc_ingredients)

    @property
    def corpus_size(self):
        return len(self.doc_len)

    def _initialize(self, fdc_ingredients: list[FDCIngredient]):
        """Calculates frequencies of terms in documents and in corpus.
        Also computes inverse document frequencies.
        """
        self.corpus = fdc_ingredients

        for i, ingredient in enumerate(fdc_ingredients):
            self.doc_len.append(len(ingredient.tokens))

            for token in ingredient.tokens:
                self.t2d.setdefault(token, defaultdict(int))
                self.t2d[token][i] += 1

        self.avgdl = mean(self.doc_len)

        for token, ingredients in self.t2d.items():
            self.idf[token] = math.log(self.corpus_size / len(ingredients))

    def rank_matches(self, tokens: list[IngredientToken]) -> list[FDCIngredientMatch]:
        """Rank and score FDC Ingredients according to closest match to tokens.

        Parameters
        ----------
        tokens : list[IngredientToken]
            List of tokens.

        Returns
        -------
        list[FDCIngredientMatch]
            Scored FDC ingredients, sorted by best first.
        """
        scores = defaultdict(float)
        for ing_token in tokens:
            if ing_token.token in self.t2d:
                for index, freq in self.t2d[ing_token.token].items():
                    denom_constant = self.k1 * (
                        1 - self.b + self.b * self.doc_len[index] / self.avgdl
                    )
                    scores[index] += (
                        self.idf[ing_token.token]
                        * freq
                        * (self.k1 + 1)
                        / (denom_constant + freq)
                    )

        matches = []
        for index, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            matches.append(
                FDCIngredientMatch(
                    fdc=self.corpus[index],
                    score=score,
                )
            )
        return matches


@lru_cache
def get_bm25_ranker() -> BM25:
    """Cached function for returning instantiated BM25 object.

    Returns
    -------
    uSIF
        Instantiation BM25 object.
    """
    logger.debug("Initializing BM25 ranker.")
    fdc_ingredients = load_fdc_ingredients()
    return BM25(fdc_ingredients, k1=1.5, b=0.75)

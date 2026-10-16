#!/usr/bin/env python3

import logging
import math
from collections import defaultdict
from functools import lru_cache
from statistics import mean

import numpy as np

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
    corpus : list[FDCIngredient]
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
        # t2d maps token to the documents that contain it and, for each containing
        # document, the frequency of the token within that document.
        self.t2d: dict[str, dict[int, int]] = {}
        # idf maps each token to it's inverse document frequency.
        self.idf: dict[str, float] = {}
        self.doc_len: list[int] = []
        self.corpus: list[FDCIngredient] = []
        # postings maps token to the documents that contain it and, for each containing
        # document, the contribution of that token to the score for that document.
        # The document indices and score contributions are stored as np.ndarrays.
        self.postings: dict[str, tuple[np.ndarray, np.ndarray]] = {}
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

        # Pre-compute the contribution of each token to every FDC ingredient that
        # contains it.
        # When it comes to ranking for FDC ingredients for a given set of query tokens,
        # we just need to look at the posting for each token in the query and sum the
        # contributions for relevant FDC ingredients.
        doc_len = np.array(self.doc_len)
        denom_constant = self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
        for token, ingredients in self.t2d.items():
            indices = np.fromiter(ingredients.keys(), dtype=np.intp)
            freqs = np.fromiter(ingredients.values(), dtype=np.float64)
            contribution = self.idf[token] + freqs * (self.k1 + 1) / (
                denom_constant[indices] + freqs
            )
            self.postings[token] = (indices, contribution)

    def rank_matches(
        self, tokens: list[IngredientToken], top_k: int
    ) -> list[FDCIngredientMatch]:
        """Rank and score FDC Ingredients according to closest match to tokens.

        Parameters
        ----------
        tokens : list[IngredientToken]
            List of tokens.
        top_k : int
            Number of highest ranking matches to return.

        Returns
        -------
        list[FDCIngredientMatch]
            Scored FDC ingredients, sorted by best first.
        """
        scores = np.zeros(self.corpus_size)
        shares_noun = np.zeros(self.corpus_size, dtype=np.bool)

        for token in tokens:
            # Get the posting for each token.
            # The posting contains the indices for the FDC ingredients in self.corpus
            # that contain the token, and the contribution to the score for that FDC
            # ingredient as a result of this token.
            posting = self.postings.get(token.token)
            if not posting:
                continue

            indices, contributions = posting
            scores[indices] += contributions
            if token.pos_tag.startswith("N"):
                shares_noun[indices] = True

        # Candidates are the FDC ingredients that share a noun with input tokens.
        candidates = np.flatnonzero(shares_noun)
        if candidates.size == 0:
            logger.debug(
                "BM25 ranker found no FDC entries that had a noun "
                "common with the ingredient name."
            )

        candidate_scores = scores[candidates]
        order = np.argsort(-1 * candidate_scores)
        return [
            FDCIngredientMatch(
                fdc=self.corpus[idx],
                score=float(scores[idx]),
            )
            for idx in candidates[order][:top_k]
        ]


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

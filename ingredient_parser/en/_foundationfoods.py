#!/usr/bin/env python3

import csv
import gzip
import string
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import as_file, files

import numpy as np

from ..dataclasses import FoundationFood
from ._loaders import load_embeddings_model
from ._utils import prepare_embeddings_tokens, tokenize

# Dict of ingredient name tokens that bypass the usual foundation food matching process.
# We do this because the embedding distance approach sometime gives poor results when
# the name we're trying to match only has one token.
FOUNDATION_FOOD_OVERRIDES: dict[tuple[str, ...], FoundationFood] = {
    ("egg",): FoundationFood(
        "Eggs, Grade A, Large, egg whole",
        1,
        748967,
        "Dairy and Egg Products",
        "foundation_food",
    ),
    ("eggs",): FoundationFood(
        "Eggs, Grade A, Large, egg whole",
        1,
        748967,
        "Dairy and Egg Products",
        "foundation_food",
    ),
    ("butter",): FoundationFood(
        "Butter, stick, unsalted",
        1,
        789828,
        "Dairy and Egg Products",
        "foundation_food",
    ),
    ("cucumber",): FoundationFood(
        "Cucumber, with peel, raw",
        1,
        2346406,
        "Vegetables and Vegetable Products",
        "foundation_food",
    ),
}

# List of preferred FDC data types.
# Increasing value indicates decreasing preference.
PREFERRED_DATATYPES = {
    "foundation_food": 0,  #  Most preferred
    "sr_legacy_food": 1,
    "survey_fndds_food": 2,
}


@dataclass
class FDCIngredient:
    """Dataclass for details of an ingredient from the FoodDataCentral database."""

    fdc_id: int
    data_type: str
    description: str
    category: str
    tokens: list[str]


@dataclass
class FDCIngredientMatch:
    """Dataclass for details of a matching FDC ingredient."""

    fdc: FDCIngredient
    score: float
    data_type: str


class uSIF:
    """Modified implementation of Unsupervised Smooth Inverse Frequency weighting scheme
    for calculation of sentence embedding vectors.

    Based on Kawin Ethayarajh. 2018. Unsupervised Random Walk Sentence Embeddings: A
    Strong but Simple Baseline. In Proceedings of the Third Workshop on Representation
    Learning for NLP, pages 91–100, Melbourne, Australia. Association for Computational
    Linguistics.

    This implementation is modified to not implement the piecewise common component
    removal.

    Attributes
    ----------
    a : float
        'a' parameter.
    embeddings : floret.floret._floret
        Floret embeddings model.
    embeddings_dimension : int
        Dimension of embeddings model.
    fdc_ingredients : dict[str, list[FDCIngredient]]
        Lists of FDC Ingredients, grouped by data type.
    fdc_vectors : dict[str, list[FDCIngredient]]
        Lists of embedding vectors for FDC Ingredients, grouped by data type.
    min_prob : float
        Minimum token probability.
    token_prob : dict[str, float]
        Token probability.
    """

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.embeddings_dimension: int = embeddings.get_dimension()

        self.fdc_ingredients: dict[str, list[FDCIngredient]] = (
            self._load_fdc_ingredients()
        )
        self.token_prob: dict[str, float] = self._estimate_token_probability(
            self.fdc_ingredients
        )
        self.min_prob: float = min(self.token_prob.values())
        self.a: float = self._calculate_a_factor()

        self.fdc_vectors = self._embed_fdc_ingredients()

    def _load_fdc_ingredients(self) -> dict[str, list[FDCIngredient]]:
        """Load FDC Ingredients from CSV.

        Returns
        -------
        dict[str, list[FDCIngredient]]
            List of FDC Ingredients, grouped by data type.
        """
        foundation_foods = defaultdict(list)
        with as_file(files(__package__) / "fdc_ingredients.csv.gz") as p:
            with gzip.open(p, "rt") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data_type = row["data_type"]
                    tokens = tuple(tokenize(row["description"]))
                    prepared_tokens = prepare_embeddings_tokens(tokens)
                    foundation_foods[data_type].append(
                        FDCIngredient(
                            fdc_id=int(row["fdc_id"]),
                            data_type=data_type,
                            description=row["description"],
                            category=row["category"],
                            tokens=prepared_tokens,
                        )
                    )

        return foundation_foods

    def _estimate_token_probability(
        self, fdc_ingredients: dict[str, list[FDCIngredient]]
    ) -> dict[str, float]:
        """Estimate word probability from the frequency of occurrence of token in FDC
        ingredient descriptions.

        Parameters
        ----------
        fdc_ingredients : dict[str, list[FDCIngredient]]
            List of FDC Ingredient objects.

        Returns
        -------
        dict[str, float]
            Dict of token: probability.
        """
        token_counts = defaultdict(int)
        for data_type in PREFERRED_DATATYPES:
            for ingredient in fdc_ingredients[data_type]:
                for token in ingredient.tokens:
                    token_counts[token] += 1

        total = sum(token_counts.values())
        return {token: count / total for token, count in token_counts.items()}

    def _average_sentence_length(self) -> int:
        """Calculate average sentence length for FDC ingredient descriptions.

        Returns
        -------
        int
            Average sentence length
        """
        token_count = 0
        sentence_count = 0
        for data_type in PREFERRED_DATATYPES:
            for fdc in self.fdc_ingredients[data_type]:
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

    def _embed_fdc_ingredients(self) -> dict[str, list[np.ndarray]]:
        """Calculate embedding vectors for all FDC Ingredients.

        Returnstoken_prob
        -------
        dict[str, list[np.ndarray]]
            Dict of embedding vectors for FDC Ingredients, grouped by data type.
        """
        vectors = defaultdict(list)
        for data_type in PREFERRED_DATATYPES:
            for fdc in self.fdc_ingredients[data_type]:
                vectors[data_type].append(self._embed(fdc.tokens))

        return vectors

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

    def find_best_match(self, tokens: list[str]) -> list[FDCIngredientMatch]:
        """Find best match between input token and FDC Ingredients.

        Parameters
        ----------
        tokens : list[str]
            List of tokens.

        Returns
        -------
        list[FDCIngredientMatch]
            List of best matching FDC Ingredient for each data type.
        """
        prepared_tokens = prepare_embeddings_tokens(tuple(tokens))
        input_token_vector = self._embed(prepared_tokens)

        best_scores = []
        for data_type in PREFERRED_DATATYPES:
            scores = [
                (self._cosine_similarity(input_token_vector, vec), idx)
                for idx, vec in enumerate(self.fdc_vectors[data_type])
            ]
            sorted_scores = sorted(scores, key=lambda x: x[0])
            best_score, best_match_idx = sorted_scores[0]
            best_scores.append(
                FDCIngredientMatch(
                    fdc=self.fdc_ingredients[data_type][best_match_idx],
                    score=best_score,
                    data_type=data_type,
                )
            )

        return best_scores


@lru_cache
def get_usif_matcher() -> uSIF:
    """Cached function for returning instantiated uSIF object.
    
    Returns
    -------
    uSIF
        Instantiation uSIF object.
    """
    embeddings = load_embeddings_model()
    return uSIF(embeddings)


def match_foundation_foods(tokens: list[str]) -> FoundationFood | None:
    """Match ingredient name to foundation foods from FDC Ingredient.

    Parameters
    ----------
    tokens : list[str]
        Ingredient name tokens.

    Returns
    -------
    FoundationFood | None
        Matching foundation food, or None if no match can be found.
    """
    override_name = tuple(t.lower() for t in tokens if t not in string.punctuation)
    if override_name in FOUNDATION_FOOD_OVERRIDES:
        return FOUNDATION_FOOD_OVERRIDES[override_name]

    u = get_usif_matcher()
    matches = u.find_best_match(tokens)
    for match in matches:
        if match.score <= 0.25:
            return FoundationFood(
                text=match.fdc.description,
                confidence=round(1 - match.score, 6),
                fdc_id=match.fdc.fdc_id,
                category=match.fdc.category,
                data_type=match.fdc.data_type,
            )

    # Fallback to best scoring match if below threshold
    sorted_matches = sorted(matches, key=lambda x: x.score)
    best_fallback_match = sorted_matches[0]
    if best_fallback_match.score <= 0.35:
        return FoundationFood(
            text=best_fallback_match.fdc.description,
            confidence=round(1 - best_fallback_match.score, 6),
            fdc_id=best_fallback_match.fdc.fdc_id,
            category=best_fallback_match.fdc.category,
            data_type=best_fallback_match.fdc.data_type,
        )

    return None

#!/usr/bin/env python3

import csv
import gzip
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
    ("salt",): FoundationFood(
        "Salt, table, iodized", 1, 746775, "Spices and Herbs", "foundation_food"
    ),
    ("egg",): FoundationFood(
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
    ("garlic",): FoundationFood(
        "Garlic, raw",
        1,
        1104647,
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


@lru_cache
def load_fdc_ingredients() -> dict[str, list[FDCIngredient]]:
    """Load FDC ingredients from CSV.

    Returns
    -------
    dict[str, list[FDCIngredient]]
        List of FDC ingredients, grouped by data type.
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
        Lists of FDC ingredients, grouped by data type.
    fdc_vectors : dict[str, list[FDCIngredient]]
        Lists of embedding vectors for FDC ingredients, grouped by data type.
    min_prob : float
        Minimum token probability.
    token_prob : dict[str, float]
        Token probability.
    """

    def __init__(self, embeddings, fdc_ingredients: dict[str, list[FDCIngredient]]):
        self.embeddings = embeddings
        self.embeddings_dimension: int = embeddings.get_dimension()

        self.fdc_ingredients: dict[str, list[FDCIngredient]] = fdc_ingredients
        self.token_prob: dict[str, float] = self._estimate_token_probability(
            self.fdc_ingredients
        )
        self.min_prob: float = min(self.token_prob.values())
        self.a: float = self._calculate_a_factor()

        self.fdc_vectors = self._embed_fdc_ingredients()

    def _estimate_token_probability(
        self, fdc_ingredients: dict[str, list[FDCIngredient]]
    ) -> dict[str, float]:
        """Estimate word probability from the frequency of occurrence of token in FDC
        ingredient descriptions.

        Parameters
        ----------
        fdc_ingredients : dict[str, list[FDCIngredient]]
            List of FDC ingredient objects.

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
        """Calculate embedding vectors for all FDC ingredients.

        Returnstoken_prob
        -------
        dict[str, list[np.ndarray]]
            Dict of embedding vectors for FDC ingredients, grouped by data type.
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
        """Find best match between input token and FDC ingredients.

        Parameters
        ----------
        tokens : list[str]
            List of tokens, prepared for use with embeddings.

        Returns
        -------
        list[FDCIngredientMatch]
            List of best matching FDC ingredient for each data type.
        """
        input_token_vector = self._embed(tokens)

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
                )
            )

        return best_scores

    def find_candidate_matches(
        self, tokens: list[str], cutoff: float = 0.25
    ) -> list[FDCIngredientMatch]:
        """Find best n candidate matches between input token and FDC ingredients.

        Parameters
        ----------
        tokens : list[str]
            List of tokens.
        cutoff : float
            Maximum allowable score of returned matches.

        Returns
        -------
        list[FDCIngredientMatch]
            List of candidate matching FDC ingredient.
        """
        prepared_tokens = prepare_embeddings_tokens(tuple(tokens))
        input_token_vector = self._embed(prepared_tokens)

        candidates = []
        for data_type in PREFERRED_DATATYPES:
            for idx, vec in enumerate(self.fdc_vectors[data_type]):
                score = self._cosine_similarity(input_token_vector, vec)
                if score <= cutoff:
                    candidates.append(
                        FDCIngredientMatch(
                            fdc=self.fdc_ingredients[data_type][idx],
                            score=score,
                        )
                    )

        return candidates


class FuzzyEmbeddingMatcher:
    """Implementation of fuzzy document distance metric used to determine the most
    similar FDC ingredient to a given ingredient name.

    Based on Morales-Garzón, A., Gómez-Romero, J., Martin-Bautista, M.J. (2020). A Word
    Embedding Model for Mapping Food Composition Databases Using Fuzzy Logic. In: Lesot,
    MJ., et al. Information Processing and Management of Uncertainty in Knowledge-Based
    Systems. IPMU 2020. Communications in Computer and Information Science, vol 1238.
    Springer, Cham. https://doi.org/10.1007/978-3-030-50143-3_50

    Attributes
    ----------
    embeddings : floret.floret._floret
        Floret embeddings model.
    """

    def __init__(self, embeddings):
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
            Embedding vector
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
        list of FDC ingredients

        Parameters
        ----------
        ingredient_name_tokens : list[str]
            Tokens for ingredient name, prepared for use with embeddings.
        fdc_ingredients : list[FDCIngredient]
            List of candidate FDC ingredients.
        """
        scored: list[FDCIngredientMatch] = []
        for fdc in fdc_ingredients:
            score = self._fuzzy_document_distance(ingredient_name_tokens, fdc.tokens)
            scored.append(FDCIngredientMatch(fdc=fdc, score=score))

        sorted_matches = sorted(scored, key=lambda x: x.score)
        return sorted_matches[0]


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


def match_foundation_foods(tokens: list[str]) -> FoundationFood | None:
    """Match ingredient name to foundation foods from FDC ingredient.

    This is done in two stages.
    The first stage uses an Unsupervised Smooth Inverse Frequency calculation to down
    select the possible candidate matching FDC ingredients.

    The second stage selects the best of these candidates using a fuzzy embedding
    document metric.

    The need for two stages is that the ingredient embeddings do not seem to be as
    accurate as off the shelf pre-trained general embeddings are for general tasks.
    Improving the quality of the embeddings might remove the need for the second stage.

    Parameters
    ----------
    tokens : list[str]
        Ingredient name tokens.

    Returns
    -------
    FoundationFood | None
        Matching foundation food, or None if no match can be found.
    """
    prepared_tokens = prepare_embeddings_tokens(tuple(tokens))

    if tuple(prepared_tokens) in FOUNDATION_FOOD_OVERRIDES:
        return FOUNDATION_FOOD_OVERRIDES[tuple(prepared_tokens)]

    u = get_usif_matcher()
    candidate_matches = u.find_candidate_matches(prepared_tokens)

    fuzzy = get_fuzzy_matcher()
    best_match = fuzzy.find_best_match(
        prepared_tokens, [m.fdc for m in candidate_matches]
    )

    if best_match.score <= 0.35:
        return FoundationFood(
            text=best_match.fdc.description,
            confidence=round(1 - best_match.score, 6),
            fdc_id=best_match.fdc.fdc_id,
            category=best_match.fdc.category,
            data_type=best_match.fdc.data_type,
        )

    return None

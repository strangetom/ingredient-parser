#!/usr/bin/env python3

import json

import numpy as np
from nltk.data import find as nltk_find


class AveragedPerceptronNumpy:
    """Averaged Perceptron for part of speech tagging implemented using NumPy.

    This is design to be used with NLTK's part of speech tagger weights, but this
    implementation is tailored to the needs of this library. Specifically:
    * NumPy is used for the mathematics, to improve execution performance.
    * Only inference is implemented, no training related code.
    * Tag confidence scores are not calculated.
    * Feature specific weights are always assumed to be 1 and therefore not implemented.


    """

    def __init__(self) -> None:
        """Initialise."""
        # Initialise to empty objects.
        # These will need to be set to real values prior to inference.
        self.tags = []
        self.n_tags = 0
        self.weights = np.array([])
        self.feature_vocab: dict[str, int] = {}

    def __repr__(self):
        return "AveragedPerceptronNumpy()"

    def predict(self, features: list[str]) -> str:
        """Predict the tag for a token described by features list.

        Parameters
        ----------
        features : list[str]
            List of features for token, built from the token properties, previous labels
            and properties of context tokens.

        Returns
        -------
        str
            Tag for token, given the provided features.
        """
        # Convert from feature strings to index in feature vocabulary.
        feature_indices = np.array(
            [
                self.feature_vocab[feat]
                for feat in features
                if feat in self.feature_vocab
            ]
        )

        # Sum weights for active features across all tags at once.
        # Shape: (n_tags,) i.e. the summed score for each tag.
        if len(feature_indices) > 0:
            scores = self.weights[feature_indices].sum(axis=0)
        else:
            scores = np.zeros(self.n_tags)

        # Find the best label
        best_idx = np.argmax(scores)
        return self.tags[best_idx]


class PerceptronTagger:
    START = ("-START-", "-START2-")
    END = ("-END-", "-END2-")

    def __init__(self):
        """Initialise IngredientTaggerNumpy"""
        self.tags = []
        self.tagdict: dict[str, str] = {}
        self.load()

    def __repr__(self):
        return "PerceptronTagger()"

    def tag(self, tokens: list[str], use_tagdict: bool = True) -> list[tuple[str, str]]:
        """Tag a list of tokens using Averaged Perceptron model.

        Parameters
        ----------
        tokens : list[str]
            List of tokens to tag.

        Returns
        -------
        list[tuple[str, str]]
            List of (token, tag) tuples.
        """
        if self.model.weights.size == 0:
            raise ValueError("AveragedPerceptronNumpy model does not have any weights.")

        tags = []
        prev, prev2 = self.START

        context = [*self.START, *[self._normalize(w) for w in tokens], *self.END]
        for idx, token in enumerate(tokens):
            tag = self.tagdict.get(token) if use_tagdict else None
            if not tag:
                features = self._get_features(idx, token, context, prev, prev2)
                tag = self.model.predict(features)

            tags.append((token, tag))

            prev2 = prev
            prev = tag

        return tags

    def _normalize(self, token: str):
        """Normalization used in pre-processing.

        - All words are lower cased
        - Groups of digits of length 4 are represented as !YEAR;
        - Other digits are represented as !DIGITS

        Parameters
        ----------
        token : str
            Token to normalize.

        Returns
        -------
        str
            Normalized token.
        """
        if "-" in token and token[0] != "-":
            return "!HYPHEN"

        if token.isdigit() and len(token) == 4:
            return "!YEAR"

        if token and token[0].isdigit():
            return "!DIGITS"

        return token.lower()

    def _get_features(
        self, i: int, token: str, context: list[str], prev: str, prev2: str
    ) -> list[str]:
        """Map tokens into a feature representation.

        This is purposefully different to NLTK's implementation. Each feature name is
        unique, so there's no need to use a defaultdict and increment the value by one
        for each feature because all the values are always 1.
        Instead, we just return the feature names and skip the additional
        multiplication in the AveragedPerceptronNumpy.predict() function.

        Parameters
        ----------
        i : int
            Index of current token.
        token : str
            Current token.
        context : list[str]
            Tokenized sentence.
        prev : str
            Label assigned to previous token.
        prev2 : str
            Label assigned to token before previous token.

        Returns
        -------
        list[str]
            List of feature names for token at given index.
        """
        i += len(self.START)

        return [
            "bias",
            "i suffix " + token[-3:],
            "i pref1 " + token[0] if token else "",
            "i-1 tag " + prev,
            "i-2 tag " + prev2,
            "i tag+i-2 tag " + prev + " " + prev2,
            "i word " + context[i],
            "i-1 tag+i word " + prev + " " + context[i],
            "i-1 word " + context[i - 1],
            "i-1 suffix " + context[i - 1][-3:],
            "i-2 word " + context[i - 2],
            "i+1 word " + context[i + 1],
            "i+1 suffix " + context[i + 1][-3:],
            "i+2 word " + context[i + 2],
        ]

    def load(self) -> None:
        """Load saved model at given path.

        Parameters
        ----------
        path : str
            Path to model to load.
        """
        prefix = "taggers/averaged_perceptron_tagger_eng/averaged_perceptron_tagger_eng"
        tag_path = nltk_find(prefix + ".classes.json")
        with open(tag_path) as f:
            # Reverse=True is need to maintain consistency with the way the NLTK
            # Perceptron Tagger resolves tied scores.
            tags = sorted(json.load(f), reverse=True)
            self.tags = tags
            tag_to_idx = {tag: i for i, tag in enumerate(tags)}

        tagdict_path = nltk_find(prefix + ".tagdict.json")
        with open(tagdict_path) as f:
            self.tagdict = json.load(f)

        weights_path = nltk_find(prefix + ".weights.json")
        with open(weights_path) as f:
            weights_dict = json.load(f)

        weights_matrix = np.zeros((len(weights_dict), len(tags)), dtype=np.float64)
        feature_vocab = {}
        for feat_idx, (feature, tag_weights) in enumerate(weights_dict.items()):
            feature_vocab[feature] = feat_idx
            for tag, weight in tag_weights.items():
                tag_idx = tag_to_idx[tag]
                weights_matrix[feat_idx, tag_idx] = weight

        self.model = AveragedPerceptronNumpy()
        self.model.tags = tags
        self.model.n_tags = len(tags)
        self.model.weights = weights_matrix
        self.model.feature_vocab = feature_vocab

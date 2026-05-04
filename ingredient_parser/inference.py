#!/usr/bin/env python3

import gzip
import json
import logging
import mimetypes

import numpy as np

from .en import FeatureDict, PreProcessor

logger = logging.getLogger(__name__)


class NumpyCRFInference:
    """Class to performance inference using trained CRF model for ingredient sentence
    labelling.


    Attributes
    ----------
    model : NumpyViterbiInference
        Implementation of Viterbi for inference.
    """

    def __init__(self, model_file: str):
        """Initialise

        Parameters
        ----------
        model_file : str
            Path to model file.
        """
        self.load(model_file)

    def __repr__(self):
        return "CRFInference()"

    def tag(self, sentence: str) -> list[tuple[str, str]]:
        """Tag a sentence with labels using model.

        Parameters
        ----------
        sentence : str
            Sentence to tag tokens of.

        Returns
        -------
        list[tuple[str, str]]
            List of (token, label) tuples.
        """
        if (
            self.model.emission_weights.size == 0
            or self.model.transition_weights.size == 0
        ):
            raise ValueError("NumpyViterbiInference model does not have any weights.")

        p = PreProcessor(sentence, custom_units={})
        features = [self._convert_features(f) for f in p.sentence_features()]
        predicted_labels = self.model.predict_sequence(features)

        labels = [
            (token.text, label)
            for token, label in zip(p.tokenized_sentence, predicted_labels)
        ]
        return labels

    def tag_from_features(self, sentence_features: list[FeatureDict]) -> list[str]:
        """Tag a sentence with labels using model.

        This function accepts a list of features for each token, rather than
        calculating the features from the tokens.

        Parameters
        ----------
        sentence_features : list[FeatureDict]
            List of feature dicts for each token.

        Returns
        -------
        list[tuple[str, float]]
            List of labels.
        """
        if (
            self.model.emission_weights.size == 0
            or self.model.transition_weights.size == 0
        ):
            raise ValueError("NumpyViterbiInference model does not have any weights.")

        features = [self._convert_features(f) for f in sentence_features]
        return self.model.predict_sequence(features)

    def _convert_features(self, features: FeatureDict) -> set[str]:
        """Convert features dict to set of strings.

        The model weights use the features as keys, so they need to be a string rather
        than a key: value pair.
        For string features, the string is prepared by joining the key and value by ":".
        For int and float features, the string is prepared by joining the key and value
        by "L".
        For boolean features, the string is prepared just using the key if the boolean
        value is True.

        Parameters
        ----------
        features : FeatureDict
            Dictionary of token features token, obtained from PreProcessor.

        Returns
        -------
        set
            Set of features as strings
        """
        converted = set()
        for key, value in features.items():
            if isinstance(value, bool):
                if value:
                    converted.add(key)
            elif isinstance(value, str):
                converted.add(key + ":" + value)
            elif isinstance(value, (int, float)):
                converted.add(key + ":" + str(value))

        return converted

    def load(self, path: str) -> None:
        """Load saved model at given path.

        Parameters
        ----------
        path : str
            Path to model to load.
        """
        mimetype, encoding = mimetypes.guess_type(path)
        if not (mimetype == "application/json" and encoding == "gzip"):
            raise ValueError("Model must be a .json.gz file.")

        with open(path, "rb") as f:
            data = json.loads(gzip.decompress(f.read()))

        self.model = NumpyViterbiInference(
            features=data["attributes"],
            labels=data["labels"],
            feature_weights=data["state_features"],
            transition_weights=data["transitions"],
        )


class NumpyViterbiInference:
    def __init__(
        self,
        features: dict[str, int],
        labels: dict[str, int],
        feature_weights: dict[str, float],
        transition_weights: dict[str, float],
    ) -> None:
        """
        Parameters
        ----------
        features : dict[str, int]
            Dict mapping feature string to index.
        labels : dict[str, int]
            Dict mapping label string to index.
        feature_weights : dict[str, float]
            Dict of weights for each feature-label combination.
        transition_weights : dict[str, float]
            Dict of weights for each label-label transition.
        """
        self.label_to_idx = labels
        self.idx_to_label = {idx: label for label, idx in self.label_to_idx.items()}
        self.n_labels = len(labels)
        self.features_to_idx = features
        self.n_features = len(features)

        # Create a NumPy matrix with size (n_features, n_labels) and populate with the
        # weights.
        self.emission_weights = np.zeros(
            (self.n_features, self.n_labels), dtype=np.float32
        )
        for feat, weight in feature_weights.items():
            feature, label = feat.split("|")
            feature_idx = self.features_to_idx[feature]
            label_idx = self.label_to_idx[label]
            self.emission_weights[feature_idx, label_idx] = weight

        # Create a NumPy matrix with size (n_labels, n_labels) and populate with the
        # weights.
        self.transition_weights = np.zeros(
            (self.n_labels, self.n_labels), dtype=np.float32
        )
        for feat, weight in transition_weights.items():
            prev_label, current_label = feat.split("|")
            prev_label_idx = self.label_to_idx[prev_label]
            current_label_idx = self.label_to_idx[current_label]
            self.transition_weights[prev_label_idx, current_label_idx] = weight

    def __repr__(self):
        return f"NumpyViterbiInference(labels={sorted(self.label_to_idx.keys())})"

    def _features_to_idx_array(self, features: set[str]) -> np.ndarray:
        """Map set of feature strings to row indices in emission matrix.

        Parameters
        ----------
        features : set[str]
            Set of feature strings to return indices of.

        Returns
        -------
        np.ndarray
            NumPy array of integer indices for string features.
        """
        return np.array(
            [
                self.features_to_idx[feat]
                for feat in features
                if feat in self.features_to_idx
            ]
        )

    def predict_sequence(self, features_seq: list[set[str]]) -> list[str]:
        """Predict the label sequence using Viterbi algorithm for a sequence of tokens
        described by sequence of features sets.

        Parameters
        ----------
        features_seq : list[set[str]]
            List of sets of features for tokens in sequence.

        Returns
        -------
        list[str]
            List of labels for sequence.
        """
        seq_len = len(features_seq)

        # Pre-compute state scores for all elements of sequence from emission matrix.
        # Rows: sequence elements
        # Columns: labels
        state_scores = np.zeros((seq_len, self.n_labels), dtype=np.float64)
        for t, features in enumerate(features_seq):
            indices = self._features_to_idx_array(features)
            if len(indices) > 0:
                # Sum the weights for the selected features by column (label) and assign
                # to the correct row of the emission_scores matrix.
                state_scores[t] = self.emission_weights[indices].sum(axis=0)

        # Initialize the Viterbi lattice as NumPy arrays.
        # One array for the scores, initialized to -inf. This is the best score for each
        # label given the previous label specified by the backpointers array.
        # One array for the backpointers, which hold the index of the previous label
        # that resulted in the score in the lattice_scores array.
        lattice_scores = np.full((seq_len, self.n_labels), -np.inf)
        backpointers = np.zeros((seq_len, self.n_labels), dtype=np.int8)

        # Deal with the first element of the sequence separately because the scores here
        # are only based on the emission features.
        lattice_scores[0] = state_scores[0]

        # Forward pass, starting at t=1 because we've already initialised t=0
        for t in range(1, seq_len):
            # Get the scores for each label from the previous lattice row.
            # [:, np.newaxis] rotates this into a column vector because this is the
            # previous label to the current label, so we need to broadcast across the
            # rows of the transition matrix.
            prev_el_scores = lattice_scores[t - 1][:, np.newaxis]

            # Candidates is a (n_label, n_label) shaped matrix containing the total
            # scores for transition from each previous label to the current label.
            # We broadcast the prev_el_scores across all rows in the transition
            # matrix and broadcast the emission_scores across all columns to end up
            # with the sum of relevant weights for each label -> label transition.
            candidates = prev_el_scores + self.transition_weights + state_scores[t]

            # Find the best score in each column and the index of the best score in each
            # column and save to the lattice_scores and backpointers matrices
            # respectively.
            lattice_scores[t] = np.max(candidates, axis=0)
            backpointers[t] = np.argmax(candidates, axis=0)

        # Back tracking through the lattice to find the best scoring sequence.
        label_seq = []
        # Find the best label for the last element of the lattice, since there isn't a
        # backpointer for this.
        backpointer = int(np.argmax(lattice_scores[-1]))
        # Iterate backwards through the lattice.
        # At each step, append the backpointer that yielded the best score to the label
        # sequence. Note the the resultant label sequence will be in reverse.
        for t in range(seq_len - 1, -1, -1):
            label_seq.append(self.idx_to_label[backpointer])
            backpointer = int(backpointers[t, backpointer])

        return list(reversed(label_seq))

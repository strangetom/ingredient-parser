#!/usr/bin/env python3

import gzip
import json
import logging
import mimetypes

import numpy as np

logger = logging.getLogger(__name__)

# Type alias for dict of token features.
FeatureDict = dict[str, str | bool]


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

    def tag_from_features(
        self, sentence_features: list[FeatureDict]
    ) -> list[tuple[str, float]]:
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

    def marginal(self, label: str, position: int) -> float:
        """Return the probability of label, label, at position, position, for the most
        recent sequence passed to predict_sequence.

        Parameters
        ----------
        label : str
            Label at position.
        index : int
            Position in sequence.

        Returns
        -------
        float
            Description

        Raises
        ------
        ValueError
            Description
        """
        if self.model.marginals.size == 0:
            raise ValueError(
                "Cannot return marginals until predict_sequence() has been called."
            )

        label_idx = self.model.label_to_idx[label]
        return float(self.model.marginals[position, label_idx])

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

        # Attribute to store marginals matrix once labels have been predicted for a
        # sequence.
        self.marginals = np.array([])

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

    def predict_sequence(self, features_seq: list[set[str]]) -> list[tuple[str, float]]:
        """Predict the label sequence using Viterbi algorithm for a sequence of tokens
        described by sequence of features sets.

        Parameters
        ----------
        features_seq : list[set[str]]
            List of sets of features for tokens in sequence.

        Returns
        -------
        list[tuple[str, float]]
            List of (label, confidence) tuples for the sequence.
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
        label_indices = [0] * seq_len
        # Find the best label for the last element of the lattice, since there isn't a
        # backpointer for this.
        label_indices[-1] = int(np.argmax(lattice_scores[-1]))
        # Iterate backwards through the lattice.
        # At each step, append the backpointer that yielded the best score to the label
        # sequence. Note the the resultant label sequence will be in reverse.
        for t in range(seq_len - 2, -1, -1):
            label_indices[t] = int(backpointers[t + 1, label_indices[t + 1]])

        predicted_labels = [self.idx_to_label[idx] for idx in label_indices]

        # Compute marginals using Log-Sum-Exp for numerical stability
        # The marginal is calculated as
        #        P(y_t = i| x) = \frac{\alpha_{t, i} \cdot \beta_{t, i}}{Z}
        # Where P is the probability of the label at position t having the value i given
        # the sequence x.
        # \alpha{t, i} is the sum of the scores for all possible paths from the start of
        # the sequence to position t that end with label i.
        # \beta{t, i} is the sum of the scores for all possible paths from position t
        # with label i to the end of the sequence.
        # Z is the partition function, a normalisation term that is the total score of
        # all possible paths through the sequence.
        #
        # The calculation is more straight forward and stable to implement as logs:
        #     log(P) = log(\alpha_{t, i}) + log(\beta_{t, i}) - log(Z)
        log_alpha = np.full((seq_len, self.n_labels), -np.inf)
        log_beta = np.full((seq_len, self.n_labels), -np.inf)

        # Forward pass
        log_alpha[0] = state_scores[0]
        for t in range(1, seq_len):
            # logsumexp(prev_alpha + transitions) + current_emissions
            # Get the scores for each label from the previous row of log_alpha.
            # [:, np.newaxis] rotates this into a column vector because this is the
            # previous label to the current label, so we need to broadcast across the
            # rows of the transition matrix.
            log_alpha[t] = (
                np.logaddexp.reduce(
                    log_alpha[t - 1][:, np.newaxis] + self.transition_weights, axis=0
                )
                + state_scores[t]
            )

        # Backward pass
        log_beta[-1] = 0.0  # log(1)
        for t in range(seq_len - 2, -1, -1):
            # logsumexp(transitions + next_emissions + next_beta)
            log_beta[t] = np.logaddexp.reduce(
                self.transition_weights + state_scores[t + 1] + log_beta[t + 1], axis=1
            )

        # Log partition function Z
        log_z = np.logaddexp.reduce(log_alpha[-1])

        # Marginal Probabilities P(y_t | x) = exp(log_alpha + log_beta - log_z)
        log_marginals = log_alpha + log_beta - log_z
        self.marginals = np.exp(log_marginals)

        # Extract the confidence for the specific labels chosen by Viterbi
        confidences = [
            float(self.marginals[t, idx]) for t, idx in enumerate(label_indices)
        ]

        return list(zip(predicted_labels, confidences))

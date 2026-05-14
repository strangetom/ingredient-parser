#!/usr/bin/env python3

import gzip
import json
import logging
import mimetypes
from pathlib import Path

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
    combined_name_labels : bool
        Set to True if there only a single NAME label present in the weights.
        Set to False otherwise.
    """

    def __init__(self, model_file: Path, combined_name_labels: bool = False):
        """Initialise

        Parameters
        ----------
        model_file : Path
            Path to model file.
        combined_name_labels : bool, optional
            If True, name labels are considered combined into a single NAME label.
        """
        self.model_file = model_file
        self.load(model_file)
        self.combined_name_labels = combined_name_labels

    def __repr__(self):
        return (
            f"NumpyCRFInference(model_file='{self.model_file}', "
            f"combined_name_labels={self.combined_name_labels})"
        )

    def tag_from_features(
        self, sentence_features: list[FeatureDict]
    ) -> list[tuple[str, float]]:
        """Tag a sentence with labels using model.

        This function accepts a list of features for each token, rather than
        calculating the features from the tokens.

        If self.combined_name_labels=True, then we cannot apply transition constraints
        because they only apply to I_NAME_TOK.

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
        return self.model.predict_sequence(
            features, constrain_transitions=not self.combined_name_labels
        )

    def _convert_features(self, features: FeatureDict) -> set[str]:
        """Convert features dict to set of strings.

        The model weights use the features as keys, so they need to be a string rather
        than a key: value pair.
        For string features, the string is prepared by joining the key and value by ":".
        For boolean features, the string is prepared just using the key if the boolean
        value is True.

        This only support features that are strings or booleans, which is fine because
        the PreProcessor only outputs features that are string of booleans.
        To support continuous features (float, int) in the future the output of this
        function should be converted to dict[str, float | int] where the key is the
        feature string and the value is a weight that is used to multiply the learned
        model weight for the feature. For string features, the weight would always be 1.
        For boolean features the weight would 1 for True and 0 for False (i.e. the
        feature is ignored by multiplying the learned weight by 0).

        Parameters
        ----------
        features : FeatureDict
            Dictionary of token features token, obtained from PreProcessor.

        Returns
        -------
        set
            Set of features as strings
        """
        return {
            key if isinstance(value, bool) else f"{key}:{value}"
            for key, value in features.items()
            if value is not False  # Skip False booleans
        }

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

    def load(self, path: Path) -> None:
        """Load saved model at given path.

        Parameters
        ----------
        path : Path
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
            scale_factor=data["quantization_scale"],
            zero_offset=data["quantization_zero_offset"],
        )


class NumpyViterbiInference:
    def __init__(
        self,
        features: dict[str, int],
        labels: dict[str, int],
        feature_weights: dict[str, float],
        transition_weights: dict[str, float],
        scale_factor: float,
        zero_offset: float,
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
        scale_factor : float
            Quantization scale factor.
        zero_offset : float
            Quantization zero offset.
        """
        self.label_to_idx = labels
        self.idx_to_label = {idx: label for label, idx in self.label_to_idx.items()}
        self.n_labels = len(labels)
        self.features_to_idx = features
        self.n_features = len(features)
        self.scale_factor = scale_factor
        self.zero_offset = zero_offset

        # Determine data type for weights
        if isinstance(next(iter(feature_weights.values())), int):
            dtype = np.int32
        else:
            dtype = np.float32

        # Create a NumPy matrix with size (n_features, n_labels) and populate with the
        # weights.
        self.emission_weights = np.zeros((self.n_features, self.n_labels), dtype=dtype)
        for feat, weight in feature_weights.items():
            feature, label = feat.split("|")
            feature_idx = self.features_to_idx[feature]
            label_idx = self.label_to_idx[label]
            self.emission_weights[feature_idx, label_idx] = weight

        # Create a NumPy matrix with size (n_labels, n_labels) and populate with the
        # weights.
        self.transition_weights = np.zeros((self.n_labels, self.n_labels), dtype=dtype)
        for feat, weight in transition_weights.items():
            prev_label, current_label = feat.split("|")
            prev_label_idx = self.label_to_idx[prev_label]
            current_label_idx = self.label_to_idx[current_label]
            self.transition_weights[prev_label_idx, current_label_idx] = weight

        # Calculate the de-quantized transition weights now because these do not change.
        self.dq_transition_weights = self._dequantize_affine(self.transition_weights)

        # Attribute to store marginals matrix once labels have been predicted for a
        # sequence.
        self.marginals = np.array([])

    def __repr__(self):
        return f"NumpyViterbiInference(labels={sorted(self.label_to_idx.keys())})"

    def _dequantize_affine(self, weights: np.ndarray) -> np.ndarray:
        """Restores the float values from quantized weights by reversing affine scaling.

        w = (w_q - zero_offset) * scale

        Parameters
        ----------
        weights : np.ndarray
            Weights to de-quantize.

        Returns
        -------
        np.ndarray
            De-quantized weights.
        """
        return (weights.astype(np.float32) - self.zero_offset) / self.scale_factor

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

    def predict_sequence(
        self, features_seq: list[set[str]], constrain_transitions: bool = True
    ) -> list[tuple[str, float]]:
        """Predict the label sequence using Viterbi algorithm for a sequence of tokens
        described by sequence of features sets.

        If constrain_transitions is True, then transitions that are not allowed by the
        labelling scheme are enforced.
        Specifically this means that I_NAME_TOK is prohibited if B_NAME_TOK has not
        occurred since the start of the sentence or since the last NAME_SEP label.

        Parameters
        ----------
        features_seq : list[set[str]]
            List of sets of features for tokens in sequence.
        constrain_transitions : bool, optional
            If True, enforce label transition constraints.
            Default is True.

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

        # Get indices for constraint-specific labels
        b_name_idx = self.label_to_idx.get("B_NAME_TOK")
        i_name_idx = self.label_to_idx.get("I_NAME_TOK")
        name_sep_idx = self.label_to_idx.get("NAME_SEP")
        # Auxiliary matrix to track if B_NAME_TOK has occurred in the best path
        # for each label at each time step since the beginning or last NAME_SEP.
        # Rows: sequence elements
        # Columns: labels
        has_b_name = np.zeros((seq_len, self.n_labels), dtype=bool)

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

        # Apply initial constraints (i.e., I_NAME_TOK cannot be first)
        if constrain_transitions:
            lattice_scores[0, i_name_idx] = -np.inf
            # Update has_b_name matrix for first sequence element
            has_b_name[0, b_name_idx] = True

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

            # Force the scores from constrained transitions to -inf
            if constrain_transitions and b_name_idx:
                # Mask transitions to I_NAME_TOK from paths that lack a B_NAME_TOK
                invalid_prev_paths = ~has_b_name[t - 1]
                candidates[invalid_prev_paths, i_name_idx] = -np.inf

            # Find the best score in each column and the index of the best score in each
            # column and save to the lattice_scores and backpointers matrices
            # respectively.
            lattice_scores[t] = np.max(candidates, axis=0)
            backpointers[t] = np.argmax(candidates, axis=0)

            # Update has_b_name matrix
            if constrain_transitions and b_name_idx:
                # Inherit state from the best predecessor for each current label.
                # We are setting the value of for each column to the value from the
                # previous row (i.e. t-1) at the index given by backpointers[t] so that
                # we inherit whether the best sequence has a B_NAME_TOk.
                has_b_name[t] = has_b_name[t - 1, backpointers[t]]
                # If current label is B_NAME_TOK, the path now has a B_NAME_TOK
                has_b_name[t, b_name_idx] = True
                # If current label is NAME_SEP, the B_NAME_TOK requirement resets
                has_b_name[t, name_sep_idx] = False

        # Back tracking through the lattice to find the best scoring sequence.
        label_indices = [0] * seq_len
        # Find the best label for the last element of the lattice, since there isn't a
        # backpointer for this.
        label_indices[-1] = int(np.argmax(lattice_scores[-1]))
        # Iterate backwards through the lattice.
        # At each step, append the backpointer that yielded the best score to the label
        # sequence.
        for t in range(seq_len - 2, -1, -1):
            label_indices[t] = int(backpointers[t + 1, label_indices[t + 1]])

        predicted_labels = [self.idx_to_label[idx] for idx in label_indices]

        self.marginals = self._compute_marginals(seq_len, state_scores)
        # Extract the confidence for the specific labels chosen by Viterbi
        confidences = [
            float(self.marginals[t, idx]) for t, idx in enumerate(label_indices)
        ]

        return list(zip(predicted_labels, confidences))

    def _compute_marginals(self, seq_len: int, state_scores: np.ndarray) -> np.ndarray:
        """Compute marginals using Log-Sum-Exp for numerical stability

        The marginal is calculated as
            `P(y_t = i| x) = alpha_{t, i} x beta_{t, i} / Z`

        Where P is the probability of the label at position t having the value i given
        the sequence x.
        alpha{t, i} is the sum of the scores for all possible paths from the start of
        the sequence to position t that end with label i.
        beta{t, i} is the sum of the scores for all possible paths from position t
        with label i to the end of the sequence.
        Z is the partition function, a normalisation term that is the total score of
        all possible paths through the sequence.
        The calculation is more straight forward and stable to implement as logs:
            `log(P) = log(alpha_{t, i}) + log(beta_{t, i}) - log(Z)`

        Parameters
        ----------
        seq_len : int
            Sequence length.
        state_scores : np.ndarray
            State score matrix.

        Returns
        -------
        np.ndarray
            Marginal probability matrix for each label at each position in the sequence.
        """
        # De-quantize state scores for marginal calculations.
        state_scores = self._dequantize_affine(state_scores)

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
                    log_alpha[t - 1][:, np.newaxis] + self.dq_transition_weights, axis=0
                )
                + state_scores[t]
            )

        # Backward pass
        log_beta[-1] = 0.0  # log(1)
        for t in range(seq_len - 2, -1, -1):
            # logsumexp(transitions + next_emissions + next_beta)
            log_beta[t] = np.logaddexp.reduce(
                self.dq_transition_weights + state_scores[t + 1] + log_beta[t + 1],
                axis=1,
            )

        # Log partition function Z
        log_z = np.logaddexp.reduce(log_alpha[-1])

        # Marginal Probabilities P(y_t | x) = exp(log_alpha + log_beta - log_z)
        log_marginals = log_alpha + log_beta - log_z
        return np.exp(log_marginals)

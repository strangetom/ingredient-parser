#!/usr/bin/env python3

import gzip
import json
import logging
import mimetypes
from itertools import pairwise
from pathlib import Path

import numpy as np

from ._common import group_consecutive_idx

logger = logging.getLogger(__name__)

# Type alias for dict of token features.
FeatureDict = dict[str, str | bool]


# Prohibited transitions between labels.
# These are based on the labelling scheme and confirmed as being not present in the
# training data, rather than just being derived directly from the training data.
PROHIBITED_TRANSITIONS = {
    "B_NAME_TOK": {"NAME_MOD", "NAME_VAR"},
    "I_NAME_TOK": {"NAME_MOD"},
    "NAME_MOD": {"PURPOSE", "I_NAME_TOK", "UNIT", "QTY"},
    "NAME_SEP": {"PURPOSE", "I_NAME_TOK", "NAME_SEP"},
    "NAME_VAR": {"COMMENT", "PURPOSE", "I_NAME_TOK", "NAME_MOD", "UNIT", "QTY"},
    "QTY": {"PURPOSE", "NAME_SEP"},
    "PURPOSE": {
        "SIZE",
        "I_NAME_TOK",
        "B_NAME_TOK",
        "NAME_SEP",
        "NAME_MOD",
        "PREP",
        "UNIT",
        "NAME_VAR",
        "QTY",
    },
}


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
        self,
        sentence_features: list[FeatureDict],
        expect_name_in_output: bool = True,
        constrain_transitions: bool = True,
    ) -> list[tuple[str, float]]:
        """Tag a sentence with labels using model.

        This function accepts a list of features for each token, rather than
        calculating the features from the tokens.

        If self.combined_name_labels=True, then we cannot apply label transition
        constraints. In this case, constrain_transitions is forced to False.

        Parameters
        ----------
        sentence_features : list[FeatureDict]
            List of feature dicts for each token.
        expect_name_in_output : bool, optional
            If True and the model doesn't label any words in the sentence as the name,
            fallback to selecting the most likely name from any token even though the
            model gives it a different label. Note that this does guarantee the output
            contains a name.
            Default is True.
        constrain_transitions : bool, optional
            If True, constrain label transitions to prevent certain invalid label
            sequences.
            Default is True.

        Returns
        -------
        list[tuple[str, float]]
            List of (label, confidence) tuples.
        """
        if (
            self.model.emission_weights.size == 0
            or self.model.transition_weights.size == 0
        ):
            raise ValueError("NumpyViterbiInference model does not have any weights.")

        if self.combined_name_labels and constrain_transitions:
            logger.debug(
                "Ignoring constrain_transitions=True because combine_name_labels=True."
            )
            constrain_transitions = False

        features = [self._convert_features(f) for f in sentence_features]
        labels, scores = self.model.predict_sequence(
            features, constrain_transitions=constrain_transitions
        )

        if expect_name_in_output and all("NAME" not in label for label in labels):
            # No tokens were assigned the NAME label, so guess if there's a name
            logger.debug(f"No tokens found where name is most probable label: {labels}")
            labels, scores = self._guess_ingredient_name(labels, scores)

        self._detect_invalid_label_sequence(labels)

        return list(zip(labels, scores))

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
            Marginal probability of given label at given position.

        Raises
        ------
        ValueError
            Raised if marginals matrix does not exist.
        """
        if self.model.marginals.size == 0:
            raise ValueError(
                "Cannot return marginals until tag_from_features() has been called."
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

    def _guess_ingredient_name(
        self, labels: list[str], scores: list[float], min_score: float = 0.2
    ) -> tuple[list[str], list[float]]:
        """Guess ingredient name from list of labels and scores.

        This only applies if the token labelling resulted in no tokens being assigned
        the NAME label. When this happens, calculate the confidence of each token being
        NAME, and select the most likely value where the confidence is greater than
        min_score.
        If there are consecutive tokens that meet that criteria, give them all the NAME
        label.

        Parameters
        ----------
        labels : list[str]
            List of token labels.
        scores : list[float]
            List of scores.
        min_score : float
            Minimum score to consider as candidate name.

        Returns
        -------
        list[str], list[float]
            Labels and scores, modified to assign a name if possible.
        """
        # For each element of the sequence, determine the most likely *NAME label whose
        # score exceeds the minimum threshold.
        # Store in a dict -> {element_index: (score, label)}
        candidate_score_labels: dict[int, tuple[float, str]] = {}
        for i, _ in enumerate(labels):
            alt_label_scores = [
                (self.marginal(label, i), label)
                for label in [
                    "B_NAME_TOK",
                    "I_NAME_TOK",
                    "NAME_VAR",
                    "NAME_MOD",
                    "NAME_SEP",
                ]
            ]
            max_score = max(alt_label_scores, key=lambda x: x[0])
            if max_score[0] > min_score:
                candidate_score_labels[i] = max_score

        if len(candidate_score_labels) == 0:
            logger.debug("No viable name tokens identified.")
            return labels, scores

        # Group element indices into groups of consecutive indices.
        groups = [
            list(group)
            for group in group_consecutive_idx(list(candidate_score_labels.keys()))
        ]

        # Take longest group of consecutive indices and replace the labels and scores at
        # these indices with the most likely *NAME labels and their score.
        indices = sorted(groups, key=len, reverse=True)[0]
        for token_index in indices:
            new_score, new_label = candidate_score_labels[token_index]
            labels[token_index] = new_label
            scores[token_index] = new_score

        logger.debug(f"Found alternative name at token indices: {indices}")
        return labels, scores

    def _detect_invalid_label_sequence(self, labels: list[str]) -> None:
        """Detect invalid label sequences in token labels.

        Invalid label sequences are those that violate the labelling scheme. The current
        list of checks are as follows:

        NAME_VAR
        * If there is a NAME_VAR label, there should be at least 2 groups of consecutive
          NAME_VAR groups.
        * The groups of consecutive NAME_VAR labels should be separated by NAME_SEP or
          PUNC.

        NAME_MOD
        * If there is a NAME_MOD label, there should be either
          * 2+ NAME_VARS and 1+ B_NAME_TOK
          * 2+ B_NAME_TOK

        The current implementation only outputs debug messages when invalid sequences
        are detected. Future versions may attempt to fix the problems too.

        Parameters
        ----------
        labels : list[str]
            List of token labels.

        Returns
        -------
        None
        """

        # NAME_VAR checks
        name_var_idx = [i for i, label in enumerate(labels) if label == "NAME_VAR"]
        name_var_groups = [list(g) for g in group_consecutive_idx(name_var_idx)]
        if len(name_var_groups) == 1:
            # There should be at least 2 groups of consecutive NAME_VAR labels.
            logger.debug(
                (
                    "Invalid label sequence for NAME_VAR label: single NAME_VAR group. "
                    "Parsed names may be incorrect."
                )
            )
        elif len(name_var_groups) > 1:
            for group1, group2 in pairwise(name_var_groups):
                # Get indices between groups and check for NAME_SEP or PUNC.
                inbetween_idx = list(range(group1[-1] + 1, group2[0]))
                inbetween_labels = [labels[i] for i in inbetween_idx]
                if not any(label in {"NAME_SEP", "PUNC"} for label in inbetween_labels):
                    # Groups of consecutive NAME_VAR labels should be separated by a
                    # PUNC or NAME_SEP label.
                    logger.debug(
                        (
                            "Invalid label sequence for NAME_VAR label: "
                            "NAME_VAR groups not separated by NAME_SEP or PUNC. "
                            "Parsed names may be incorrect."
                        )
                    )

        # NAME_MOD checks
        name_mod_idx = [i for i, label in enumerate(labels) if label == "NAME_MOD"]
        if name_mod_idx:
            # Get index of last NAME_MOD label.
            name_mod_idx = max(name_mod_idx)
            # Count number of NAME_VAR and B_NAME_TOK labels that occur after the
            # NAME_MOD label.
            name_var_count = sum(
                1 for label in labels[name_mod_idx:] if label == "NAME_VAR"
            )
            b_name_tok_count = sum(
                1 for label in labels[name_mod_idx:] if label == "B_NAME_TOK"
            )
            if not (
                b_name_tok_count >= 2 or (name_var_count >= 2 and b_name_tok_count >= 1)
            ):
                # NAME_MOD should be followed by at least 2 B_NAME_TOK or at least 2
                # NAME_VAR and at least 1 B_NAME_TOK.
                logger.debug(
                    (
                        "Invalid label sequence for NAME_MOD label: "
                        "NAME_MOD is not followed by at least 2 NAME_VAR "
                        "or 2 B_NAME_TOK. "
                        "Parsed names may be incorrect."
                    )
                )

        return None


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

        self.transition_constraint_mask = self._precompute_constraint_mask()

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

    def _precompute_constraint_mask(self) -> np.ndarray:
        """Compute constraint mask.

        This is a boolean matrix of shape (n_labels, n_labels) where a value of 1 means
        that the transition from previous label (row) to current label (column) is
        forbidden.

        Returns
        -------
        np.ndarray
            Boolean matrix indicating forbidden transitions.

        """
        mask = np.zeros((self.n_labels, self.n_labels), dtype=np.bool_)

        for prev_label, constrained_labels in PROHIBITED_TRANSITIONS.items():
            prev_idx = self.label_to_idx[prev_label]
            for idx in [self.label_to_idx[label] for label in constrained_labels]:
                mask[prev_idx, idx] = 1

        return mask

    def predict_sequence(
        self, features_seq: list[set[str]], constrain_transitions: bool = True
    ) -> tuple[list[str], list[float]]:
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
        tuple[list[str], list[float]]
            (List of labels, list of confidences) for the sequence.
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
                candidates[self.transition_constraint_mask] = -np.inf
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

        return predicted_labels, confidences

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

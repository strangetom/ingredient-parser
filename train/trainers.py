#!/usr/bin/env python3

import gzip
import hashlib
import io
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import numpy as np
import scipy

from ingredient_parser.inference import FeatureDict, NumpyViterbi

logger = logging.getLogger(__name__)

TokenFeatureIndices = list[int]
SentenceFeatures = list[TokenFeatureIndices]


@dataclass
class CRFModelParameters:
    attributes: dict[str, int]
    labels: dict[str, int]
    state_features: dict[str, float | int]
    transitions: dict[str, float | int]
    quantization_scale: float
    quantization_zero_offset: int


@dataclass
class CRFHyperParameters:
    optimizer: Literal["L-BFGS-B"]
    l2: float
    maxiter: int  # max_iterations in crfsuite
    maxls: int  # max_linesearch in crfsuite
    ftol: float  # delta in crfsuite
    maxcor: int  # num_memories in crfsuite
    quantize_bits: int
    min_abs_weight: float


class NumpyCRFTrainer:
    # Define default hyper parameters
    hyperparameters = CRFHyperParameters(
        optimizer="L-BFGS-B",
        l2=0.5,
        maxiter=1000,
        maxls=5,
        ftol=5e-5,
        maxcor=3,
        quantize_bits=8,
        min_abs_weight=0.01,
    )
    result: scipy.optimize.OptimizeResult | None = None

    def __init__(
        self,
        training_sentence_features: list[list[FeatureDict]],
        training_sentence_labels: list[list[str]],
    ) -> None:
        self.training_sentences, self.feats_to_idx = self._generate_feature_index_map(
            training_sentence_features
        )
        self.true_sentence_labels, self.labels_to_idx = self._generate_label_index_map(
            training_sentence_labels
        )

        self.observed_feature_counts = self.compute_observed_feature_counts(
            self.training_sentences,
            self.true_sentence_labels,
            len(self.feats_to_idx),
            len(self.labels_to_idx),
        )

    def _generate_feature_index_map(
        self, training_sentence_features: list[list[FeatureDict]]
    ) -> tuple[list[SentenceFeatures], dict[str, int]]:
        """Convert FeatureDicts to list of strings, and create dict mapping string
        features to indices. return the training data features converted to lists of
        indices.

        Parameters
        ----------
        training_sentence_features : list[list[FeatureDict]]
                      List of FeatureDicts for each training sentence.

        Returns
        -------
        tuple[list[SentenceFeatures], dict[str, int]]
            List of SentenceFeatures, which are the features lists for each token
            for each sentence, converted to indices.
            Dict mapping feature string to index.
        """
        converted_training_sentences: list[SentenceFeatures] = []
        feats_to_idx: dict[str, int] = {}

        next_feature_idx = 0
        for sentence_features in training_sentence_features:
            converted_sentence_features: SentenceFeatures = []
            for token_features in sentence_features:
                converted_token_feats: list[int] = []
                for feat in sorted(NumpyViterbi.convert_features(token_features)):
                    if feat not in feats_to_idx:
                        feats_to_idx[feat] = next_feature_idx
                        next_feature_idx += 1
                    converted_token_feats.append(feats_to_idx[feat])

                converted_sentence_features.append(converted_token_feats)

            converted_training_sentences.append(converted_sentence_features)

        return converted_training_sentences, feats_to_idx

    def _generate_label_index_map(
        self, training_sentence_labels: list[list[str]]
    ) -> tuple[list[list[int]], dict[str, int]]:
        """Generate dict mapping label to index and convert all training sentence labels
        to indices.

        Parameters
        ----------
        training_sentence_labels : list[list[str]]
            True labels for each sentence.

        Returns
        -------
        tuple[list[list[int]], dict[str, int]]
            List of label indices for each training sentence.
            Dict mapping label to index.
        """
        converted_training_sentences: list[list[int]] = []
        labels_to_idx: dict[str, int] = {}

        next_label_idx = 0
        for sentence_labels in training_sentence_labels:
            converted_sentence_labels = []
            for label in sentence_labels:
                if label not in labels_to_idx:
                    labels_to_idx[label] = next_label_idx
                    next_label_idx += 1
                converted_sentence_labels.append(labels_to_idx[label])
            converted_training_sentences.append(converted_sentence_labels)

        return converted_training_sentences, labels_to_idx

    def compute_observed_feature_counts(
        self,
        training_sentence_features: list[SentenceFeatures],
        true_sentence_labels: list[list[int]],
        n_features: int,
        n_labels: int,
    ) -> np.ndarray:
        """Compute the observed counts for each observed feature-label combination and
        each previous label-label combination.

        This is returned as a flattened array.

        Parameters
        ----------
        training_sentence_features : list[SentenceFeatures]
            List of feature indices for each token in each training sentence.
        true_sentence_labels : list[list[int]]
            List of label indices for each training sentence.
        n_features : int
            Number of features.
        n_labels : int
            Number of labels.

        Returns
        -------
        np.ndarray
            Flattened array of observed feature counts.
        """
        observed_emissions = np.zeros((n_features, n_labels), dtype=np.float64)
        observed_transitions = np.zeros((n_labels, n_labels), dtype=np.float64)

        for sentence_features_idx, sentence_labels_idx in zip(
            training_sentence_features, true_sentence_labels
        ):
            for t, (token_feats_idx, label_idx) in enumerate(
                zip(sentence_features_idx, sentence_labels_idx)
            ):
                # Increment count for each feature-label pair.
                if token_feats_idx:
                    observed_emissions[token_feats_idx, label_idx] += 1

                # Transitions only exist for the 2nd token onwards.
                if t > 0:
                    prev_label_idx = sentence_labels_idx[t - 1]
                    # Increment count for each previous label-label pair.
                    observed_transitions[prev_label_idx, label_idx] += 1

        # Flatten, to support the format required by scipy.optimize.minimize when
        # training.
        return np.concatenate(
            [observed_emissions.ravel(), observed_transitions.ravel()]
        )

    def train(self, path: Path) -> None:
        """Train model to optimize weights.

        Parameters
        ----------
        path : Path
            Path to save trained model to.
        """
        start_time = time.monotonic()
        self.result = None

        n_features = len(self.feats_to_idx)
        n_labels = len(self.labels_to_idx)

        training_data = list(zip(self.training_sentences, self.true_sentence_labels))

        initial_weights = np.zeros(
            (n_features * n_labels + n_labels * n_labels,), dtype=np.float64
        )
        res = scipy.optimize.minimize(
            fun=crf_objective_function,  # Returns (loss, flat_gradient)
            x0=initial_weights,
            args=(
                training_data,
                self.observed_feature_counts,
                n_features,
                n_labels,
                self.hyperparameters.l2,
            ),
            method=self.hyperparameters.optimizer,
            jac=True,  # Tells scipy the function returns the gradient too
            options={
                "maxiter": self.hyperparameters.maxiter,
                "maxls": self.hyperparameters.maxls,
                "ftol": self.hyperparameters.ftol,
                "maxcor": self.hyperparameters.maxcor,
            },
        )
        self.result = res
        optimised_weights = res.x

        split_point = n_features * n_labels
        self.emission_weights = optimised_weights[:split_point].reshape(
            (n_features, n_labels)
        )
        self.transition_weights = optimised_weights[split_point:].reshape(
            (n_labels, n_labels)
        )

        elapsed_time = timedelta(seconds=int(time.monotonic() - start_time))
        logger.info(f"Model trained in {elapsed_time}.")
        logger.info(f"Stopped after {res.nfev} iterations.")

        # Post training modifications
        self._prune_weights(self.hyperparameters.min_abs_weight)
        scale_factor = 1.0
        if self.hyperparameters.quantize_bits:
            scale_factor = self._quantize(self.hyperparameters.quantize_bits)

        self._simplify_weights()
        self._save(path, scale_factor)

        return res

    def _save(self, path: Path, scale_factor: float):
        """Save trained weights to gzipped json.

        Parameters
        ----------
        path : Path
            Path to save model to.
        scale_factor : float
            Description

        Deleted Parameters
        ------------------
        emission_weights : np.ndarray
            Trained emission weights.
        transition_weights : np.ndarray
            Trained transition weights.
        """

        class NpEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, np.integer):
                    return int(o)
                if isinstance(o, np.floating):
                    return float(o)
                if isinstance(o, np.ndarray):
                    return o.tolist()
                return super(NpEncoder, self).default(o)

        state_features = {}
        for feature, f_idx in self.feats_to_idx.items():
            for label, l_idx in self.labels_to_idx.items():
                weight = self.emission_weights[f_idx, l_idx]
                if weight != 0:
                    state_features[(feature, label)] = weight

        transitions = {}
        for prev_label, p_idx in self.labels_to_idx.items():
            for label, l_idx in self.labels_to_idx.items():
                weight = self.transition_weights[p_idx, l_idx]
                if weight != 0:
                    transitions[(prev_label, label)] = weight

        params = CRFModelParameters(
            attributes=self.feats_to_idx,
            labels=self.labels_to_idx,
            state_features={"\u001f".join(k): v for k, v in state_features.items()},
            transitions={"\u001f".join(k): v for k, v in transitions.items()},
            quantization_scale=scale_factor,
            quantization_zero_offset=0,
        )

        # We use gzip.GzipFile and io.TextIOWrapper so that we can set mtime=0 for the
        # gzip. This removes the timestamp from the output file meaning it is always
        # identical for the same set of model weights.
        with gzip.GzipFile(path, mode="wb", mtime=0) as gz:
            with io.TextIOWrapper(gz, encoding="utf-8") as f:
                json.dump(asdict(params), f, cls=NpEncoder)

    def _quantize(self, nbits: int) -> float:
        """Quantize weights to nbit signed integer using linear scaling.

        Because the model weights are only used additively during inference, and we only
        consider the relative magnitudes of the weights, there is no need for keep the
        scaling factor because it would just be a multiplier of all of the weights.

        Parameters
        ----------
        nbits : int
            Number of bits for integer scaling.
            If None, no quantisation is performed.
            Default is None.

        Returns
        -------
        float
            Description
        """
        # Choose an appropriate type to minimise model size.
        if nbits <= 8:
            type_ = np.int8
        elif nbits <= 16:
            type_ = np.int16
        else:
            type_ = np.int32

        max_weight = max(
            np.max(np.abs(self.emission_weights)),
            np.max(np.abs(self.transition_weights)),
        )

        if max_weight == 0:
            return 1.0

        scale = (2 ** (nbits - 1) - 1) / max_weight
        self.emission_weights = np.round(self.emission_weights * scale).astype(type_)
        self.transition_weights = np.round(self.transition_weights * scale).astype(
            type_
        )
        logger.debug(f"Quantized model weights using {nbits} bits of precision.")
        return scale

    def _prune_weights(self, min_abs_weight: float) -> None:
        """Prune weights by removing weights smaller than min_abs_weight.

        Parameters
        ----------
        min_abs_weight : float
            Minimum absolute value of weight to keep.

        Returns
        -------
        None
            Description
        """
        if min_abs_weight == 0:
            # Nothing to prune
            return None

        initial_weight_count = np.count_nonzero(
            self.emission_weights
        ) + np.count_nonzero(self.transition_weights)
        self.emission_weights[np.abs(self.emission_weights) < min_abs_weight] = 0
        self.transition_weights[np.abs(self.transition_weights) < min_abs_weight] = 0
        remaining_count = np.count_nonzero(self.emission_weights) + np.count_nonzero(
            self.transition_weights
        )
        pruned_pc = 100 * (1 - remaining_count / initial_weight_count)
        logger.debug(
            (
                f"Pruned {pruned_pc:.2f}% of weights for having absolute "
                f"values small than {min_abs_weight}."
            )
        )

    def _simplify_weights(self) -> None:
        """Simplify weights matrix by discarding any rows that are all zeros.

        We also simplify the feature vocab to remove the entries corresponding to those
        rows too.

        We do not need to do this for the transition weights because the size of that
        matrix is known ahead of time.
        """
        # Find row indices where absolute sum of weights is non zero. We keep these and
        # discard the rest.
        mask = np.abs(self.emission_weights).sum(axis=1) > 0
        nonzero_idx = np.argwhere(mask)

        new_feats_to_idx = {}
        next_feature_index = 0
        for feature, idx in sorted(self.feats_to_idx.items(), key=lambda x: x[1]):
            if idx in nonzero_idx:
                new_feats_to_idx[feature] = next_feature_index
                next_feature_index += 1

        self.feats_to_idx = new_feats_to_idx
        # Can't use nonzero_idx to index here because it has the wrong dimensions.
        self.emission_weights = self.emission_weights[mask]

    def write_model_config(
        self, model_file: Path, extra_parameters: dict[str, None | int | float | bool]
    ) -> Path:
        """Write configuration JSON file detail model parameters.

        Parameters
        ----------
        model_file : Path
            Path to model file to generate config for.
        extra_parameters : dict[str, None | int | float | bool]
            Dict of extra model hyperparameters to include in config.

        Returns
        -------
        Path
            Config file path.
        """
        if self.result is None:
            raise ValueError("No training results. Run train() first.")

        if model_file.suffix == ".gz" and model_file.stem.endswith(".json"):
            # Strip suffix (to remove '.gz').
            config_file = model_file.with_suffix("")
        else:
            config_file = model_file.with_suffix(".json")

        config = asdict(self.hyperparameters)
        config["datetime"] = datetime.now().isoformat()
        config["stopping_reason"] = self.result.message

        config.update(extra_parameters)

        with open(model_file, "rb", buffering=0) as f:
            config["sha256"] = hashlib.file_digest(f, "sha256").hexdigest()

        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)

        return config_file


def crf_objective_function(
    flat_weights: np.ndarray,
    training_data: list[tuple[SentenceFeatures, list[int]]],
    observed_counts: np.ndarray,
    n_features: int,
    n_labels: int,
    l2_reg: float = 1.0,
) -> tuple[float, np.ndarray]:
    """
    Compute the regularized Negative Log-Likelihood (NLL) and its analytical gradient.

    This function serves as the primary objective function for optimizing a
    linear-chain Conditional Random Field (CRF) using quasi-Newton algorithms
    (e.g., Scipy's `L-BFGS-B`). It leverages log-space forward-backward
    subroutines to maintain numerical stability and utilizes vectorization to
    efficiently calculate feature expectations.

    The NLL is calculated by ...


    The gradient is calculated by ...

    Parameters
    ----------
    flat_weights : np.ndarray
        A 1D float64 array of shape `(n_features * n_labels + n_labels * n_labels,)`
        containing the flattened parameter weights. The first `n_features * n_labels`
        elements represent the state emission weights, and the remaining
        `n_labels * n_labels` elements represent transition weights.
    training_data : list[tuple[SentenceFeatures, list[int]]]
        A collection of training sequences. Each tuple represents a single sentence
        structured as `(sentence_features, true_labels_idx)`:

        * `sentence_features` : list[list[int]]
            A sequence of positions $t$, where each position contains a list of
            pre-mapped integer feature indices active at that time step.
        * `true_labels_idx` : list[int]
            The ground-truth target label integer indices for the sequence,
            matching the length of `sentence_features`.
    empirical_counts : np.ndarray
        A 1D float64 array matching the shape of `flat_weights`. Represents the
        pre-computed total counts of feature-label and label-label configurations
        observed directly within the ground-truth training dataset.
        Structured identically to flat_weights.
    n_features : int
        The total number of unique features discovered across the training corpus.
    n_labels : int
        The total number of unique target tags/labels within the classification scheme.
    l2_reg : float, default=1.0
        The L2 regularization coefficient. Controls model complexity and
        prevents over-fitting by penalizing large weight magnitudes.

    Returns
    -------
    total_loss : float
        The scalar value of the L2-regularized Negative Log-Likelihood objective.
    flat_gradient : np.ndarray
        A 1D float64 array matching the shape of `flat_weights`. Contains the partial
        derivatives of the loss objective with respect to each parameter weight.
    """
    # Unpack flat weights into 2D matrices for emissions and transitions
    split_point = n_features * n_labels
    emission_weights = flat_weights[:split_point].reshape((n_features, n_labels))
    transition_weights = flat_weights[split_point:].reshape((n_labels, n_labels))

    total_loss = 0.0
    expected_emissions = np.zeros_like(emission_weights)
    expected_transitions = np.zeros_like(transition_weights)

    for sentence_features, true_label_indices in training_data:
        seq_len = len(sentence_features)
        if seq_len == 0:
            continue

        # Compute state scores for current sentence.
        state_scores = np.zeros((seq_len, n_labels), dtype=np.float64)
        for t, feature_indices in enumerate(sentence_features):
            if len(feature_indices) > 0:
                state_scores[t] = emission_weights[feature_indices].sum(axis=0)

        # Compute distribution parameters for current sentence.
        log_alpha, log_beta, log_z, marginals = NumpyViterbi.compute_forward_backward(
            state_scores, transition_weights
        )

        # Compute score for true labels for current sentence.
        true_score = 0.0
        for t, feature_indices in enumerate(sentence_features):
            current_label_idx = true_label_indices[t]
            if len(feature_indices) > 0:
                true_score += emission_weights[feature_indices, current_label_idx].sum()

            # Include transition weights for all but the first token.
            if t > 0:
                prev_label_idx = true_label_indices[t - 1]
                true_score += transition_weights[prev_label_idx, current_label_idx]

        total_loss += log_z - true_score

        # Calculate the emission expectations for the current sentence.
        # This is the marginal probability of each label at each token, accumulated for
        # every active feature of the token.
        # e.g. if t0 has a marginal probability of 0.75 for the label QTY, then all
        # active features for t0 (is_numeric, stem=!num etc.) have the probability added
        # to their value in the expected_emissions matrix.
        #
        # To do this efficiently, we're going to create a list of all the active
        # features (flat_features) and the token index they were active at (flat_t),
        # then use np.add.at to efficiently add the marginal values to the
        # expected_emissions matrix in place to avoid additional memory allocations.
        #
        # Equivalent to:
        # for t, feature_indices in enumerate(features_seq):
        #   token_probabilities = marginals[t]
        #   for f in feature_indices:
        #     expected_emissions[f] += token_probabilities
        #
        flat_features, flat_t = [], []
        for t, feature_indices in enumerate(sentence_features):
            if len(feature_indices) > 0:
                flat_features.extend(feature_indices)
                flat_t.extend([t] * len(feature_indices))

        if flat_features:
            # Add to `expected_emission` at indices `np.s_[flat_features, :]` values
            # `marginals[flat_t].
            np.add.at(expected_emissions, np.s_[flat_features, :], marginals[flat_t])

        # Calculate the transition expectations for the current sentence.
        # This is the marginal probability of each label-label transitions for each
        # token.
        # Equivalent to (but avoids the triple nested loop):
        # for t in range(1, seq_len):
        #   for i in range(n_labels):  # previous label
        #     for j in range(n_labels):  # current label
        #       log_p_transition = (
        #         log_alpha[t-1, i]
        #         + transition_weights[i, j]
        #         + state_scores[t, j]
        #         + log_beta[t, j]
        #         - log_z
        #       )
        #       p_transition = np.exp(log_p_transition)
        #       expected_transitions[i, j] += p_transition
        #
        if seq_len > 1:
            a = log_alpha[:-1, :, np.newaxis]  # (seq_len-1, n_labels, 1)
            w = transition_weights[np.newaxis, :, :]  # (1,         n_labels, n_labels)
            e = state_scores[1:, np.newaxis, :]  # (seq_len-1, 1,         n_labels)
            b = log_beta[1:, np.newaxis, :]  # (seq_len-1, 1,         n_labels)

            log_pairwise = a + w + e + b - log_z
            expected_transitions += np.exp(log_pairwise).sum(axis=0)

    # Apply L2 penalties to overall loss scalar
    total_loss += 0.5 * l2_reg * np.sum(flat_weights**2)

    # Compute the partial gradient for each weight.
    observed_emissions = observed_counts[:split_point].reshape((n_features, n_labels))
    observed_transitions = observed_counts[split_point:].reshape((n_labels, n_labels))

    grad_emissions = expected_emissions - observed_emissions + l2_reg * emission_weights
    grad_transitions = (
        expected_transitions - observed_transitions + l2_reg * transition_weights
    )

    # Flatten matrices back into a single dimension to satisfy Scipy formatting
    # requirements
    flat_gradient = np.concatenate([grad_emissions.ravel(), grad_transitions.ravel()])

    return total_loss, flat_gradient

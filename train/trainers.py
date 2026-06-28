#!/usr/bin/env python3

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from itertools import chain
from pathlib import Path
from typing import Any

import numpy as np
import pycrfsuite

from ingredient_parser.inference import FeatureDict, NumpyCRFInference

logger = logging.getLogger(__name__)


class IngredientParserTrainer(pycrfsuite.Trainer):  # type: ignore
    """Custom modification of the pycrfsuite.Trainer class to provide more useful
    logging.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._iterations = 0
        self._start_time = 0
        self.stopping_reason = None

    def on_start(self, log):
        """Callback called on start of training.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        self._start_time = time.time()

    def on_featgen_progress(self, log, percent):
        """Callback called on during feature generation.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        percent : int
            Percentage of feature generation complete.
        """
        ...

    def on_featgen_end(self, log):
        """Callback called on end of feature generation.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        ...

    def on_prepared(self, log):
        """Callback called on training preparation completed.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        logger.info("Training model with training data.")

    def on_optimization_end(self, log):
        """Callback called on end of optimisation.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        log_lines = [line for line in log.splitlines() if line]
        if len(log_lines) > 1:
            self.stopping_reason = log_lines[0]

    def on_iteration(self, log: str, info: dict[str, Any]):
        """Callback called on every training iteration.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        info : dict[str, Any]
            Log line converted to dict with the following keys:
                num (iteration number)
                loss
                feature_norm
                error_norm
                active_features
                linesearch_trials
                linesearch_step
                time
        """
        self._iterations += 1

    def on_end(self, log):
        """Callback called on end of training.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        elapsed_time = timedelta(seconds=int(time.time() - self._start_time))
        logger.info(f"Model trained in {elapsed_time}.")
        logger.info(f"Stopped after {self._iterations} iterations.")

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
        if model_file.suffix == ".gz" and model_file.stem.endswith(".json"):
            # Strip suffix (to remove '.gz').
            config_file = model_file.with_suffix("")
        else:
            config_file = model_file.with_suffix(".json")

        config = self.get_params()
        config["datetime"] = datetime.now().isoformat()
        config["stopping_reason"] = self.stopping_reason

        config.update(extra_parameters)

        with open(model_file, "rb", buffering=0) as f:
            config["sha256"] = hashlib.file_digest(f, "sha256").hexdigest()

        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)

        return config_file


TokenFeatures = set[str]
SentenceFeatures = list[TokenFeatures]


class NumpyCRFTrainer:
    def __init__(
        self,
        training_sentence_features: list[list[FeatureDict]],
        training_sentence_labels: list[list[str]],
    ) -> None:
        self.true_sentence_labels = training_sentence_labels
        self.training_sentences, self.feats_to_idx = self._generate_feature_index_map(
            training_sentence_features
        )
        self.labels_to_idx = self._generate_label_index_map(training_sentence_labels)

        self.observed_feature_counts = self.compute_observed_feature_counts(
            self.training_sentences,
            self.true_sentence_labels,
            self.feats_to_idx,
            self.labels_to_idx,
        )

    def _generate_feature_index_map(
        self, training_sentence_features: list[list[FeatureDict]]
    ) -> tuple[list[SentenceFeatures], dict[str, int]]:
        """Convert FeatureDicts to set[str] and create dict mapping features to index.

        Parameters
        ----------
        sentence_features: list[list[FeatureDict]]
            List of FeatureDicts for each training sentence.
        """
        converted_training_sentences: list[SentenceFeatures] = []
        unique_features = set()

        for sentence_features in training_sentence_features:
            converted_sentence_features: SentenceFeatures = []
            for token_features in sentence_features:
                converted_token_feats = NumpyCRFInference.convert_features(
                    token_features
                )
                converted_sentence_features.append(converted_token_feats)

                unique_features |= set(chain.from_iterable(token_features))

            converted_training_sentences.append(converted_sentence_features)

        feats_to_idx = {feat: i for i, feat in enumerate(unique_features)}
        return converted_training_sentences, feats_to_idx

    def _generate_label_index_map(
        self, training_sentence_labels: list[list[str]]
    ) -> dict[str, int]:
        """Generate dict mapping label to index.

        Parameters
        ----------
        training_sentence_labels : list[list[str]]
            True labels for each sentence.

        Returns
        -------
        dict[str, int]
            Dict mapping label to index.
        """
        unique_labels = set()
        for sentence_labels in training_sentence_labels:
            unique_labels |= set(chain.from_iterable(sentence_labels))

        return {feat: i for i, feat in enumerate(unique_labels)}

    def compute_observed_feature_counts(
        self,
        training_sentence_features: list[list[set[str]]],
        true_sentence_labels: list[list[str]],
        feats_to_idx: dict[str, int],
        labels_to_idx: dict[str, int],
    ) -> np.ndarray:
        """Compute the observed counts for each observed feature-label combination and
        each previous label-label combination.

        This is returned as a flattened array.

        Parameters
        ----------
        training_data : list[tuple[list[set[str]], list[str]]]
            Each training sentence is a tuple of the sentence features and true labels.
            The sentences features are themselves a list of list[str], where the
            list[str] are the list of features for each token in the sentence.
        features_to_idx : dict[str, int]
            Dict mapping feature to index.
        labels_to_idx : dict[str, int]
            Dict mapping label to index.

        Returns
        -------
        np.ndarray
            Flattened array of observed feature counts.
        """
        observed_emissions = np.zeros(
            (len(feats_to_idx), len(labels_to_idx)), dtype=np.float64
        )
        observed_transitions = np.zeros(
            (len(labels_to_idx), len(labels_to_idx)), dtype=np.float64
        )

        for sentence_features, sentence_labels in zip(
            training_sentence_features, true_sentence_labels
        ):
            # Map labels to indices
            label_indices = [labels_to_idx[label] for label in sentence_labels]

            for t, (token_feats, label_idx) in enumerate(
                zip(sentence_features, label_indices)
            ):
                # Map token features to indices
                token_feat_indices = [
                    feats_to_idx[feat] for feat in token_feats if feat in feats_to_idx
                ]
                # Increment count for each feature-label pair.
                if token_feat_indices:
                    observed_emissions[token_feat_indices, label_idx] += 1

                # Transitions only exist for the 2nd token onwards.
                if t > 0:
                    prev_label_idx = label_indices[t - 1]
                    # Increment count for each previous label-label pair.
                    observed_transitions[prev_label_idx, label_idx] += 1

        # Flatten, to support the format required by scipy.optimize.minimize when
        # training.
        return np.concatenate(
            [observed_emissions.ravel(), observed_transitions.ravel()]
        )

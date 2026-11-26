#!/usr/bin/env python3

import array
import gzip
import io
import json
import logging
import random
from collections import defaultdict
from contextlib import contextmanager
from itertools import chain
from pathlib import Path
from typing import ClassVar, Iterator

import numpy as np

from ._common import is_float, is_fraction, is_range

logger = logging.getLogger(__name__)


class NumpyAveragedPerceptron:
    """Averaged Perceptron for part of speech tagging implemented using NumPy.

    This is designed to be used with NLTK's part of speech tagger weights, but this
    implementation is tailored to the needs of this library. Specifically:
    * NumPy is used for the mathematics, to improve execution performance.
    * Only inference is implemented, no training related code.
    * Tag confidence scores are not calculated.
    * Feature specific weights are always assumed to be 1 and therefore not implemented.


    """

    def __init__(
        self, tags: list[str], weights: np.ndarray, feature_vocab: dict[str, int]
    ) -> None:
        """Initialise NumpyAveragedPerceptron.

        Parameters
        ----------
        tags : list[str]
            List of part of speech tags, sorted alphabetically.
        weights : np.ndarray
            Matrix of weights with size (len(feature_vocab), len(tags))
        feature_vocab : dict[str, int]
            Dict mapping feature to column in weights matrix.
        """
        if weights.shape != (len(feature_vocab), len(tags)):
            raise ValueError(
                f"NumpyAveragedPerceptron.weights has shape {weights.shape}, expected "
                f"({len(feature_vocab)}, {len(tags)})."
            )

        self.tags = tags
        self.n_tags = len(tags)
        self.weights = weights
        self.feature_vocab = feature_vocab

    def __repr__(self):
        return "NumpyAveragedPerceptron()"

    def predict(self, features: list[str]) -> str:
        """Predict the tag for a token described by features list.

        Parameters
        ----------
        features : list[str]
            List of features for token, built from the token properties, previous tags
            and properties of context tokens.

        Returns
        -------
        str
            Tag for token, given the provided features.
        """
        # Convert from feature strings to index in feature vocabulary.
        feature_indices = [
            idx for f in features if (idx := self.feature_vocab.get(f)) is not None
        ]

        # Sum weights for active features across all tags at once.
        # Shape: (n_tags,) i.e. the summed score for each tag.
        if len(feature_indices) > 0:
            scores = self.weights.take(feature_indices, axis=0).sum(axis=0)
        else:
            scores = np.zeros(self.n_tags)

        # Return the best tag.
        return self.tags[scores.argmax()]


class NumpyAveragedPerceptronTrainer:
    """Averaged Perceptron for training part of speech tagging implemented using NumPy.

    ...
    """

    def __init__(self, tags: list[str]):
        self.tags = tags
        # Dict mapping tag to index in weights matrix.
        self.tag_to_idx = {tag: i for i, tag in enumerate(self.tags)}
        self.n_tags = len(tags)

        # Initialise empty feature vocab.
        self.feature_vocab: dict[str, int] = {}
        # Index used when building feature vocab, mapping feature to row in weights
        # matrix.
        self.next_feature_index = 0

        # Assume an initial size for features so we can efficiently size the weights
        # matrix.
        initial_features = 10_000
        # Matrix of weights: [n_features, n_tags]
        self.weights = np.zeros((initial_features, self.n_tags), dtype=np.float32)

        # Accumulated weight for each feature/tag combination
        self._totals = np.zeros((initial_features, self.n_tags), dtype=np.float64)
        # The last iteration each feature/tag combination was changed.
        # This is to avoid having to update every key in self._totals every
        # iteration, we only update each feature/tag key when it changes,
        # accounting for the iterations since it last changed.
        self._tstamps = np.zeros((initial_features, self.n_tags), dtype=np.int32)

        # Count the number of times each feature has been updated (independent of
        # the tag) during training.
        self._feat_updates = np.zeros((initial_features,), dtype=np.int32)
        # The minimum number of feature updates required to consider the feature in
        # the prediction step.
        self.min_feat_updates: int = 0

        # Keep track of total iterations during training so that we know how to average
        # at the end.
        self._iteration: int = 0

    def __repr__(self):
        return "NumpyAveragedPerceptronTrainer()"

    def _resize_matrices(self) -> None:
        """Resize matrices by doubling the number of rows.

        This is called within _features_to_idx during training once the vocabulary
        reaches the current number of rows of the matrices.

        This matrix size doubling approach is used to be efficient during training. The
        maximum size of the weights and other matrices are unknown at the start of
        training, so an initial guess is used. Every time the number of features exceeds
        the size of the matrix we double it's size, thus limited the number of times we
        have to preform this operation.

        At the end of training, _simplify_weights is called to trim the matrix sizes so
        they match the actual number of features and we don't save unused empty rows.
        """
        current_capacity = self.weights.shape[0]
        new_capacity = current_capacity * 2

        # Helper to resize a single matrix and copy data from old matrix into new one.
        def resize_mat(old_mat: np.ndarray) -> np.ndarray:
            ndim = old_mat.ndim
            dtype = old_mat.dtype
            if ndim == 1:
                new_mat = np.zeros((new_capacity,), dtype=dtype)
                new_mat[:current_capacity] = old_mat
            else:  # assume ndim=2, since we don't use anything with higher dimensions.
                cols = old_mat.shape[1]
                new_mat = np.zeros((new_capacity, cols), dtype=dtype)
                new_mat[:current_capacity, :] = old_mat

            return new_mat

        self.weights = resize_mat(self.weights)
        self._totals = resize_mat(self._totals)
        self._tstamps = resize_mat(self._tstamps)
        self._feat_updates = resize_mat(self._feat_updates)

    def _features_to_idx(self, features: list[str]) -> np.ndarray:
        """Map feature string to indices by lookup in vocab dict.

        If the feature is not in the vocabulary, then insert it, resizing the weights
        and other matrices as necessary.

        Parameters
        ----------
        features : list[str]
            Set of feature strings to return indices of.

        Returns
        -------
        np.ndarray
            Array of integer indices for string features.
        """
        for feat in features:
            if feat not in self.feature_vocab:
                self.feature_vocab[feat] = self.next_feature_index
                self.next_feature_index += 1

        # Resize matrices if the vocab now exceeds the current number of rows.
        if self.next_feature_index >= self.weights.shape[0]:
            self._resize_matrices()

        return np.array(
            [idx for f in features if (idx := self.feature_vocab.get(f)) is not None]
        )

    def predict(self, features: list[str]) -> str:
        """Predict the tag for a token described by features list.

        Parameters
        ----------
        features : list[str]
            List of features for token, built from the token properties, previous tags
            and properties of context tokens.

        Returns
        -------
        str
            Tag for token, given the provided features.
        """
        feature_indices = self._features_to_idx(features)

        # Don't consider features until they have been updated more than
        # min_feat_updates times. We only do this during training.
        feature_indices = feature_indices[
            self._feat_updates[feature_indices] >= self.min_feat_updates
        ]

        # Sum weights for active features across all tags at once.
        # Shape: (n_tags,) i.e. the summed score for each tag.
        if len(feature_indices) > 0:
            scores = self.weights.take(feature_indices, axis=0).sum(axis=0)
        else:
            scores = np.zeros(self.n_tags)

        # Return the best tag.
        return self.tags[scores.argmax()]

    def _update_totals(self, tag_index: int, feature_indices: np.ndarray):
        """Update weights for feature by given change

        Parameters
        ----------
        tag_index : int
            Index of tag to update total for.
        feature_indices : np.ndarray
            Array of indices corresponding to features to update weights for.
        """
        # Calculate how many iterations passed since this weight was last touched
        iters = self._iteration - self._tstamps[feature_indices, tag_index]

        # Add the accumulated weight to totals
        # totals += iterations_passed * current_weight
        self._totals[feature_indices, tag_index] += (
            iters * self.weights[feature_indices, tag_index]
        )

        # Update timestamp to current iteration
        self._tstamps[feature_indices, tag_index] = self._iteration

    def update(self, truth: str, guess: str, features: list[str]) -> None:
        """Update weights for given features.

        This only makes changes if the true and predicted tags are different.

        Parameters
        ----------
        truth : str
            True tag for given features.
        guess : str
            Predicted tag for given features.
        features : list[str]
            Features.

        Returns
        -------
        None
        """
        self._iteration += 1

        if truth == guess:
            return None

        # Update the weights and accumulated totals for the features and tags are
        # changing.
        feature_indices = self._features_to_idx(features)
        # For true tag
        truth_idx = self.tag_to_idx[truth]
        self._update_totals(truth_idx, feature_indices)
        self.weights[feature_indices, truth_idx] += 1.0

        # For guess tag
        guess_idx = self.tag_to_idx[guess]
        self._update_totals(guess_idx, feature_indices)
        self.weights[feature_indices, guess_idx] -= 1.0

        # Increment feature update counts.
        # We do this here so that we only increment the count for each feature once,
        # even though we adjusted the weights for different tags for that feature.
        self._feat_updates[feature_indices] += 1

        return None

    def average_weights(self):
        """Average the value for each weight over all updates.

        This is done once at the end of training, and is what makes the Averaged
        Perceptron as effective as it is.
        """
        # Final pass to bring all totals up to date
        iters = self._iteration - self._tstamps
        self._totals += iters * self.weights

        # Average weights
        self.weights = self._totals / self._iteration

    def filter_features(self) -> None:
        """Filter features from weights matrix if they were updated less than than
        min_feat_updates.

        If min_feat_updates is 0, do nothing.

        Note: We have to also set the rows in the _totals matrix to 0 here so that the
        features remain at zero weight for all tags when averaging. If we don't, then
        the features would retain whatever accumulated weight total they had at the last
        iteration the feature was updated.

        Returns
        -------
        None
        """
        if self.min_feat_updates == 0:
            # Nothing to filter
            return None

        # Initial feature count is number of features that have ever been updated.
        initial_feature_count = np.count_nonzero(self._feat_updates)

        # Set row indices where feature has not been updated at least
        # min_feature_updates times.
        # We're only considering rows with at least one feature update here to make the
        # calculation of the logging message easier. We could just do
        # np.argwhere(self._feat_updates < self.min_feat_updates), but that would also
        # include features that have never been updated.
        idx_to_zero = np.argwhere(
            np.logical_and(
                0 < self._feat_updates, self._feat_updates < self.min_feat_updates
            )
        )

        # Set weights for these rows to 0.
        # We also need to set the rows in the _totals matrix to zero for these too so
        # they remain 0 after averaging.
        self.weights[idx_to_zero, :] = 0
        self._totals[idx_to_zero, :] = 0

        filtered_count = idx_to_zero.shape[0]

        filtered_pc = 100 * filtered_count / initial_feature_count
        logger.debug(
            "Removed %0.2f%% of features for updating less than %s times.",
            filtered_pc,
            self.min_feat_updates,
        )

    def prune_weights(self, min_abs_weight: float) -> None:
        """Prune weights by removing weights smaller than min_abs_weight.

        Parameters
        ----------
        min_abs_weight : float
            Minimum absolute value of weight to keep.
        """
        if min_abs_weight == 0:
            # Nothing to prune
            return None

        initial_weight_count = np.count_nonzero(self.weights)
        self.weights[np.abs(self.weights) < min_abs_weight] = 0
        remaining_count = np.count_nonzero(self.weights)
        pruned_pc = 100 * (1 - remaining_count / initial_weight_count)

        logger.debug(
            "Pruned %0.2f%% of weights for having absolute values small than %f.",
            pruned_pc,
            min_abs_weight,
        )

    def quantize(self, nbits: int | None = None) -> None:
        """Quantize weights to nbit signed integer using linear scaling.

        Because the model weights are only used additively during inference, and we only
        consider the relative magnitudes of the weights, there is no need for keep the
        scaling factor because it would just be a multiplier of all of the weights.

        Parameters
        ----------
        nbits : int, optional
            Number of bits for integer scaling.
            If None, no quantisation is performed.
            Default is None.
        """
        if nbits is None:
            return

        # Choose an appropriate type to minimise model size.
        if nbits <= 8:
            type_ = np.int8
        elif nbits <= 16:
            type_ = np.int16
        else:
            type_ = np.int32

        max_weight = np.max(np.abs(self.weights))
        scale = (2 ** (nbits - 1) - 1) / max_weight
        self.weights = np.round(self.weights * scale).astype(type_)
        logger.debug("Quantized model weights using %d bits of precision.", nbits)

    def simplify_weights(self) -> None:
        """Simplify weights matrix by discarding any rows that are all zeros.

        We also simplify the feature vocab to remove the entries corresponding to those
        rows too.
        """
        # Find row indices where absolute sum of weights is non zero. We keep these and
        # discard the rest.
        mask = np.abs(self.weights).sum(axis=1) > 0

        new_feature_vocab = {}
        for feature, idx in sorted(self.feature_vocab.items(), key=lambda x: x[1]):
            if mask[idx]:
                new_feature_vocab[feature] = len(new_feature_vocab)

        self.feature_vocab = new_feature_vocab
        # Can't use nonzero_idx to index here because it has the wrong dimensions, so
        # use mask.
        self.weights = self.weights[mask]


class _FeatureWeightCount(int):
    """Return value of the object_pairs_hook for an inner {tag: weight} object.
    The value is the number of weights in the list of pairs i.e. the number of
    (non-zero) weights for that feature.

    We use a distinct type so we can determine whether the hook has been passed a inner
    {tag: weight} object or the outer {feature: _FeatureWeightCount} object.
    """


class PerceptronTagger:
    START: ClassVar[tuple[str, str]] = ("-START-", "-START2-")
    END: ClassVar[tuple[str, str]] = ("-END-", "-END2-")

    def __init__(
        self,
        model_path: Path | None = None,
        max_cache_size: int = 2**15,
    ):
        """Initialize PerceptronTagger.

        Parameters
        ----------
        model_path : str, optional
            If provided, load model from given location.
        autodownload_weights : bool, optional
            If True, automatically download NLTK's PerceptronTagger weights if missing.
            (the default is True)
        max_cache_size : int, optional
            Sets the maximum cache size when using tag_with_cache().
        """
        self.tagdict = {}

        self.max_cache_size = max_cache_size
        # The tag cache keys are a tuple of the token, context tokens and context token
        # tags that would otherwise be used to generate the features.
        self._tag_cache: dict[tuple[str, ...], str] = {}

        if model_path is not None:
            self.load(model_path)
        else:
            self.model = None

    def __repr__(self):
        return "PerceptronTagger()"

    def tag(self, tokens: list[str], use_tagdict: bool = True) -> list[tuple[str, str]]:
        """Tag a list of tokens using Averaged Perceptron model.

        Parameters
        ----------
        tokens : list[str]
            List of tokens to tag.
        use_tagdict : bool, optional
            When True, the tagdict is used to determine the tag (if present in the
            tagdict), which avoids using the model.
            Default is True.

        Returns
        -------
        list[tuple[str, str]]
            List of (token, tag) tuples.

        Raises
        ------
        ValueError
            Raised if AveragedPerceptron model has not been loaded.
        """
        if self.model is None:
            raise ValueError("AveragedPerceptron model has not been loaded.")

        output = []
        prev, prev2 = self.START
        context = [*self.START, *[self._normalize(w) for w in tokens], *self.END]
        for idx, token in enumerate(tokens):
            tag = self.tagdict.get(token) if use_tagdict else None
            if not tag:
                features = self._get_features(idx, token, context, prev, prev2)
                tag = self.model.predict(features)

            output.append((token, tag))

            prev2 = prev
            prev = tag

        return output

    def tag_with_cache(
        self, tokens: list[str], use_tagdict: bool = True
    ) -> list[tuple[str, str]]:
        """Tag a list of tokens using Averaged Perceptron model.

        The function caches the tags for tokens and their context (including the tags of
        previous tokens in the context) and returns the tag from the cache where
        possible. This is useful when tagging a large number of sentence that contain
        a lot similarities, for example the descriptions of the FDC ingredients,
        because it avoid using the model which makes this quicker.

        This function is intended to be used with the `cache_context()`
        context manager, so that the cache is emptied upon exiting the context.

        Alternative, `clear_cache()` can be called to manually clear the cache.

        If the size of the cache exceeds self.max_cache_size, the cache is cleared.

        Parameters
        ----------
        tokens : list[str]
            List of tokens to tag.
        use_tagdict : bool, optional
            When True, the tagdict is used to determine the tag (if present in the
            tagdict), which avoids using the model and the cache.
            Default is True.

        Returns
        -------
        list[tuple[str, str]]
            List of (token, tag) tuples.

        Raises
        ------
        ValueError
            Raised if AveragedPerceptron model has not been loaded.
        """
        if self.model is None:
            raise ValueError("AveragedPerceptron model has not been loaded.")

        output = []
        prev, prev2 = self.START
        context = [*self.START, *[self._normalize(w) for w in tokens], *self.END]

        offset = len(self.START)
        for idx, token in enumerate(tokens):
            tag = self.tagdict.get(token) if use_tagdict else None
            if not tag:
                i = idx + offset
                cache_key = (
                    token,
                    prev,
                    prev2,
                    context[i - 2],
                    context[i - 1],
                    context[i + 1],
                    context[i + 2],
                )
                tag = self._tag_cache.get(cache_key)
                if not tag:
                    # Fallback to using the model, and add result to cache.
                    features = self._get_features(idx, token, context, prev, prev2)
                    tag = self.model.predict(features)
                    if self.max_cache_size > 0:
                        if len(self._tag_cache) > self.max_cache_size:
                            self._tag_cache.clear()
                            logger.debug(
                                (
                                    "PerceptronTagger tag cache exceeded maximum cache"
                                    " size of %s and was cleared."
                                ),
                                self.max_cache_size,
                            )

                        self._tag_cache[cache_key] = tag

            output.append((token, tag))

            prev2 = prev
            prev = tag

        return output

    def clear_cache(self) -> None:
        """Empty the tag cache of all cached entries."""
        self._tag_cache.clear()

    @contextmanager
    def cache_context(self) -> Iterator["PerceptronTagger"]:
        """Context manager for used with `tag_with_cache`, which clears the cache upon
        exiting the context.

        Examples
        --------
        >>> with tagger.cache_context() as t:
        ...     for tokens in many_token_lists:
        ...         t.tag_with_cache(tokens)
        """
        try:
            yield self
        finally:
            self.clear_cache()

    def _normalize(self, token: str) -> str:
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
        if is_fraction(token):
            return "!FRACTION"

        if is_range(token):
            return "!RANGE"

        if is_float(token):
            return "!NUMBER"

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
            "i pref1 " + (token[0] if token else ""),
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

    @staticmethod
    def _load_tag_weights(
        weights_path: str, tag_to_idx: dict[str, int]
    ) -> tuple[np.ndarray, dict[str, int]]:
        """Memory efficient method of loading tag weights from sparse JSON file.

        To avoid loading complete weights file into memory and then converting into to
        the NumPy array needed by NumpyAveragedPerceptron, we use this slightly more
        memory efficient method of loading the JSON.

        We define an object_pairs_hook callback that is called as each object is parsed
        from the JSON file. This hook will encounter two type of object:
        1. Inner objects, with the form {tag: weight}.
        2. The outer object, with the form {feature: weights}.

        The callback handles the inner objects by storing the tags and weight values in
        dense array objects. When doing so, we return the number of weights in this
        inner object, which we need to be able to assign the (tag, value) pairs to the
        correct row.

        When encountering the outer object (which only happens once), it comprises pairs
        of (feature, weight count), where the weight count came from handling the inner
        objects. We return this unchanged from the callback.

        Parameters
        ----------
        weights_path : str
            Path to tagger weights JSON file.
        tag_to_idx : dict[str, int]
            Dict mapping tag to column index.

        Returns
        -------
        tuple[np.ndarray, dict[str, int]]
            Tagger weights, as a dense NumPy array.
            Feature vocabulary, as a dict mapping the feature to the row of the weights
            matrix.
        """

        # Define arrays for flat storage of tags and their weight as we encounter them
        # when loading the JSON containing the weights.
        # H = unsigned short - this stores the index of the tag.
        tag_cols = array.array("H")
        # d = double - this stores the value of the weight.
        values = array.array("d")

        def object_pairs_hook(
            pairs: list[tuple[str, float]] | list[tuple[str, _FeatureWeightCount]],
        ) -> _FeatureWeightCount | list[tuple[str, _FeatureWeightCount]]:
            if pairs and isinstance(pairs[0][1], _FeatureWeightCount):
                # This is the outer object comprising {feature: _FeatureWeightCount}
                # pairs.
                return pairs

            # Inner objects of (tag: weight) pairs.
            for tag, weight in pairs:
                tag_cols.append(tag_to_idx[tag])
                values.append(weight)

            # Return the number of weights for this set of pairs i.e. for this specific
            # feature.
            return _FeatureWeightCount(len(pairs))

        with open(weights_path) as f:
            # This return from json.load using the object_pairs_hook is a dict of
            # {feature: _FeatureWeightCount} i.e. the number of weights that are
            # non-zero for each feature.
            features = json.load(f, object_pairs_hook=object_pairs_hook)

        # Create feature vocab which maps each feature to it's row index in the dense
        # weights matrix.
        feature_vocab = {feature: i for i, (feature, _) in enumerate(features)}

        # Calculate the row index for every tag weight we have stored in the tag_cols
        # and values arrays above.
        # The features dict contains the number of weights for each feature, so we just
        # need to repeat the row index that many times for each feature.
        weight_counts = np.fromiter((count for _, count in features), dtype=np.int64)
        rows = np.repeat(np.arange(len(features)), weight_counts)

        weights_matrix = np.zeros(
            (len(feature_vocab), len(tag_to_idx)), dtype=np.float64
        )
        weights_matrix[rows, np.frombuffer(tag_cols, dtype=np.uint16)] = np.frombuffer(
            values, dtype=np.float64
        )

        return weights_matrix, feature_vocab

    def load(self, path: Path) -> None:
        """Load saved model.

        Parameters
        ----------
        path : Path
            Path to model data JSON file.

        Raises
        ------
        LookupError
            Raised if PerceptronTagger weights are cannot be found.
        """
        with open(path, "rb") as f:
            model_data = json.loads(gzip.decompress(f.read()))

        # Load tags and sort them to ensure consistency with training.
        tags = sorted(model_data["tags"], reverse=True)
        tag_to_idx = {tag: i for i, tag in enumerate(tags)}
        # Load tagdict
        self.tagdict = model_data["tagdict"]

        # Create weights matrix and feature_vocab and assign weight value for non-zero
        # elements.
        weights_dict = model_data["weights"]
        weights_matrix = np.zeros(
            (len(weights_dict), len(tags)), dtype=np.dtype(model_data["weight_dtype"])
        )
        feature_vocab = {}
        for feature, weights in model_data["weights"].items():
            feature_idx = len(feature_vocab)
            feature_vocab[feature] = feature_idx
            for tag, weight in weights.items():
                tag_idx = tag_to_idx[tag]
                weights_matrix[feature_idx, tag_idx] = weight

        self.model = NumpyAveragedPerceptron(tags, weights_matrix, feature_vocab)
        logger.debug("Part of speech tagger model loaded.")

    def train(
        self,
        tokenised_sentences: list[list[str]],
        truth: list[list[str]],
        n_iter: int = 10,
        min_feat_updates: int = 0,
        min_abs_weight: float = 0,
        quantize_bits: int | None = None,
        make_tag_dict: bool = True,
        tag_dict_frequency_threshold: int = 20,
        tag_dict_ambiguity_threshold: float = 1,
    ) -> None:
        """Train model using example sentences and their true tags.

        Parameters
        ----------
        tokenised_sentences : list[list[str]]
            List of tokenized sentences, each comprising a list of tokens.
        truth : list[list[str]]
            List of true tags for each sentence.
        n_iter : int, optional
            Number of training iterations.
            Default is 10.
        min_feat_updates : int, optional
            Minimum number of feature updates required to consider feature.
        min_abs_weight : float, optional
            Weights below this value will be pruned after training.
            Default is 0.
        quantize_bits : int | None, optional
            Number of bits to quantize weights to after training.
        make_tag_dict : bool, optional
            If True, create a dict of tags for tokens that are unambiguous in the
            training data. Default is True.
        """
        # Generate list of possible tags from truth data.
        tags = list(sorted(set(chain.from_iterable(truth)), reverse=True))
        self.model = NumpyAveragedPerceptronTrainer(tags)

        if len(self.model.tags) == 0:
            raise ValueError("Set the model tags before training.")

        # Empty tagdict at start of training. If make_tag_dict=True, we will regenerate
        # a new tagdict. If not, we don't want to use a stale tagdict.
        self.tagdict = {}
        if make_tag_dict:
            self._make_tagdict(
                tokenised_sentences,
                truth,
                tag_dict_frequency_threshold,
                tag_dict_ambiguity_threshold,
            )

        # Set min_feature_updates for model
        self.model.min_feat_updates = min_feat_updates

        # We need to convert to list before we start training so that we can shuffle the
        # list after each training epoch.
        training_data = list(zip(tokenised_sentences, truth))

        for iter_ in range(n_iter):
            n = 0  # number of total tokens this iteration
            c = 0  # number of correctly tagged tokens this iteration
            for sent, true_tags in training_data:
                prev, prev2 = self.START
                context = [*self.START, *[self._normalize(w) for w in sent], *self.END]
                for idx, (token, true_tag) in enumerate(
                    zip(sent, true_tags, strict=True)
                ):
                    guess = self.tagdict.get(token) if make_tag_dict else None
                    if not guess:
                        features = self._get_features(idx, token, context, prev, prev2)
                        guess = self.model.predict(features)
                        # Update model weights
                        self.model.update(true_tag, guess, features)

                    # Use the guess here to avoid to model becoming over-reliant on the
                    # historical tags being correct
                    prev2 = prev
                    prev = guess

                    n += 1
                    c += guess == true_tag

            logger.info("Iter %d: %0.2f%% correct tokens.", iter_, 100 * c / n)

            if iter_ < n_iter - 1:
                # Shuffle data for next iteration.
                # Don't bother shuffling if this is the last iteration because we won't
                # do anything with the shuffled data.
                random.shuffle(training_data)

        self.model.average_weights()
        self.model.filter_features()
        self.model.prune_weights(min_abs_weight)
        if quantize_bits:
            self.model.quantize(quantize_bits)
        self.model.simplify_weights()

        # Now convert from NumpyAveragedPerceptronTrainer to NumpyAveragedPerceptron for
        # evaluation.
        # If we don't do this, then unknown features will try to trigger matrix resizing
        # and will get added to the feature vocab.
        weights = self.model.weights
        feature_vocab = self.model.feature_vocab
        self.model = NumpyAveragedPerceptron(tags, weights, feature_vocab)

    def _make_tagdict(
        self,
        tokenised_sentences: list[list[str]],
        truth: list[list[str]],
        frequency_threshold: int,
        ambiguity_threshold: float,
    ) -> None:
        """Generate dict of unambiguous token and their tags.

        This dict only includes tokens that occur more than frequency_threshold times in
        the training data, and have the given tag at least frequency_threshold of the
        time.

        Parameters
        ----------
        tokenised_sentences : list[list[str]]
            List of tokenized sentences.
        truth : list[list[str]]
            True tags for each tokenized sentence.
        frequency_threshold : int
            Number of instances of a token to consider as candidate for tagdict.
        ambiguity_threshold : float
            Proportion of times the candidate has a tag for it to be included in the
            tagdict. Value between 0 and 1.
        """
        if not (frequency_threshold > 0):
            raise ValueError(
                f"tagdict frequency_threshold must > 0, not {frequency_threshold}"
            )

        if not (0 < ambiguity_threshold <= 1):
            raise ValueError(
                f"tagdict ambiguity_threshold between [0, 1], not {ambiguity_threshold}"
            )

        counts = defaultdict(lambda: defaultdict(int))
        for tokens, tags in zip(tokenised_sentences, truth):
            for token, tag in zip(tokens, tags):
                counts[token][tag] += 1

        for token, tag_freqs in counts.items():
            tag, mode = max(tag_freqs.items(), key=lambda item: item[1])
            n = sum(tag_freqs.values())
            if n >= frequency_threshold and (float(mode) / n) >= ambiguity_threshold:
                self.tagdict[token] = tag

    def save(self, path: Path):
        """Save model to given path.

        Model is saved as a gzipped JSON file containing the following:
        * tags, the list of tags the model was trained on.
        * features, the list of features the model was trained on.
        * weights, a dict of dicts of non-zero weights in the following format
        {
            "feature_a": {
                "tag_1": weight,
                "tag_2": weight
            },
            "feature_b": {
                "tag_1": weight,
                ...
            },
            ...
        }
        * tagdict, a dict of tags for tokens with unambiguous tags.
        * weight_dtype, the dtype of the weights matrix.

        Parameters
        ----------
        path : Path
            [description]

        Raises
        ------
        ValueError
            [description]
        """
        if self.model is None:
            raise ValueError("AveragedPerceptron model has not been loaded.")

        idx_to_tag = {i: tag for i, tag in enumerate(self.model.tags)}

        # Convert the weights to a native Python type according to the weights matrix
        # dtype.
        if np.issubdtype(self.model.weights.dtype, np.integer):
            type_func = int
        else:
            type_func = float

        weights_as_dict = defaultdict(dict)
        for feature, row_idx in self.model.feature_vocab.items():
            for column_idx, weight in enumerate(self.model.weights[row_idx]):
                if weight != 0:
                    weights_as_dict[feature][idx_to_tag[column_idx]] = type_func(weight)

        model = {
            "tags": self.model.tags,
            "weights": weights_as_dict,
            "tagdict": self.tagdict,
            "weight_dtype": self.model.weights.dtype.name,
        }
        # We use gzip.GzipFile and io.TextIOWrapper so that we can set mtime=0 for the
        # gzip. This removes the timestamp from the output file meaning it is always
        # identical for the same set of model weights.
        with gzip.GzipFile(path, mode="wb", mtime=0) as gz:
            with io.TextIOWrapper(gz, encoding="utf-8") as f:
                json.dump(model, f)

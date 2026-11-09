#!/usr/bin/env python3

import array
import json
import logging
from contextlib import contextmanager
from typing import ClassVar, Iterator

import numpy as np
from nltk.data import find as nltk_find
from nltk.downloader import download as nltk_download

logger = logging.getLogger(__name__)

_WEIGHT_FILE_PREFIX = (
    "taggers/averaged_perceptron_tagger_eng/averaged_perceptron_tagger_eng."
)


class NumpyAveragedPerceptron:
    """Averaged Perceptron for part of speech tagging implemented using NumPy.

    This is design to be used with NLTK's part of speech tagger weights, but this
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
        feature_indices = [
            idx for f in features if (idx := self.feature_vocab.get(f)) is not None
        ]

        # Sum weights for active features across all tags at once.
        # Shape: (n_tags,) i.e. the summed score for each tag.
        if len(feature_indices) > 0:
            scores = self.weights.take(feature_indices, axis=0).sum(axis=0)
        else:
            scores = np.zeros(self.n_tags)

        # Return the best label
        return self.tags[scores.argmax()]


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

    def __init__(self, autodownload_weights: bool = True, max_cache_size: int = 2**15):
        """Initialize PerceptronTagger.

        Parameters
        ----------
        autodownload_weights : bool, optional
            If True, automatically download NLTK's PerceptronTagger weights if missing.
            (the default is True)
        max_cache_size : int, optional
            Sets the maximum cache size when using tag_with_cache().
        """
        self.autodownload_weights = autodownload_weights
        self.tagdict: dict[str, str] = {}

        self.max_cache_size = max_cache_size
        # The tag cache keys are a tuple of the token, context tokens and context token
        # tags that would otherwise be used to generate the features.
        self._tag_cache: dict[tuple[str, ...], str] = {}

        self.load()

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
        """
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

        If the size of the cache exceeds

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
        """
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

    @staticmethod
    def _load_tag_weights(
        weights_path: str, tag_to_idx: dict[str, int]
    ) -> tuple[np.ndarray, dict[str, int]]:
        """Memory efficient method of loading tag weights from spare JSON file.

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
            # This return from json.load using the object_paris_hook is a dict of
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

    def load(self) -> None:
        """Load saved model at given path.

        Parameters
        ----------
        path : str
            Path to model to load.

        Raises
        ------
        LookupError
            Raised if PerceptronTagger weights are cannot be found.
        """
        try:
            tag_path, tagdict_path, weights_path = self._get_weights_paths()
        except LookupError as e:
            if self.autodownload_weights:
                logger.debug(
                    "Downloading required NLTK resource: averaged_perceptron_tagger_eng"
                )
                nltk_download("averaged_perceptron_tagger_eng")
                tag_path, tagdict_path, weights_path = self._get_weights_paths()
            else:
                raise e

        with open(tag_path) as f:
            # Reverse=True is need to maintain consistency with the way the NLTK
            # Perceptron Tagger resolves tied scores.
            tags = sorted(json.load(f), reverse=True)
            tag_to_idx = {tag: i for i, tag in enumerate(tags)}

        with open(tagdict_path) as f:
            self.tagdict = json.load(f)

        weights_matrix, feature_vocab = self._load_tag_weights(weights_path, tag_to_idx)

        self.model = NumpyAveragedPerceptron(tags, weights_matrix, feature_vocab)
        logger.debug("Part of speech tagger model loaded.")

    def _get_weights_paths(self) -> tuple[str, str, str]:
        """Get paths to weights files for PerceptronTagger weights.

        If the files cannot be found, a LookupError is raised.

        Returns
        -------
        tuple[str, str, str]
            tag_path, tagdict_path, weights_path
        """
        tag_path = nltk_find(_WEIGHT_FILE_PREFIX + "classes.json")
        tagdict_path = nltk_find(_WEIGHT_FILE_PREFIX + "tagdict.json")
        weights_path = nltk_find(_WEIGHT_FILE_PREFIX + "weights.json")
        return tag_path, tagdict_path, weights_path

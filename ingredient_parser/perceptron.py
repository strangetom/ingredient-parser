#!/usr/bin/env python3

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

        with open(weights_path) as f:
            weights_dict = json.load(f)

        rows, cols, vals = [], [], []
        feature_vocab = {}
        for feat_idx, (feature, tag_weights) in enumerate(weights_dict.items()):
            feature_vocab[feature] = feat_idx
            for tag, weight in tag_weights.items():
                rows.append(feat_idx)
                cols.append(tag_to_idx[tag])
                vals.append(weight)

        weights_matrix = np.zeros((len(feature_vocab), len(tags)), dtype=np.float64)
        weights_matrix[rows, cols] = vals

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

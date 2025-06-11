#!/usr/bin/env python3

import nltk

from ..dataclasses import Token
from ._constants import FLATTENED_UNITS_LIST, SIZES


class MIP:
    """
    Multi-ingredient Phrases.

    This class handles the detection of multi-ingredient phrases in an ingredient
    sentence, and the generation of features for tokens within the multi-ingredient
    phrase.

    A multi-ingredient phrase is a phrase within an ingredient sentence that states a
    list of alternative ingredients for a give amount. For example
    * 2 tbsp butter or olive oil
             ^^^^^^^^^^^^^^^^^^^
    * 1 cup vegetable, olive or sunflower oil
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    """

    mip_parser = nltk.RegexpParser(
        r"""
        # Extended multi-ingredient phrase containing of 3 ingredients
        EMIP: {<NN.*|JJ.*>+<,><NN.*|JJ.*>+<CC><NN.*|JJ.*>*<NN.*>}
        # Multi-ingredient phrase containing of 2 ingredients
        MIP: {<NN.*|JJ.*>+<CC><NN.*|JJ.*>*<NN.*>}     
        """
    )

    def __init__(self, tokenized_sentence: list[Token]):
        self.tokenized_sentence = tokenized_sentence
        self.phrases: list[list[int]] = self.detect_phrases(tokenized_sentence)

    def _get_subtree_indices(
        self, parent_tree: nltk.Tree, subtree: nltk.Tree
    ) -> list[int]:
        """Get the indices of a subtree in the parent tree.

        Parameters
        ----------
        parent_tree : nltk.Tree
            Parent tree to find indices of subtree within.
        subtree : nltk.Tree
            Subtree to find within parent tree.

        Returns
        -------
        list[int]
            List of indices of subtree in parent tree.
            If not found, return empty list.
        """
        parent_leaves = parent_tree.leaves()
        subtree_leaves = subtree.leaves()

        subtree_len = len(subtree_leaves)
        for i in range(len(parent_leaves) - subtree_len + 1):
            if (
                parent_leaves[i] == subtree_leaves[0]
                and parent_leaves[i : i + subtree_len] == subtree_leaves
            ):
                return list(range(i, i + subtree_len))

        return []

    def _cc_is_not_or(
        self, text_pos: list[tuple[str, str]], indices: list[int]
    ) -> bool:
        """Return True if conjunction in phrase is not "or".

        Parameters
        ----------
        text_pos : list[tuple[str, str]]
            List of (text, pos) tuples.
        indices : list[int]
            Indices of tokens in phrase.

        Returns
        -------
        bool
            True if phrase conjunction is not "or".
        """
        text = [text_pos[i][0] for i in indices]
        pos = [text_pos[i][1] for i in indices]
        try:
            cc_index = pos.index("CC")
            if text[cc_index].lower() != "or":
                return True
            return False
        except ValueError:
            return False

    def detect_phrases(self, tokenized_sentence: list[Token]) -> list[list[int]]:
        """Detect multi-ingredient phrases in tokenized sentence.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence to detect phrases within.

        Returns
        -------
        list[list[int]]
            List of phrases. Each phrase is specified by the indices of the tokens in
            the tokenized sentence.
        """
        phrases = []

        text_pos = [(token.text, token.pos_tag) for token in self.tokenized_sentence]
        parsed = self.mip_parser.parse(text_pos)
        for subtree in parsed.subtrees(filter=lambda t: t.label() in ["EMIP", "MIP"]):
            indices = self._get_subtree_indices(parsed, subtree)
            # If the conjunction is not "or", skip
            if self._cc_is_not_or(text_pos, indices):
                continue

            # Remove any units or sizes from the beginning of the phrase
            first_idx = indices[0]
            tokens_to_discard = [*FLATTENED_UNITS_LIST, *SIZES]
            while self.tokenized_sentence[first_idx].text.lower() in tokens_to_discard:
                indices = indices[1:]
                first_idx = indices[0]

            # If phrase is empty, skip.
            if not indices:
                continue

            # If first index is now a conjunction, skip.
            if self.tokenized_sentence[indices[0]].pos_tag == "CC" or not indices:
                continue

            phrases.append(indices)

        return phrases

    def token_features(self, index: int, prefix: str) -> dict[str, str | bool]:
        """Return dict of features for token at index.

        Features:
        "mip_start": True if index at start of multi-ingredient phrase.
        "mip_end": True if index at end of multi-ingredient phrase.

        Parameters
        ----------
        index : int
            Index of token to return features for.
        prefix : str
            Feature label prefix.

        Returns
        -------
        dict[str, str | bool]
            Dict of features.
            If index is not in phrase, return empty dict.
        """
        features = {}
        for phrase in self.phrases:
            if index not in phrase:
                continue

            if index == phrase[0]:
                features[prefix + "mip_start"] = True

            if index == phrase[-1]:
                features[prefix + "mip_end"] = True

        return features

    def _candidate_name_mod(self, phrase: list[int], index: int) -> bool:
        """Return True if token at index in phrase is candidate for NAME_MOD label.

        A token is a candidate for NAME_MOD if it is the first element of the phrase.

        Parameters
        ----------
        phrase : list[int]
            List of token indices for phrase.
        index : int
            Index of token to consider.

        Returns
        -------
        bool
            True, if token is first in phrase.
        """
        split_phrase_tokens = list(self._split_phrase(self.tokenized_sentence, phrase))
        if len(split_phrase_tokens[0]) > 1:
            return split_phrase_tokens[0][0].index == index

        return False

    def _split_phrase(self, tokenized_sentence: list[Token], phrase: list[int]):
        """Yield lists of items from *iterable*, where each list is delimited by
        an item where callable *pred* returns ``True``.

            >>> list(split_at("abcdcba", lambda x: x == "b"))
            [['a'], ['c', 'd', 'c'], ['a']]

            >>> list(split_at(range(10), lambda n: n % 2 == 1))
            [[0], [2], [4], [6], [8], []]

        At most *maxsplit* splits are done. If *maxsplit* is not specified or -1,
        then there is no limit on the number of splits:

            >>> list(split_at(range(10), lambda n: n % 2 == 1, maxsplit=2))
            [[0], [2], [4, 5, 6, 7, 8, 9]]

        By default, the delimiting items are not included in the output.
        To include them, set *keep_separator* to ``True``.

            >>> list(split_at("abcdcba", lambda x: x == "b", keep_separator=True))
            [['a'], ['b'], ['c', 'd', 'c'], ['b'], ['a']]

        """
        phrase_tokens = [tokenized_sentence[i] for i in phrase]

        buf = []
        # it = iter(tokenized_sentence)
        for token in phrase_tokens:
            if token.text == "," or token.pos_tag == "CC":
                yield buf
                yield [token]
                buf = []
            else:
                buf.append(token)
        yield buf

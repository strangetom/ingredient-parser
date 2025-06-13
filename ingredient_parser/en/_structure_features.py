#!/usr/bin/env python3

import nltk

from ..dataclasses import Token
from ._constants import FLATTENED_UNITS_LIST, SIZES


class SentenceStrucureFeatures:
    """
    Sentence structure features.

    This class handles the detection and feature generation related to the structure of
    the ingredient sentence.
    * Multi-ingredient phrases
      A multi-ingredient phrase is a phrase within an ingredient sentence that states
      a list of alternative ingredients for a give amount. For example
        * 2 tbsp butter or olive oil
                 ^^^^^^^^^^^^^^^^^^^
        * 1 cup vegetable, olive or sunflower oil
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    * Compound sentences containing multiple ingredients of different amounts
      A compound sentence is a sentence that includes more than one subject. For example
        * 1 tablespoon chopped fresh sage or 1 teaspoon dried sage
                                          ^^^^^^^^^^^^^^^^^^^^^^^^
    """

    mip_parser = nltk.RegexpParser(
        r"""
        # Extended multi-ingredient phrase containing of 3 ingredients
        EMIP: {<NN.*|JJ.*>+<,><NN.*|JJ.*>+<CC><NN.*|JJ.*>*<NN.*>}
        # Multi-ingredient phrase containing of 2 ingredients
        MIP: {<NN.*|JJ.*>+<CC><NN.*|JJ.*>*<NN.*>}
        """
    )

    # RegexpParser to detect the start of the subject phrase.
    # UNIT and SIZE are custom tags, based on the FLATTENED_UNITS_LIST and SIZES
    # constants.
    compound_parser = nltk.RegexpParser(r"CS: {<CC><CD>+<NN.*|JJ.*|UNIT|SIZE>}")

    def __init__(self, tokenized_sentence: list[Token]):
        self.tokenized_sentence = tokenized_sentence
        self.phrases = self.detect_phrases(tokenized_sentence)
        self.sentence_splits = self.detect_sentences_splits(tokenized_sentence)

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
        for subtree in parsed.subtrees(filter=lambda t: t.label() in ["EMIP", "MIP"]):  #  type: ignore
            indices = self._get_subtree_indices(parsed, subtree)  #  type: ignore
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

    def detect_sentences_splits(self, tokenized_sentence: list[Token]) -> list[int]:
        """Return indices of tokens that mark a split in sentence subject.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence to detect phrases within.

        Returns
        -------
        list[int]
            List of indices.
        """
        split_indices = []

        text_pos = []
        for t in tokenized_sentence:
            if t.text.lower() in FLATTENED_UNITS_LIST:
                pos = "UNIT"
            elif t.text.lower() in SIZES:
                pos = "SIZE"
            else:
                pos = t.pos_tag

            text_pos.append((t.feat_text, pos))
        parsed = self.compound_parser.parse(text_pos)
        for subtree in parsed.subtrees(filter=lambda t: t.label() == "CS"):  #  type: ignore
            indices = self._get_subtree_indices(parsed, subtree)  #  type: ignore
            # If the conjunction is not "or", skip
            if self._cc_is_not_or(text_pos, indices):
                continue

            split_indices.append(indices[0])

        return split_indices

    def token_features(self, index: int, prefix: str) -> dict[str, bool]:
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
        dict[str, bool]
            Dict of features.
        """
        features = {
            prefix + "mip_start": False,
            prefix + "mip_end": False,
            prefix + "after_sentence_split": False,
        }
        for phrase in self.phrases:
            if index not in phrase:
                continue

            if index == phrase[0]:
                features[prefix + "mip_start"] = True

            if index == phrase[-1]:
                features[prefix + "mip_end"] = True

        for split_index in self.sentence_splits:
            if index >= split_index:
                features[prefix + "after_sentence_split"] = True

        return features

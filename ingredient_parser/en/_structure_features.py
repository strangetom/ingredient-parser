#!/usr/bin/env python3

import nltk

from ..dataclasses import Token
from ._constants import FLATTENED_UNITS_LIST, SIZES

# Lists of (token, pos) pairs for identifying the start of example phrases.
# For example phrases starting with an preposition/subordinating conjunction (IN)
EXAMPLE_PHRASE_START_IN = [("AS", "IN"), ("LIKE", "IN"), ("E.G.", "IN")]
# For example phrase starting with a JJ-IN pair
EXAMPLE_PHRASE_START_JJ = [[("SUCH", "JJ"), ("AS", "IN")]]


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

    * Examples of ingredients
      Phrases that give more specific examples of the ingredient. For example
        * 1kg floury potatoes, such as King Edward or Maris Piper, peeled
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    """

    # RegexpParser to detect multi-ingredient phrases.
    # Each phrase is made of noun/adjective chunks, separated by a conjunction or
    # punctuation and ending with a noun.
    mip_parser = nltk.RegexpParser(
        r"""
        # Extended multi-ingredient phrase containing of 3 ingredients
        # w, x or y z
        EMIP: {<NN.*|JJ.*>+<,><NN.*|JJ.*>+<,>?<CC><DT|NN.*|JJ.*>*<NN.*>}
        # Multi-ingredient phrase containing of 2 ingredients
        # x or y z
        MIP: {<NN.*|JJ.*>+<CC><DT|NN.*|JJ.*>*<NN.*>}
        """
    )

    # RegexpParser to detect the start of new ingredient sentence in compound sentence.
    # UNIT and SIZE are custom tags, based on the FLATTENED_UNITS_LIST and SIZES
    # constants.
    compound_parser = nltk.RegexpParser(r"CS: {<CC><CD>+<NN.*|JJ.*|UNIT|SIZE>}")

    # RegexpParser to detect phrases of examples of ingredients.
    # A sequence of nouns or adjectives, optionally followed by a comma, repeating zero
    # or more times.
    # Followed by an optional conjunction or determinant.
    # Followed by an optional sequeunce nouns or adjectives.
    # Followed by a noun.
    example_parser = nltk.RegexpParser(r"""
        NP: {(<NN.*|JJ.*>+<,>?)*<CC|DT>?<NN.*|JJ.*>*<NN.*>}
        EX: {<JJ.*>?<IN><NP>}
    """)

    def __init__(self, tokenized_sentence: list[Token]):
        """Initialize.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence.
        """
        self.tokenized_sentence = tokenized_sentence
        self.mip_phrases = self.detect_mip_phrases(tokenized_sentence)
        self.sentence_splits = self.detect_sentences_splits(tokenized_sentence)
        self.example_phrases = self.detect_examples(tokenized_sentence)

    def __repr__(self) -> str:
        return (
            "SentenceStrucureFeatures("
            + f"mip_phrases: {self.mip_phrases}, "
            + f"sentence_splits: {self.sentence_splits}, "
            + f"example_phrases: {self.example_phrases})"
        )

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

    def detect_mip_phrases(self, tokenized_sentence: list[Token]) -> list[list[int]]:
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

    def detect_examples(self, tokenized_sentence: list[Token]) -> list[list[int]]:
        """Detect example phrases in tokenized sentence.

        Example phrases are phrases that give specific examples of an ingredient, for
        example
            1 cup oil, such as vegetable
                       ^^^^^^^^^^^^^^^^^
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
        examples = []

        text_pos = [(token.text, token.pos_tag) for token in self.tokenized_sentence]
        parsed = self.example_parser.parse(text_pos)
        for subtree in parsed.subtrees(filter=lambda t: t.label() == "EX"):  #  type: ignore
            indices = self._get_subtree_indices(parsed, subtree)  #  type: ignore
            phrase_text_pos = [
                (token.text.upper(), token.pos_tag)
                for i, token in enumerate(self.tokenized_sentence)
                if i in indices
            ]

            # Check start of phrase for key words
            if phrase_text_pos[:2] in EXAMPLE_PHRASE_START_JJ:
                examples.append(indices)
                continue
            elif phrase_text_pos[0] in EXAMPLE_PHRASE_START_IN:
                examples.append(indices)
                continue
            elif (
                phrase_text_pos[0][1] == "JJ"
                and phrase_text_pos[1] in EXAMPLE_PHRASE_START_IN
            ):
                # The phrase starts with JJ+IN, but doesn't match any pairs in
                # EXAMPLE_PHRASE_START_JJ.
                # Check if it matches anything in EXAMPLE_PHRASE_START_IN is we ignore
                # the first token.
                examples.append(indices[1:])
                continue

        return examples

    def token_features(self, index: int, prefix: str) -> dict[str, bool]:
        """Return dict of features for token at index.

        Features:
        "mip_start": True if index at start of multi-ingredient phrase.
        "mip_end": True if index at end of multi-ingredient phrase.
        "after_sentence_split": True if index after sentence split.
        "example_phrase": True is index in example phrase.

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
            prefix + "example_phrase": False,
        }
        for phrase in self.mip_phrases:
            if index not in phrase:
                continue

            if index == phrase[0]:
                features[prefix + "mip_start"] = True

            if index == phrase[-1]:
                features[prefix + "mip_end"] = True

        for split_index in self.sentence_splits:
            if index >= split_index:
                features[prefix + "after_sentence_split"] = True

        for phrase in self.example_phrases:
            if index in phrase:
                features[prefix + "example_phrase"] = True

        return features

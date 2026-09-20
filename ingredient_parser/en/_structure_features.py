#!/usr/bin/env python3

import logging

import nltk

from ..dataclasses import Token
from ._constants import DIMENSIONS, FLATTENED_UNITS_LIST, LENGTH_UNITS, SIZES

# Lists of (token, pos) pairs for identifying the start of example phrases.
# For example phrases starting with an preposition/subordinating conjunction (IN)
EXAMPLE_PHRASE_START_IN = [("AS", "IN"), ("LIKE", "IN"), ("E.G.", "IN")]
# For example phrase starting with a JJ-IN pair
EXAMPLE_PHRASE_START_JJ = [[("SUCH", "JJ"), ("AS", "IN")]]


logger = logging.getLogger("ingredient-parser.preprocess._structure_features")


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
    * Dimensional phrases
      Phrases that describe the dimension of the ingredient. For example
        * 1 2 inch long piece of ginger
            ^^^^^^^^^^^
    """

    # RegexpParser to detect multi-ingredient phrases.
    # Each phrase is made of noun/adjective chunks, separated by a conjunction or
    # punctuation and ending with a noun.
    mip_parser = nltk.RegexpParser(
        r"""
        # Extended multi-ingredient phrase containing of 3 ingredients
        # w, x or y z
        EMIP: {<NN.*|JJ.*|VB.*>+<,><NN.*|JJ.*|VB.*>+<,>?<CC><DT|NN.*|JJ.*|VB.*>*<NN.*>}
        # Multi-ingredient phrase containing of 2 ingredients
        # x or y z
        MIP: {<NN.*|JJ.*|VB.*>+<CC><DT|NN.*|JJ.*|VB.*>*<NN.*>}
        """
    )

    # RegexpParser to detect the start of new ingredient sentence in compound sentence.
    # UNIT and SIZE are custom tags, based on the FLATTENED_UNITS_LIST and SIZES
    # constants.
    compound_parser = nltk.RegexpParser(r"""
        CS_WU: {<CC><RB>?<CD|DT>+<RB>?<UNIT|SIZE>+} # with unit: quantity with unit/size
        CS_NU: {<CC><CD>+<NN.*|JJ.*>}  # no unit: quantity but no unit or size
        CS_HALF: {<CC><HALF>} # "or half the", "or half that" etc.
    """)

    # RegexpParser to detect phrases of examples of ingredients.
    # A sequence of nouns or adjectives, optionally followed by a comma, repeating zero
    # or more times.
    # Followed by an optional conjunction or determinant.
    # Followed by an optional sequence nouns or adjectives.
    # Followed by a noun.
    example_parser = nltk.RegexpParser(r"""
        NP: {(<NN.*|JJ.*>+<,>?)*<CC|DT>?<NN.*|JJ.*>*<NN.*>}
        EX: {<JJ.*>?<IN><NP>}
    """)

    # RegexpParser to detect dimensional phrases.
    # Each phrase comprises a number followed by a length unit followed a dimension.
    # There can optionally be a preposition prior to the dimension.
    # LEN and DIM are custom tags based on the LENGTH_UNIT and DIMENSIONS constants.
    # Examples: 1 inch thick, 2 cm in diameter, 1 inch (2 cm) long, ¼ in / 5 mm thick
    dimensional_phrase_parser = nltk.RegexpParser(r"""
        LENGTH: {<CD><LEN>}
        PLENGTH: {<\(><LENGTH><\)>}  # LENGTH in parentheses
        SLENGTH: {<SYM><LENGTH>}  # LENGTH following forward slash
        DP: {<LENGTH><SLENGTH|PLENGTH>?<IN>?<DIM>*}
    """)

    def __init__(self, tokenized_sentence: list[Token]):
        """Initialize.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence.
        """
        self.tokenized_sentence = tokenized_sentence
        self.units_sizes = [*FLATTENED_UNITS_LIST, *SIZES]
        self.mip_phrases = self.detect_mip_phrases(tokenized_sentence)
        self.sentence_splits = self.detect_sentences_splits(tokenized_sentence)
        self.example_phrases = self.detect_examples(tokenized_sentence)
        self.dimensional_phrases = self.detect_dimensional_phrases(tokenized_sentence)

    def __repr__(self) -> str:
        return (
            "SentenceStrucureFeatures("
            + f"mip_phrases: {self.mip_phrases}, "
            + f"sentence_splits: {self.sentence_splits}, "
            + f"example_phrases: {self.example_phrases}), "
            + f"dimensional_phrases: {self.dimensional_phrases})"
        )

    def _get_subtree_indices(
        self, parent_tree: nltk.Tree, labels: list[str]
    ) -> list[tuple[list[int], str]]:
        """Get the indices of a subtree in the parent tree.

        Parameters
        ----------
        parent_tree : nltk.Tree
            Parent tree to find indices of subtree within.
        labels : list[str]
            Labels of subtrees to find indices of.

        Returns
        -------
        list[tuple[list[int], str]]
            List of pairs of (list of indices, label) of subtree in parent tree.
            If not found, return empty list.
        """
        indices = []
        subtree_labels = []

        leaf_idx = 0
        for child in parent_tree:
            if isinstance(child, nltk.Tree):
                num_leaves = len(child.leaves())
                if child.label() in labels:
                    subtree_labels.append(child.label())
                    indices.append(list(range(leaf_idx, leaf_idx + num_leaves)))

                # Jump leaf_idx forwards by num_leaves regardless of whether the child
                # was a Tree we were looking for.
                leaf_idx += num_leaves
            else:
                leaf_idx += 1

        return list(zip(indices, subtree_labels))

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

    def detect_mip_phrases(
        self, tokenized_sentence: list[Token]
    ) -> list[tuple[list[int], str]]:
        """Detect multi-ingredient phrases in tokenized sentence.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence to detect phrases within.

        Returns
        -------
        list[tuple[list[int], str]]
            List of phrases.
            Each phrase is specified by the indices of the tokens in the tokenized
            sentence and the label of the phrase type (i.e. MIP, EMIP).
        """
        phrases = []

        text_pos = [(token.text, token.pos_tag) for token in tokenized_sentence]
        parsed = self.mip_parser.parse(text_pos)
        logger.debug("MIP parser: \n%s", parsed)
        for indices, label in self._get_subtree_indices(parsed, ["EMIP", "MIP"]):  # type: ignore
            # If the conjunction is not "or", skip
            if self._cc_is_not_or(text_pos, indices):
                continue

            # Remove first unit or size from the beginning of the phrase
            first_idx = indices[0]
            if tokenized_sentence[first_idx].text.lower() in self.units_sizes:
                indices = indices[1:]
                first_idx = indices[0]

            # If phrase is empty, skip.
            if not indices:
                continue

            # If first index is now a conjunction, skip.
            if tokenized_sentence[indices[0]].pos_tag == "CC":
                continue

            phrases.append((indices, label))

        return phrases

    def _get_clause_boundary_indices(
        self, phrase_indices: list[int], type_: str
    ) -> list[int]:
        """Get the indices of the clause boundaries in multi-ingredient phrases.

        If type_ is MIP, the boundary is at the first conjunction.
        If type_ is EMIP, the first boundary is at the first comma, the second boundary
        is at the first conjunction.

        Parameters
        ----------
        phrase_indices : list[int]
            Indices of multi-ingredient phrase.
        type_ : str
            Type of phrase i.e. MIP, EMIP.

        Returns
        -------
        list[int]
            List of indices of clause boundaries.
        """
        boundary_indices = []

        tags = [
            token.pos_tag
            for i, token in enumerate(self.tokenized_sentence)
            if i in phrase_indices
        ]
        if type_ == "MIP":
            try:
                index = tags.index("CC")
                boundary_indices.append(phrase_indices[index])
            except ValueError:
                logger.debug(
                    "Did not find MIP clause boundary in phrase at indices: %s",
                    phrase_indices,
                )

        elif type_ == "EMIP":
            # First boundary at first comma.
            # Second boundary at first conjunction.
            try:
                index = tags.index(",")
                boundary_indices.append(phrase_indices[index])
            except ValueError:
                logger.debug(
                    "Did not find 1st EMIP clause boundary in phrase at indices: %s",
                    phrase_indices,
                )

            try:
                index = tags.index("CC")
                boundary_indices.append(phrase_indices[index])
            except ValueError:
                logger.debug(
                    "Did not find 2nd EMIP clause boundary in phrase at indices: %s",
                    phrase_indices,
                )

        return boundary_indices

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
            elif t.text.lower() == "half":
                pos = "HALF"
            else:
                pos = t.pos_tag

            text_pos.append((t.feat_text, pos))

        parsed = self.compound_parser.parse(text_pos)
        logger.debug("Sentence split parser: \n%s", parsed)
        for indices, _ in self._get_subtree_indices(
            parsed,  # type: ignore
            ["CS_WU", "CS_NU", "CS_HALF"],
        ):
            # If the conjunction is not "or", skip
            if self._cc_is_not_or(text_pos, indices):
                continue

            split_idx = indices[0]
            if self.tokenized_sentence[split_idx - 1].text.lower() in self.units_sizes:
                # If the token prior to the split is a unit or size, assume that this
                # isn't a split in sentence subject, but rather it's an alternative
                # unit/size e.g. "3 cups or 1 lb ..."
                continue

            split_indices.append(split_idx)

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

        text_pos = [(token.text, token.pos_tag) for token in tokenized_sentence]
        parsed = self.example_parser.parse(text_pos)
        logger.debug("Example parser: \n%s", parsed)
        for indices, _ in self._get_subtree_indices(parsed, ["EX"]):  #  type: ignore
            phrase_text_pos = [
                (token.text.upper(), token.pos_tag)
                for i, token in enumerate(tokenized_sentence)
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
                # Check if it matches anything in EXAMPLE_PHRASE_START_IN if we ignore
                # the first token.
                examples.append(indices[1:])
                continue

        return examples

    def detect_dimensional_phrases(
        self, tokenized_sentence: list[Token]
    ) -> list[list[int]]:
        """Detect dimensional phrases in tokenized sentence.

        Dimensional phrases are phrases the describe the dimension of the ingredient,
        for example:
            1 mm wide
            2 inch long
            10 in diameter

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
        dimensional_phrases = []

        text_pos = []
        for t in tokenized_sentence:
            if t.text.lower() in LENGTH_UNITS and t.pos_tag != "IN":
                # We need to check the POS tag so we don't confuse "in" (preposition)
                # with "in" (abbreviation of inch).
                pos = "LEN"
            elif t.text.lower() in DIMENSIONS:
                pos = "DIM"
            else:
                pos = t.pos_tag

            text_pos.append((t.feat_text, pos))

        parsed = self.dimensional_phrase_parser.parse(text_pos)
        logger.debug("Dimensional phrase parser: \n%s", parsed)
        dimensional_phrases = self._get_subtree_indices(parsed, ["DP"])  # type: ignore
        if dimensional_phrases:
            # Unzip dimensional phrase so we can discard the phrase labels, since
            # they're all "DP".
            dimensional_phrases, _ = zip(*dimensional_phrases)
            return list(dimensional_phrases)

        return []

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
            prefix + "within_mip": False,
            prefix + "after_sentence_split": False,
            prefix + "example_phrase": False,
        }
        for phrase, label in self.mip_phrases:
            if index not in phrase:
                continue

            features[prefix + "within_mip"] = True

            if index == phrase[0]:
                features[prefix + "mip_start"] = True

            if index == phrase[-1]:
                features[prefix + "mip_end"] = True

            boundary_indices = self._get_clause_boundary_indices(phrase, label)
            for i, boundary in enumerate(boundary_indices):
                if index == boundary:
                    # Don't set feature on boundaries.
                    break
                elif index < boundary:
                    # Clauses are enumerated by (negative) distance from end of phrase.
                    distance = -1 * len(boundary_indices) + i
                    features[prefix + f"within_mip_clause_{distance}"] = True
                    break
                elif index > max(boundary_indices):
                    features[prefix + "within_mip_clause_0"] = True

        for split_index in self.sentence_splits:
            if index >= split_index:
                features[prefix + "after_sentence_split"] = True

        for phrase in self.example_phrases:
            if index in phrase:
                features[prefix + "example_phrase"] = True

        for phrase in self.dimensional_phrases:
            if index in phrase:
                features[prefix + "dimensional_phrase"] = True

        return features

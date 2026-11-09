#!/usr/bin/env python3

import logging
from collections import defaultdict
from itertools import chain, groupby

import nltk

from .._common import group_consecutive_idx
from ..dataclasses import Token
from ..inference import FeatureDict
from ._constants import (
    BREAKS,
    CLOSE_BRACKET,
    DIMENSIONS,
    LENGTH_UNITS,
    OPEN_BRACKET,
    OR_TOKENS,
    SIZES,
)

# Lists of (token, pos) pairs for identifying the start of example phrases.
# For example phrases starting with an preposition/subordinating conjunction (IN)
EXAMPLE_PHRASE_START_IN = [("AS", "IN"), ("LIKE", "IN"), ("E.G.", "IN")]
# For example phrase starting with a JJ-IN pair
EXAMPLE_PHRASE_START_JJ = [[("SUCH", "JJ"), ("AS", "IN")]]

logger = logging.getLogger("ingredient-parser.preprocess._structure_features")


class SentenceStructureFeatures:
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

    def __init__(
        self,
        tokenized_sentence: list[Token],
        units: set[str],
        token_is_unit: list[bool],
    ):
        """Initialize.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence.
        units : set[str]
            Set of units, including custom units.
        token_is_unit : list[bool]
            List of bools indicating if token at that position in sentence is a unit.
        """
        self.tokenized_sentence = tokenized_sentence
        self.token_is_unit = token_is_unit
        self._units = units

        # Calculate some flags that we can use to avoid parsing sentences that cannot
        # match certain patterns.
        # The sentence contains a token in OR_TOKENS that has the CC tag.
        self.candidate_CC = any(
            t.pos_tag == "CC" and t.text.lower() in OR_TOKENS
            for t in tokenized_sentence
        )
        # The sentence contains a "as"/"like"/"e.g." token that has the IN tag.
        self.candidate_IN = any(
            t.pos_tag == "IN" and t.text.lower() in {"as", "like", "e.g."}
            for t in tokenized_sentence
        )

        self.mip_features = self.determine_mip_features(tokenized_sentence)
        self.sentence_split_features = self.determine_sentence_split_features(
            tokenized_sentence
        )
        self.example_phrase_features = self.determine_example_phrase_features(
            tokenized_sentence
        )
        self.dimensional_features = self.determine_dimensional_features(
            tokenized_sentence
        )
        self.segment_features = self.determine_segment_features(tokenized_sentence)
        self.paren_span_features = self.determine_paren_features(tokenized_sentence)

    def __repr__(self) -> str:
        return (
            "SentenceStructureFeatures("
            + f"mip_phrases: {self.mip_phrases}, "
            + f"sentence_splits: {self.sentence_splits}, "
            + f"example_phrases: {self.example_phrases}, "
            + f"dimensional_phrases: {self.dimensional_phrases}"
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
            if text[cc_index].lower() not in OR_TOKENS:
                return True
            return False
        except ValueError:
            return False

    def determine_mip_features(
        self, tokenized_sentence: list[Token]
    ) -> list[FeatureDict]:
        """Determine multi-ingredient phrase features for tokens.

        Since all MIP phrases require a token with the CC pos tag, we first check for
        that and return early if not present.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence to detect phrases within.

        Returns
        -------
        list[FeatureDict]
            List of FeatureDicts containing MIP features for each token.
        """
        # mip_phrases is a list of phrases, where each phrases comprises a list of the
        # token indices and the label of the type of phrase (MIP, EMIP).
        # This is convenient to keep for testing purposes.
        self.mip_phrases: list[tuple[list[int], str]] = []

        # Define default MIP features for all tokens.
        mip_features: list[FeatureDict] = [
            {
                "mip_start": False,
                "mip_end": False,
                "within_mip": False,
            }
            for _ in tokenized_sentence
        ]

        if not self.candidate_CC:
            # All the patterns in mip_parser require CC, so there's no point
            # continuing if the sentence does not contain CC.
            return mip_features

        text_pos = [(token.text, token.pos_tag) for token in tokenized_sentence]
        parsed = self.mip_parser.parse(text_pos)
        logger.debug("MIP parser: \n%s", parsed)
        for indices, label in self._get_subtree_indices(parsed, ["EMIP", "MIP"]):  # type: ignore
            # If the conjunction is not "or", skip
            if self._cc_is_not_or(text_pos, indices):
                continue

            # Remove first unit or size from the beginning of the phrase
            first = tokenized_sentence[indices[0]].text.lower()
            if first in self._units or first in SIZES:
                indices = indices[1:]

            # If phrase is empty, skip.
            if not indices:
                continue

            # If first index is now a conjunction, skip.
            if tokenized_sentence[indices[0]].pos_tag == "CC":
                continue

            self.mip_phrases.append((indices, label))
            # Determine features for tokens in this multi-ingredient phrase.
            clauses, clause_boundaries = self._get_mip_clauses(indices, label)

            mip_clause_pattern = "-".join(str(len(c)) for c in clauses)

            # Get the last stem of the last clause.
            head_stem = tokenized_sentence[indices[-1]].features.stem
            # Get the first stem of the first clause.
            first_stem = tokenized_sentence[indices[0]].features.stem

            clause = 0
            for i, index in reversed(list(enumerate(indices))):
                mip_features[index]["mip_clause_pattern"] = mip_clause_pattern
                mip_features[index]["shared_head_stem"] = head_stem
                mip_features[index]["shared_first_stem"] = first_stem
                mip_features[index]["within_mip"] = True
                if i == 0:
                    mip_features[index]["mip_start"] = True
                elif i == len(indices) - 1:
                    mip_features[index]["mip_end"] = True

                if index in clause_boundaries:
                    # Decrement clause number
                    clause -= 1
                    # Don't set the within_mip_clause_ feature for clause boundary
                    # tokens.
                    continue

                mip_features[index]["mip_clause"] = str(clause)

                clause_start_index = clauses[clause][0]
                clause_first_pos = tokenized_sentence[clause_start_index].pos_tag
                mip_features[index]["clause_first_pos"] = clause_first_pos

        return mip_features

    def _get_mip_clauses(
        self, phrase_indices: list[int], type_: str
    ) -> tuple[list[list[int]], list[int]]:
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
        tuple[list[list[int]], list[int]]
            List of clauses, each defined as a list of indices.
            List of indices of clause boundaries.
        """
        boundary_indices = []

        tags = [self.tokenized_sentence[i].pos_tag for i in phrase_indices]
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

        # Group phrase indices into clauses, ignoring the boundary tokens.
        clauses = [
            list(clause)
            for is_boundary, clause in groupby(
                phrase_indices, key=lambda i: i in boundary_indices
            )
            if not is_boundary
        ]

        return clauses, boundary_indices

    def determine_sentence_split_features(
        self, tokenized_sentence: list[Token]
    ) -> list[FeatureDict]:
        """Return indices of tokens that mark a split in sentence subject.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence to detect phrases within.

        Returns
        -------
        list[FeatureDict]
            List of FeatureDicts containing sentence split features.
        """
        # sentence_splits is a list of indices where a CC token indicates a semantic
        # split in the sentence.
        # This is convenient to keep for testing purposes.
        self.sentence_splits: list[int] = []

        # By default all "after_sentence_split" features are False.
        sentence_split_features: list[FeatureDict] = [
            {"after_sentence_split": False} for _ in tokenized_sentence
        ]

        if not self.candidate_CC:
            # All the patterns in compound_parser require CC, so there's no point
            # continuing if the sentence does not contain CC.
            return sentence_split_features

        text_pos = []
        for t in tokenized_sentence:
            if self.token_is_unit[t.index]:
                pos = "UNIT"
            elif t.text.lower() in SIZES:
                pos = "SIZE"
            elif t.text.lower() == "half":
                pos = "HALF"
            elif t.text.lower().endswith("%"):
                # For the purposes of detecting compound sentences, numeric tokens
                # ending with '%' are not useful markers, so change their pos to VB.
                pos = "VB"
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
            token_before_split = self.tokenized_sentence[split_idx - 1].text.lower()
            if split_idx > 0 and (
                token_before_split in self._units or token_before_split in SIZES
            ):
                # If the token prior to the split is a unit or size, assume that this
                # isn't a split in sentence subject, but rather it's an alternative
                # unit/size e.g. "3 cups or 1 lb ..."
                continue

            # Set after_sentence_split=True for all tokens after split
            self.sentence_splits.append(split_idx)
            for features in sentence_split_features[split_idx:]:
                features["after_sentence_split"] = True

        return sentence_split_features

    def determine_example_phrase_features(
        self, tokenized_sentence: list[Token]
    ) -> list[FeatureDict]:
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
        list[FeatureDict]
            List of FeatureDicts containing example phrase features for each token.
        """
        # example_phrases is a list of list of indices which indicate example phrases.
        # This is convenient to keep for testing purposes.
        self.example_phrases: list[list[int]] = []

        # By default all "example_phrase" features are False.
        example_phrase_features: list[FeatureDict] = [
            {"example_phrase": False} for _ in tokenized_sentence
        ]

        if not self.candidate_IN:
            # All the patterns in example_parser require IN, so there's no point
            # continuing if the sentence does not contain IN.
            return example_phrase_features

        text_pos = [(token.text, token.pos_tag) for token in tokenized_sentence]
        parsed = self.example_parser.parse(text_pos)
        logger.debug("Example parser: \n%s", parsed)
        for indices, _ in self._get_subtree_indices(parsed, ["EX"]):  #  type: ignore
            phrase_text_pos = [
                (tokenized_sentence[i].text.upper(), tokenized_sentence[i].pos_tag)
                for i in indices
            ]

            # Check start of phrase for key words
            phrase_indices = []
            if phrase_text_pos[:2] in EXAMPLE_PHRASE_START_JJ:
                phrase_indices = indices
            elif phrase_text_pos[0] in EXAMPLE_PHRASE_START_IN:
                phrase_indices = indices
            elif (
                phrase_text_pos[0][1] == "JJ"
                and phrase_text_pos[1] in EXAMPLE_PHRASE_START_IN
            ):
                # The phrase starts with JJ+IN, but doesn't match any pairs in
                # EXAMPLE_PHRASE_START_JJ.
                # Check if it matches anything in EXAMPLE_PHRASE_START_IN if we ignore
                # the first token.
                phrase_indices = indices[1:]

            if phrase_indices:
                self.example_phrases.append(phrase_indices)
                for index in phrase_indices:
                    example_phrase_features[index]["example_phrase"] = True

        return example_phrase_features

    def determine_dimensional_features(
        self, tokenized_sentence: list[Token]
    ) -> list[FeatureDict]:
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
        list[FeatureDict]
            List of FeatureDicts containing dimensional features
        """
        # dimensional_phrases is a list of list of indices which indicate dimensional
        # phrases.
        # This is convenient to keep for testing purposes.
        self.dimensional_phrases = []

        dimensional_features = [{} for _ in tokenized_sentence]

        # Flag for optimising function call. All the patterns in the
        # dimensional_phrase_parser require a LEN tag, so if we don't find one in the
        # sentence we can avoid parsing the sentence.
        includes_LEN = False

        text_pos = []
        for t in tokenized_sentence:
            if t.text.lower() in LENGTH_UNITS and t.pos_tag != "IN":
                # We need to check the POS tag so we don't confuse "in" (preposition)
                # with "in" (abbreviation of inch).
                pos = "LEN"
                includes_LEN = True
            elif t.text.lower() in DIMENSIONS:
                pos = "DIM"
            else:
                pos = t.pos_tag

            text_pos.append((t.feat_text, pos))

        if not includes_LEN:
            return dimensional_features

        parsed = self.dimensional_phrase_parser.parse(text_pos)
        logger.debug("Dimensional phrase parser: \n%s", parsed)
        dimensional_phrases = self._get_subtree_indices(parsed, ["DP"])  # type: ignore
        if dimensional_phrases:
            # Unzip dimensional phrase so we can discard the phrase labels, since
            # they're all "DP".
            dimensional_phrases, _ = zip(*dimensional_phrases)
            self.dimensional_phrases = list(dimensional_phrases)
            for index in chain.from_iterable(dimensional_phrases):
                dimensional_features[index]["dimensional_phrase"] = True

        return dimensional_features

    def determine_segment_features(
        self, tokenized_sentence: list[Token]
    ) -> list[FeatureDict]:
        """Determine segment based features for tokenized_sentence.

        The current features based on segments are:
        * segment - the segment count, capped at 3.
        * segment_from_end - the segment count starting at the end, capped at 2.
        * segment_position - one of ONLY, FIRST, LAST, MID, SEP.
        * segment_length - number of tokens in segment.
        * segment_starts_with_qty - True if segment starts with a quantity.
        * qty_in_earlier_segment - True if a previous segment contains a quantity.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence to determine segment features for.

        Returns
        -------
        list[FeatureDict]
            List of FeatureDicts containing the segment features for each token.
        """
        segment_members = defaultdict(list)
        for token in tokenized_sentence:
            # Segment break tokens are not considered part of the segment.
            if token.text not in BREAKS:
                segment_members[token.segment].append(token.index)

        last_segment = max(segment_members, default=0)
        segement_features = []
        for token in tokenized_sentence:
            # Cap the segment number at 3 to prevent rare larger values overfitting.
            token_segement_features: FeatureDict = {
                "segment": str(min(token.segment, 3)),
                "segment_from_end": str(min(last_segment - token.segment, 2)),
            }
            if token.text in BREAKS:
                token_segement_features["segment_position"] = "SEP"
                segement_features.append(token_segement_features)
                continue

            members = segment_members[token.segment]
            n_members = len(members)

            if n_members == 1:
                segment_position = "ONLY"
            elif token.index == members[0]:
                segment_position = "FIRST"
            elif token.index == members[-1]:
                segment_position = "LAST"
            else:
                segment_position = "MID"

            token_segement_features["segment_position"] = segment_position

            # We don't include segment_length=1 here because it is identical to
            # segment_position="ONLY"
            if n_members > 1:
                token_segement_features["segment_length"] = (
                    "2" if n_members == 2 else "3-4" if n_members <= 4 else "5+"
                )

            # True if current segment starts with quantity.
            token_segement_features["segment_starts_with_qty"] = (
                tokenized_sentence[members[0]].feat_text == "!num"
            )

            # Indicate if previous segment contained quantity
            if token.segment > 0:
                qty_in_earlier_segment = False
                for previous_segment in range(token.segment):
                    for member in segment_members[previous_segment]:
                        if self.tokenized_sentence[member].feat_text == "!num":
                            qty_in_earlier_segment = True
                            break

                token_segement_features["qty_in_earlier_segment"] = (
                    qty_in_earlier_segment
                )

            segement_features.append(token_segement_features)

        return segement_features

    def determine_paren_features(
        self, tokenized_sentence: list[Token]
    ) -> list[FeatureDict]:
        """Determine parenthesis span based features for tokenized_sentence.

        Parenthesis spans include tokens that are within parentheses or brackets, not
        including the parenthesis or bracket characters themselves. The spans are
        identified from adjacent tokens with the same paren_depth value.

        The current features based on parentheses spans are:
        * paren_first_pos - the POS tag of the first token in a parentheses span.

        Parameters
        ----------
        tokenized_sentence : list[Token]
            Tokenized sentence to determine parentheses span features for.

        Returns
        -------
        list[FeatureDict]
            List of FeatureDicts containing the segment features for each token.
        """
        in_paren_tokens = [
            t.index
            for t in tokenized_sentence
            if t.paren_depth > 0
            and t.text not in OPEN_BRACKET
            and t.text not in CLOSE_BRACKET
        ]
        if in_paren_tokens == []:
            return [{}] * len(tokenized_sentence)

        paren_spans = [list(g) for g in group_consecutive_idx(in_paren_tokens)]
        # Create dict mapping index to paren_span.
        paren_span_map = {idx: span for span in paren_spans for idx in span}
        logger.debug("Parentheses spans: %s", paren_spans)

        parens_features = []
        for token in tokenized_sentence:
            token_paren_span_features: FeatureDict = {}

            paren_span_members = paren_span_map.get(token.index)
            if paren_span_members is None:
                parens_features.append(token_paren_span_features)
                continue

            token_paren_span_features["paren_first_pos"] = tokenized_sentence[
                paren_span_members[0]
            ].pos_tag

            parens_features.append(token_paren_span_features)

        return parens_features

    def token_features(self, index: int) -> FeatureDict:
        """Return dict of features for token at index.

        Parameters
        ----------
        index : int
            Index of token to return features for.

        Returns
        -------
        FeatureDict
            Dict of structure features.
        """
        return {
            **self.mip_features[index],
            **self.sentence_split_features[index],
            **self.example_phrase_features[index],
            **self.dimensional_features[index],
            **self.segment_features[index],
            **self.paren_span_features[index],
        }

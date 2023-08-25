#!/usr/bin/env python3

import collections
import re
from dataclasses import dataclass
from itertools import groupby, islice
from operator import itemgetter
from statistics import mean
from typing import Generator, Iterator

from ._utils import pluralise_units

WORD_CHAR = re.compile(r"\w")

APPROXIMATE_TOKENS = ["about", "approx.", "approximately", "nearly"]
SINGULAR_TOKENS = ["each"]


@dataclass
class IngredientAmount:
    """Dataclass for holding ingredient amount, comprising a quantity and a unit."""

    quantity: str
    unit: str
    confidence: float
    APPROXIMATE: bool = False
    SINGULAR: bool = False


@dataclass
class IngredientText:
    """Dataclass for holding parsed ingredient strings"""

    text: str
    confidence: float


@dataclass
class ParsedIngredient:
    """Dataclass for holding the parsed values for an input sentence.

    * Sentence: The original input sentence
    * Quantity: The parsed quantities from the input sentence
    * Unit: The parsed units from the input sentence
    * Name: The parsed name from the input sentence
    * Comment: The parsed comment from the input sentence
    * Other: Any tokens in the input sentence that were not labelled
    """

    name: IngredientText | None
    amount: list[IngredientAmount]
    comment: IngredientText | None
    other: IngredientText | None
    sentence: str


def consume(iterator: Iterator, n: int) -> None:
    """Advance the iterator n-steps ahead. If n is none, consume entirely.
    See consume from https://docs.python.org/3/library/itertools.html#itertools-recipes

    Parameters
    ----------
    iterator : Iterator
        Iterator to advance.
    n : int
        Number of iterations to advance by.
    """
    if n is None:
        # Feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # Advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)


class PostProcessor:

    """Recipe ingredient sentence PostProcessor class.

    Performs the necessary postprocessing on the sentence tokens and labels and scores
    for the tokens after tagging with the CRF model in order to return a coherent
    structure of parsed information.

    Attributes
    ----------
    labels : list[str]
        List of labels for tokens.
    scores : list[float]
        Confidence associated with the label for each token.
    sentence : str
        Original ingredient sentence.
    tokens : list[str]
        List of tokens for original ingredient sentence.
    """

    def __init__(
        self, sentence: str, tokens: list[str], labels: list[str], scores: list[float]
    ):
        self.sentence = sentence
        self.tokens = tokens
        self.labels = labels
        self.scores = scores

    def __repr__(self) -> str:
        """__repr__ method

        Returns
        -------
        str
            String representation of initialised object
        """
        return f'PostProcessor("{self.sentence}")'

    def __str__(self) -> str:
        """__str__ method

        Returns
        -------
        str
            Human readable string representation of object
        """
        _str = [
            "Post-processed recipe ingredient sentence",
            f"\t{list(zip(self.tokens, self.labels))}",
        ]
        return "\n".join(_str)

    def parsed(self) -> ParsedIngredient:
        """Return parsed ingredient data

        Returns
        -------
        ParsedIngredient
            Object containing structured data from sentence.
        """
        amounts = self._postprocess_amounts()
        name = self._postprocess("NAME")
        comment = self._postprocess("COMMENT")
        other = self._postprocess("OTHER")

        return ParsedIngredient(
            sentence=self.sentence,
            amount=amounts,
            name=name,
            comment=comment,
            other=other,
        )

    def _postprocess(self, selected: str) -> IngredientText | None:
        """Process tokens, labels and scores with selected label into an
        IngredientText object.

        Parameters
        ----------
        selected : str
            Label of tokens to postprocess

        Returns
        -------
        IngredientText
            Object containing ingredient comment text and confidence
        """
        # Select indices of tokens, labels and scores for selected label
        idx = [i for i, label in enumerate(self.labels) if label == selected]

        # Join consecutive tokens together and average their score
        parts = []
        confidence_parts = []
        for group in self._group_consecutive_idx(idx):
            idx = list(group)
            joined = " ".join([self.tokens[i] for i in idx])
            confidence = mean([self.scores[i] for i in idx])

            parts.append(joined)
            confidence_parts.append(confidence)

        # Find the indices of the joined tokens list where the element
        # if a single punctuation mark or is the same as the previous element
        # in the list
        keep_idx = self._remove_isolated_punctuation_and_duplicates(parts)
        parts = [parts[i] for i in keep_idx]
        confidence_parts = [confidence_parts[i] for i in keep_idx]

        # Join all the parts together into a single string and fix any
        # punctuation weirdness as a result.
        text = ", ".join(parts)
        text = self._fix_punctuation(text)

        if len(parts) == 0:
            return None

        return IngredientText(
            text=text,
            confidence=round(mean(confidence_parts), 6),
        )

    def _postprocess_amounts(self) -> list[IngredientAmount]:
        """Process tokens, labels and scores into IngredientAmount objects, by combining
        QTY labels with any following UNIT labels, up to the next QTY label.

        The confidence is the average confidence of all labels in the IngredientGroup.

        If the sequence of QTY and UNIT labels matches the "sizable unit" pattern, determine
        the amounts in a different way.

        Returns
        -------
        list[IngredientAmount]
            List of IngredientAmount objects
        """
        if match := self._sizable_unit_pattern():
            return match
        else:
            return self._fallback_pattern(self.tokens, self.labels, self.scores)

    def _fix_punctuation(self, text: str) -> str:
        """Fix some common punctuation errors that result from combining tokens of the
        same label together.

        Parameters
        ----------
        text : str
            Text resulting from combining tokens with same label

        Returns
        -------
        str
            Text, with punctuation errors fixed
        """
        # Remove leading comma
        if text.startswith(", "):
            text = text[2:]

        # Remove trailing comma
        if text.endswith(","):
            text = text[:-1]

        # Correct space following open parens or before close parens
        text = text.replace("( ", "(").replace(" )", ")")

        # Remove parentheses that aren't part of a matching pair
        idx_to_remove = []
        stack = []
        for i, char in enumerate(text):
            if char == "(":
                # Add index to stack when we find an opening parens
                stack.append(i)
            elif char == ")":
                if len(stack) == 0:
                    # If the stack is empty, we've found a dangling closing parens
                    idx_to_remove.append(i)
                else:
                    # Remove last added index from stack when we find a closing parens
                    stack.pop()

        # Insert anything left in stack into idx_to_remove
        idx_to_remove.extend(stack)
        text = "".join(char for i, char in enumerate(text) if i not in idx_to_remove)

        return text

    def _remove_isolated_punctuation_and_duplicates(
        self, parts: list[str]
    ) -> list[int]:
        """Find elements in list that comprise a single punctuation character or are a
        duplicate of the previous element and discard their indices.

        Parameters
        ----------
        parts : list[str]
            List of tokens with single label, grouped if consecutive

        Returns
        -------
        list[int]
            Indices of elements in parts to keep

        """
        # Only keep a part if contains a word character
        idx_to_keep = []
        for i, part in enumerate(parts):
            if i == 0 and WORD_CHAR.search(part):
                idx_to_keep.append(i)
            elif WORD_CHAR.search(part) and part != parts[i - 1]:
                idx_to_keep.append(i)

        return idx_to_keep

    def _group_consecutive_idx(
        self, idx: list[int]
    ) -> Generator[Iterator[int], None, None]:
        """Yield groups of consecutive indices

        Given a list of integers, yield groups of integers where the value of each in a
        group is adjacent to the previous element's value.

        Parameters
        ----------
        idx : list[int]
            List of indices

        Yields
        ------
        list[list[int]]
            List of lists, where each sub-list contains consecutive indices

        Examples
        -------
        >>> groups = group_consecutive_idx([0, 1, 2, 4, 5, 6, 8, 9])
        >>> [list(g) for g in groups]
        [[0, 1, 2], [4, 5, 6], [8, 9]]
        """
        for k, g in groupby(enumerate(idx), key=lambda x: x[0] - x[1]):
            yield map(itemgetter(1), g)

    def _sizable_unit_pattern(self) -> list[IngredientAmount] | None:
        """Identify sentences which match the pattern where there is a
        quantity-unit pair split by one or more quantity-unit pairs e.g.

        * 1 28 ounce can
        * 2 17.3 oz (484g) package

        Return the correct sets of quantities and units, or an empty list.

        For example, for the sentence: 1 28 ounce can; the correct amounts are:
        [
            IngredientAmount(quantity="1", unit="can", score=0.x...),
            IngredientAmount(quantity="28", unit="ounce", score=0.x...),
        ]

        Returns
        -------
        list[IngredientAmount]
            List of IngredientAmount objects
        """
        # We assume that the pattern will not be longer than the first element
        # defined in patterns.
        patterns = [
            ["QTY", "QTY", "UNIT", "QTY", "UNIT", "QTY", "UNIT", "UNIT"],
            ["QTY", "QTY", "UNIT", "QTY", "UNIT", "UNIT"],
            ["QTY", "QTY", "UNIT", "UNIT"],
        ]

        # List of possible units at end of pattern that constitute a match
        end_units = [
            "bag",
            "block",
            "box",
            "can",
            "envelope",
            "jar",
            "package",
            "packet",
            "piece",
            "tin",
        ]

        # Down select to just QTY and UNIT tokens, scores and labels
        tokens = [
            token
            for token, label in zip(self.tokens, self.labels)
            if label in ["QTY", "UNIT"]
        ]
        scores = [
            score
            for score, label in zip(self.scores, self.labels)
            if label in ["QTY", "UNIT"]
        ]
        labels = [label for label in self.labels if label in ["QTY", "UNIT"]]

        amounts = []
        for pattern in patterns:
            for match in self._match_pattern(tokens, labels, pattern):
                # If the pattern ends with one of end_units, we have found a match for
                # this pattern!
                start, stop = match
                if tokens[stop - 1] in end_units:
                    # Pop matches out of tokens and scores
                    matching_tokens = [tokens.pop(start) for i in range(start, stop)]
                    matching_scores = [scores.pop(start) for i in range(start, stop)]
                    # Also pop matches out of labels, but we don't actually need them
                    _ = [labels.pop(start) for i in range(start, stop)]

                    # The first amount is the first and last items
                    first = IngredientAmount(
                        quantity=matching_tokens.pop(0),
                        unit=matching_tokens.pop(-1),
                        confidence=mean(
                            [matching_scores.pop(0), matching_scores.pop(-1)]
                        ),
                    )
                    amounts.append(first)

                    # And create the IngredientAmount object for the pairs in between
                    for i in range(0, len(matching_tokens), 2):
                        quantity = matching_tokens[i]
                        unit = matching_tokens[i + 1]
                        confidence = mean(matching_scores[i : i + 1])

                        amount = IngredientAmount(
                            quantity=quantity,
                            unit=unit,
                            confidence=confidence,
                            SINGULAR=True,
                        )
                        amounts.append(amount)

        # If we haven't found any matches so far, return None so consumers
        # of the output of this function know there was no match.
        if len(amounts) == 0:
            return None

        # Make units plural if appropriate
        for amount in amounts:
            if amount.quantity != "1" and amount.quantity != "":
                amount.unit = pluralise_units(amount.unit)

        # Mop up any remaining amounts that didn't fit the pattern and have a guess
        # at where to insert them so they are in the order they appear in the sentence.
        if tokens != [] and self.tokens.index(tokens[0]) < match[0]:
            return self._fallback_pattern(tokens, labels, scores) + amounts
        else:
            return amounts + self._fallback_pattern(tokens, labels, scores)

    def _match_pattern(
        self, tokens: list[str], labels: list[str], pattern: list[str]
    ) -> list[tuple[int, int]]:
        """Find a pattern of labels and return the indices of the start and end of match.

        For example, consider the sentence:
        One 15-ounce can diced tomatoes, with liquid

        It has the tokens and labels:
        ['1', '15', 'ounce', 'can', 'diced', 'tomatoes', ',', 'with', 'liquid']
        ['QTY', 'QTY', 'UNIT', 'UNIT', 'COMMENT', 'NAME', 'COMMA', 'COMMENT', 'COMMENT']

        If we search for the pattern:
        ["QTY", "QTY", "UNIT", "UNIT"]

        Then we get:
        [(0, 3)]

        Raises
        ------
        ValueError
            When the length of tokens and labels are not equal.

        Parameters
        ----------
        tokens : list[str]
            List of tokens to return matching pattern from.
        labels : list[str]
            List of labels to find matching pattern in.
        pattern : list[str]
            Pattern to match inside labels.

        Returns
        -------
        list[tuple[int]]
            Tuple of start index end index for matching pattern.
        """

        if len(tokens) != len(labels):
            raise ValueError("The length of tokens and labels must be the same.")

        if len(pattern) > len(tokens):
            # We can never find a match.
            return []

        plen = len(pattern)
        matches = []

        indices = iter(range(len(labels)))
        for i in indices:
            # Short circuit: If the label[i] is not equal to the first element
            # of pattern skip to next iteration
            if labels[i] == pattern[0] and labels[i : i + plen] == pattern:
                matches.append((i, i + plen))
                # Advance iterator to prevent overlapping matches
                consume(indices, plen)

        return matches

    def _fallback_pattern(
        self, tokens: list[str], labels: list[str], scores: list[float]
    ) -> list[IngredientAmount]:
        """Fallback pattern for grouping quantities and units into amounts.
        This is done simply by grouping a QTY with all following UNIT until
        the next QTY.

        Parameters
        ----------
        tokens : list[str]
            Tokens for input sentence
        labels : list[str]
            Labels for input sentence tokens
        scores : list[float]
            Scores for each label

        Returns
        -------
        list[IngredientAmount]
            List of dictionaries for each set of amounts.
            The dictionary contains:
                quantity: str
                unit: list[str]
                score: list[float]
        """
        amounts = []
        for i, (token, label, score) in enumerate(zip(tokens, labels, scores)):
            if label == "QTY":
                # Whenever we come across a new QTY, create new IngredientAmount
                amounts.append(
                    IngredientAmount(quantity=token, unit=[], confidence=[score])
                )

            if label == "UNIT":
                if len(amounts) == 0:
                    # Not come across a QTY yet, so create IngredientAmount
                    # with no quantity
                    amounts.append(
                        IngredientAmount(quantity="", unit=[], confidence=[])
                    )

                if i > 0 and labels[i - 1] == "COMMA":
                    # If previous token was a comma, append to unit
                    # of last IngredientAmount
                    amounts[-1].unit.append(",")

                # Append token and score for unit to last IngredientAmount
                amounts[-1].unit.append(token)
                amounts[-1].confidence.append(score)

            # Check if any flags should be set
            if self._is_approximate(i, tokens, labels):
                amounts[-1].APPROXIMATE = True

            if self._is_singular(i, tokens, labels):
                amounts[-1].SINGULAR = True

            if self._is_singular_and_approximate(i, tokens, labels):
                amounts[-1].APPROXIMATE = True
                amounts[-1].SINGULAR = True

        # Loop through IngredientAmounts to fix unit and confidence
        # Unit needs converting to a string and making plural if appropriate
        # Confidence needs averaging
        for amount in amounts:
            combined_unit = " ".join(amount.unit)
            # Pluralise the units if appropriate
            if amount.quantity != "1" and amount.quantity != "":
                combined_unit = pluralise_units(combined_unit)

            amount.unit = combined_unit
            amount.confidence = round(mean(amount.confidence), 6)

        return amounts

    def _is_approximate(self, i: int, tokens: list[str], labels: list[str]) -> bool:
        """Return True is token at current index is approximate, determined
        by the token label being QTY and the previous token being in a list of
        approximate tokens.

        Parameters
        ----------
        i : int
            Index of current token
        tokens : list[str]
            List of all tokens
        labels : list[str]
            List of all token labels

        Returns
        -------
        bool
            True if current token is approximate
        """
        if i == 0:
            return False

        if labels[i] == "QTY" and tokens[i - 1].lower() in APPROXIMATE_TOKENS:
            return True

        return False

    def _is_singular(self, i: int, tokens: list[str], labels: list[str]) -> bool:
        """Return True is token at current index is singular, determined
        by the token label being UNIT and the next token being in a list of
        singular tokens.

        Parameters
        ----------
        i : int
            Index of current token
        tokens : list[str]
            List of all tokens
        labels : list[str]
            List of all token labels

        Returns
        -------
        bool
            True if current token is singular
        """
        if i == len(tokens) - 1:
            return False

        if labels[i] == "UNIT" and tokens[i + 1].lower() in SINGULAR_TOKENS:
            return True

        return False

    def _is_singular_and_approximate(
        self, i: int, tokens: list[str], labels: list[str]
    ) -> bool:
        """Return True if the current token is approximate and singular, determined
        by the token label being QTY and is preceded by a token in a list of singular
        tokens, then token in a list of approximate tokens.

        e.g. each nearly 3 ...

        Parameters
        ----------
        i : int
            Index of current token
        tokens : list[str]
            List of all tokens
        labels : list[str]
            List of all token labels

        Returns
        -------
        bool
            True if current token is singular
        """
        if i < 2:
            return False

        if (
            labels[i] == "QTY"
            and tokens[i - 1].lower() in APPROXIMATE_TOKENS
            and tokens[i - 2].lower() in SINGULAR_TOKENS
        ):
            return True

        return False

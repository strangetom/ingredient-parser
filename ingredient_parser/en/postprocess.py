#!/usr/bin/env python3

import re
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from itertools import chain, pairwise
from statistics import mean
from typing import Any

from ingredient_parser.en._foundationfoods import match_foundation_foods

from .._common import consume, group_consecutive_idx
from ..dataclasses import (
    CompositeIngredientAmount,
    FoundationFood,
    IngredientAmount,
    IngredientText,
    ParsedIngredient,
)
from ._constants import (
    APPROXIMATE_TOKENS,
    PREPARED_INGREDIENT_TOKENS,
    SINGULAR_TOKENS,
    STOP_WORDS,
    STRING_NUMBERS_REGEXES,
)
from ._regex import FRACTION_TOKEN_PATTERN
from ._utils import (
    combine_quantities_split_by_and,
    ingredient_amount_factory,
    replace_string_range,
)

WORD_CHAR = re.compile(r"\w")


@dataclass
class _PartialIngredientAmount:
    """Dataclass for incrementally building ingredient amount information.

    Attributes
    ----------
    quantity : str
        Parsed ingredient quantity
    unit : list[str]
        Unit or unit tokens of parsed ingredient quantity
    confidence : list[float]
        Average confidence of all tokens or list of confidences for each token of parsed
        ingredient amount, between 0 and 1.
    starting_index : int
        Index of token in sentence that starts this amount
    related_to_previous : bool, optional
        If True, indicates it is related to the previous IngredientAmount object. All
        related objects should have the same APPROXIMATE and SINGULAR flags
    APPROXIMATE : bool, optional
        When True, indicates that the amount is approximate.
        Default is False.
    SINGULAR : bool, optional
        When True, indicates if the amount refers to a singular item of the ingredient.
        Default is False.
    PREPARED_INGREDIENT : bool, optional
        When True, indicates the amount applies to the prepared ingredient.
        When False, indicates the amount applies to the ingredient before preparation.
        Default is False.
    """

    quantity: str
    unit: list[str]
    confidence: list[float]
    starting_index: int
    related_to_previous: bool = False
    APPROXIMATE: bool = False
    SINGULAR: bool = False
    PREPARED_INGREDIENT = False


class PostProcessor:
    """Recipe ingredient sentence PostProcessor class.

    Performs the necessary postprocessing on the sentence tokens and labels and scores
    for the tokens after tagging with the CRF model in order to return a coherent
    structure of parsed information.

    Attributes
    ----------
    sentence : str
        Original ingredient sentence.
    tokens : list[str]
        List of tokens for original ingredient sentence.
    pos_tags : list[str]
        List of part of speech tags for tokens.
    labels : list[str]
        List of labels for tokens.
    scores : list[float]
        Confidence associated with the label for each token.
    separate_names : bool, optional
        If True and the sentence contains multiple alternative ingredients, return an
        IngredientText object for each ingredient name, otherwise return a single
        IngredientText object.
        Default is True.
    discard_isolated_stop_words : bool, optional
        If True, isolated stop words are discarded from the name, preparation or
        comment fields. Default value is True.
    string_units : bool, optional
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Default is False.
    imperial_units : bool, optional
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.
    foundation_foods : bool, optional
        If True, populate the foundation_foods field of ParsedIngredient.
        Default is False, in which case the foundation_foods field is an empty list.
    consumed : list[int]
        List of indices of tokens consumed as part of setting the APPROXIMATE and
        SINGULAR flags. These tokens should not end up in the parsed output.
    """

    def __init__(
        self,
        sentence: str,
        tokens: list[str],
        pos_tags: list[str],
        labels: list[str],
        scores: list[float],
        separate_names: bool = True,
        discard_isolated_stop_words: bool = True,
        string_units: bool = False,
        imperial_units: bool = False,
        foundation_foods: bool = False,
    ):
        self.sentence = sentence
        self.tokens = tokens
        self.pos_tags = pos_tags
        self.labels = labels
        self.scores = scores
        self.separate_names = separate_names
        self.discard_isolated_stop_words = discard_isolated_stop_words
        self.string_units = string_units
        self.imperial_units = imperial_units
        self.foundation_foods = foundation_foods
        self.consumed = []

    def __repr__(self) -> str:
        """__repr__ method.

        Returns
        -------
        str
            String representation of initialised object
        """
        return f'PostProcessor("{self.sentence}")'

    def __str__(self) -> str:
        """__str__ method.

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

    @cached_property
    def parsed(self) -> ParsedIngredient:
        """Return parsed ingredient data.

        Returns
        -------
        ParsedIngredient
            Object containing structured data from sentence.
        """
        amounts = self._postprocess_amounts()

        foundationfoods = []
        if self.separate_names:
            name, foundationfoods = self._postprocess_names()
        else:
            # Replace all labels containing NAME with "NAME"
            name_replaced_labels = []
            for label in self.labels:
                if "NAME" in label:
                    name_replaced_labels.append("NAME")
                else:
                    name_replaced_labels.append(label)
            self.labels = name_replaced_labels

            # Process NAME labels as any other label, but return a list
            if processed_name := self._postprocess("NAME"):
                name = [processed_name]
            else:
                name = []

        size = self._postprocess("SIZE")
        preparation = self._postprocess("PREP")
        comment = self._postprocess("COMMENT")
        purpose = self._postprocess("PURPOSE")

        return ParsedIngredient(
            name=name,
            size=size,
            amount=amounts,
            preparation=preparation,
            comment=comment,
            purpose=purpose,
            foundation_foods=foundationfoods,
            sentence=self.sentence,
        )

    def _postprocess(self, selected_label: str) -> IngredientText | None:
        """Process tokens, labels and scores with selected label into IngredientText.

        Parameters
        ----------
        selected_label : str
            Label of tokens to postprocess

        Returns
        -------
        IngredientText
            Object containing ingredient comment text and confidence
        """
        # Select indices of tokens, labels and scores for selected_label
        # Do not include tokens, labels and scores in self.consumed
        label_idx = [
            i
            for i, label in enumerate(self.labels)
            if label in [selected_label, "PUNC"] and i not in self.consumed
        ]

        # If idx is empty or all the selected idx are PUNC, return None
        if not label_idx or all(self.labels[i] == "PUNC" for i in label_idx):
            return None

        return self._postprocess_indices(label_idx, selected_label)

    def _postprocess_names(self) -> tuple[list[IngredientText], list[FoundationFood]]:
        """Process tokens, labels and scores for the ingredient name(s).

        This function handles multiple ingredient names e.g. "butter or olive oil",
        determined by the labels provided for each token.
        Where multiple alternative ingredients names are identified, each one is
        returned in a separate IngredientText object.

        Returns
        -------
        list[IngredientText], list[FoundationFoods]
        """
        name_idx = [
            i
            for i, label in enumerate(self.labels)
            if ("NAME" in label or label == "PUNC") and i not in self.consumed
        ]

        # If idx is empty or all the selected idx are PUNC, return None
        if not name_idx or all(self.labels[i] == "PUNC" for i in name_idx):
            return [], []

        name_labels = [self.labels[i] for i in name_idx]
        bio_groups = self._group_name_labels(name_labels)
        constructed_names = self._construct_names(bio_groups)

        names = []
        foundation_foods = set()  # Use a set to avoid duplicates
        for group in constructed_names:
            # Convert from name_label indices to token indices
            token_idx = [name_idx[idx] for idx in group]
            ing_text = self._postprocess_indices(token_idx, "NAME")
            if ing_text is not None:
                names.append(ing_text)

                if self.foundation_foods:
                    tokens = [self.tokens[i] for i in token_idx]
                    ff = match_foundation_foods(tokens)
                    if ff:
                        foundation_foods.add(ff)

        return names, list(foundation_foods)

    def _group_name_labels(self, name_labels: list[str]) -> list[list[tuple[int, str]]]:
        """Group name labels according to name label type.

        B_NAME_TOK and all following I_NAME_TOK up to the next label that is not
        I_NAME_TOK or PUNC are grouped.

        All consecutive NAME_MOD labels are grouped.
        All consecutive NAME_VAR labels are grouped.

        A NAME_SEP label starts a new group.

        Parameters
        ----------
        name_labels : list[str]
            List of name labels.

        Returns
        -------
        list[list[tuple[int, str]]]
            List of BIO groups.
            Each group is a list of tuples, where each tuple is the (index, label) of
            the original name_labels list element.
        """
        name_groups = []
        current_group = []
        prev_label = None
        for idx, label in enumerate(name_labels):
            # Start new group on NAME_SEP name label
            if label == "NAME_SEP":
                if current_group:
                    name_groups.append(current_group)
                current_group = []
            # Start new group for new "B_*" name label
            elif label.startswith("B_"):
                if current_group:
                    name_groups.append(current_group)
                current_group = [(idx, label)]
            # Start new group if encountering new NAME_MOD or NAME_VAR, or append to
            # current group if previous label was the same as current label.
            elif label in ["NAME_MOD", "NAME_VAR"]:
                if prev_label == label:
                    current_group.append((idx, label))
                else:
                    if current_group:
                        name_groups.append(current_group)
                    current_group = [(idx, label)]
            # Must be an I_NAME_TOK or PUNC label, so append to current group
            else:
                current_group.append((idx, label))

            prev_label = label

        # Add last group to list if not empty
        if current_group:
            name_groups.append(current_group)

        return name_groups

    def _construct_names(
        self, name_groups: list[list[tuple[int, str]]]
    ) -> list[list[int]]:
        """Construct names from BIO groups.

        All VAR groups are prepended to the next TOK group.
        MOD groups are prepended to all subsequent TOK groups or VAR+TOK groups.

        To make this easier, iterate through the BIO groups from last to first. This
        means we can easily keep track of which TOK group to prepend VAR and MOD
        groups.

        Parameters
        ----------
        name_groups : list[list[tuple[int, str]]]
            List of BIO groups.
            Each group is a list of tuples, where each tuple if the (index, label) of
            the original list element.

        Returns
        -------
        list[list[int]]
            List of name_label indices for each name.
        """
        constructed_names = []

        # Keep track the last TOK group we come across (moving from last to first).
        # Also keep track of whether we have used it by prepending a VAR or MOD
        # group.
        last_encountered_name = None
        last_encountered_name_used = False

        # Iterate from last to first BIO group
        for group in reversed(name_groups):
            current_group_idx, labels = zip(*group)
            current_label = self._get_name_group_label(labels)

            if current_label == "TOK":
                # If we've previously come across a TOK group and haven't used it,
                # then store it.
                if last_encountered_name and not last_encountered_name_used:
                    constructed_names.append(last_encountered_name)

                # Set current group to last_encountered_name group.
                last_encountered_name = current_group_idx
                last_encountered_name_used = False

            elif current_label == "VAR":
                # Prepend this group to last encountered NAME group
                if last_encountered_name:
                    constructed_names.append(current_group_idx + last_encountered_name)
                    last_encountered_name_used = True
                else:
                    # If we are here, then we've come across a VAR group that does not
                    # preceed a TOK group, so the model has made an error in it's
                    # labelling. Add this VAR group anyway.
                    constructed_names.append(current_group_idx)

            elif current_label == "MOD":
                # If we've previously come across a NAME group and haven't used it,
                # then store it.
                if last_encountered_name and not last_encountered_name_used:
                    constructed_names.append(last_encountered_name)
                    last_encountered_name_used = True

                # Prepend this group to all constructed names so far
                constructed_names = [
                    current_group_idx + name for name in constructed_names
                ]

        # If we've iterated through all BIO groups and haven't used
        # last_encountered_name, add it to constructed_names now.
        if last_encountered_name and not last_encountered_name_used:
            constructed_names.append(last_encountered_name)

        # Return reversed list, so names are in the order they appear in sentence.
        return list(reversed(constructed_names))

    def _get_name_group_label(self, labels: tuple[str]) -> str:
        """Get the NAME label type for the labels in a name group.

        One of TOK, VAR, MOD.

        Parameters
        ----------
        labels : tuple[str]
            Tuple of labels for name group elements.

        Returns
        -------
        str
            Group label
        """
        for label in labels:
            if label != "PUNC":
                return label.split("_")[-1]

        return ""

    def _postprocess_indices(
        self, label_idx: list[int], selected_label: str
    ) -> IngredientText | None:
        """Process list of token indices into a single IngredientText object.

        Consecutive tokens are joined together, with non-consecutive groups being joined
        by a comma (unless selected_label is NAME).

        Indices for tokens that would be ungrammatical are removed prior to joining.
        Duplicate tokens that are adjacent are also removed.

        Parameters
        ----------
        label_idx : list[int]
            List of indices of tokens to postprocess into IngredientText
        selected_label : str
            Label of tokens being post processed.

        Returns
        -------
        IngredientText | None
            IngredientText object for selected tokens.
            If the post processing results in all tokens being ignored, return None.
        """
        # Join consecutive tokens together and average their score
        parts = []
        confidence_parts = []
        starting_index = label_idx[-1]
        for group in group_consecutive_idx(label_idx):
            idx = list(group)
            idx = self._remove_invalid_indices(idx)

            if all(self.labels[i] == "PUNC" for i in idx):
                # Skip if the group only contains PUNC
                continue

            # Convert any fractions in intermediate form (i.e. #1$2) into text
            group_tokens = []
            for i in idx:
                if FRACTION_TOKEN_PATTERN.match(self.tokens[i]):
                    text_fraction = (
                        self.tokens[i].replace("#", " ").replace("$", "/").strip()
                    )
                    # If fraction range, remove space that will follow hyphen caused by
                    # replacing # with space.
                    text_fraction = text_fraction.replace("- ", "-")
                    group_tokens.append(text_fraction)
                else:
                    group_tokens.append(self.tokens[i])

            joined = " ".join(group_tokens)
            confidence = mean([self.scores[i] for i in idx])

            if self.discard_isolated_stop_words and joined.lower() in STOP_WORDS:
                # Skip part if it's a stop word
                continue

            self.consumed.extend(idx)
            parts.append(joined)
            confidence_parts.append(confidence)
            starting_index = min(starting_index, idx[0])

        # Find the indices of the joined tokens list where the element
        # is the same as the previous element in the list.
        keep_idx = self._remove_adjacent_duplicates(parts)
        parts = [parts[i] for i in keep_idx]
        confidence_parts = [confidence_parts[i] for i in keep_idx]

        # Join all the parts together into a single string and fix any
        # punctuation weirdness as a result.
        # If the selected_label is NAME, join with a space. For all other labels, join
        # with a comma and a space.
        if selected_label == "NAME":
            text = " ".join(parts)
        else:
            text = ", ".join(parts)
        text = self._fix_punctuation(text)

        if len(parts) == 0:
            return None

        return IngredientText(
            text=text,
            confidence=round(mean(confidence_parts), 6),
            starting_index=starting_index,
        )

    def _postprocess_amounts(
        self,
    ) -> list[IngredientAmount | CompositeIngredientAmount]:
        """Process tokens, labels and scores into IngredientAmount.

        This is done by combining QTY labels with any following UNIT labels,
        up to the next QTY label.

        The confidence is the average confidence of all labels in the IngredientGroup.

        A number of special cases are considered before the default processing:
        1. "sizable unit" pattern
        2. "composite amounts" pattern

        Returns
        -------
        list[IngredientAmount | CompositeIngredientAmount]
            List of IngredientAmount and  CompositeIngredientAmount objects.
        """
        self._convert_string_number_qty()

        funcs = [
            self._sizable_unit_pattern,
            self._composite_amounts_pattern,
            self._fallback_pattern,
        ]

        amounts = []
        for func in funcs:
            idx = self._unconsumed(list(range(len(self.tokens))))
            tokens = self._unconsumed(self.tokens)
            labels = self._unconsumed(self.labels)
            scores = self._unconsumed(self.scores)

            parsed_amounts = func(idx, tokens, labels, scores)
            amounts.extend(parsed_amounts)

        return sorted(amounts, key=lambda x: x.starting_index)

    def _unconsumed(self, list_: list[Any]) -> list[Any]:
        """Return elements from list whose index is not in the list of consumed indices.

        Parameters
        ----------
        list_ : list[Any]
            List of items to remove consumed elements from

        Returns
        -------
        list[Any]
            List of items without consumed elements
        """
        return [el for i, el in enumerate(list_) if i not in self.consumed]

    def _remove_invalid_indices(self, idx: list[int]) -> list[int]:
        """Remove indices of tokens that aren't valid in the group.

        The invalid indices correspond to punctuation that cannot start or end a phrase,
        or brackets that aren't part of a matched pair.

        Parameters
        ----------
        idx : list[int]
            List of indices for group of consecutive tokens
            with same label or PUNC label.

        Returns
        -------
        list[int]
            List of indices with invalid punctuation removed.
        """
        # For groups with more than 1 element, remove invalid leading and trailing
        # punctuation so they don't get incorrectly consumed.
        while len(idx) > 1 and self.tokens[idx[0]] in [
            ")",
            "]",
            "}",
            ",",
            ":",
            ";",
            "-",
            ".",
            "!",
            "?",
            "*",
        ]:
            idx = idx[1:]

        while len(idx) > 1 and self.tokens[idx[-1]] in [
            "[",
            "(",
            "{",
            ",",
            ":",
            ";",
            "-",
        ]:
            idx = idx[:-1]

        # Remove brackets that aren't part of a matching pair
        idx_to_remove = []
        tok_name = None  # Unnecessary, but prevents typing errors
        stack = defaultdict(list)  # Separate stack for each bracket type
        for i, tok in enumerate([self.tokens[i] for i in idx]):
            if tok in ["(", ")"]:
                tok_name = "PAREN"
            elif tok in ["[", "]"]:
                tok_name = "SQAURE"

            if tok in ["(", "["]:
                # Add index to stack when we find an opening parens
                stack[tok_name].append(i)
            elif tok in [")", "]"]:
                if len(stack[tok_name]) == 0:
                    # If the stack is empty, we've found a dangling closing parens
                    idx_to_remove.append(i)
                else:
                    # Remove last added index from stack when we find a closing parens
                    stack[tok_name].pop()

        # Insert anything left in stack into idx_to_remove and remove
        for stack_idx in stack.values():
            idx_to_remove.extend(stack_idx)
        idx = [idx[i] for i, _ in enumerate(idx) if i not in idx_to_remove]

        return idx

    def _fix_punctuation(self, text: str) -> str:
        """Fix some common punctuation errors that result when combining tokens.

        Parameters
        ----------
        text : str
            Text resulting from combining tokens with same label

        Returns
        -------
        str
            Text, with punctuation errors fixed

        Examples
        --------
        >>> p = PostProcessor("", [], [], [])
        >>> p._fix_punctuation(", some words ( inside ),")
        "some words (inside)"
        """
        if text == "":
            return text

        # Correct space following open parens or before close parens
        text = text.replace("( ", "(").replace(" )", ")")

        # Remove space around forward slash
        text = text.replace(" / ", "/")

        # Correct space preceding various punctuation
        for punc in [",", ":", ";", ".", "!", "?", "*", "'"]:
            text = text.replace(f" {punc}", punc)

        return text.strip()

    def _remove_adjacent_duplicates(self, parts: list[str]) -> list[int]:
        """Find indices of adjacent duplicate strings.

        Parameters
        ----------
        parts : list[str]
            List of strings with single label.

        Returns
        -------
        list[int]
            Indices of elements in parts to keep.

        Examples
        --------
        >>> p = PostProcessor("", [], [], [])
        >>> p._remove_isolated_punctuation_and_duplicate_indices(
            ["word", "word", "another"],
        )
        [1, 2]
        """

        idx_to_keep = []
        for i, (first, second) in enumerate(pairwise([*parts, ""])):
            if first != second:
                idx_to_keep.append(i)

        return idx_to_keep

    def _replace_string_numbers(self, text: str) -> str:
        """Replace string numbers (e.g. one, two) with numeric values (e.g. 1, 2).

        Parameters
        ----------
        text : str
            Ingredient sentence

        Returns
        -------
        str
            Ingredient sentence with string numbers replace with numeric values

        Examples
        --------
        >>> p = PreProcessor("")
        >>> p._replace_string_numbers("three large onions")
        "3 large onions"

        >>> p = PreProcessor("")
        >>> p._replace_string_numbers("twelve bonbons")
        "12 bonbons"
        """
        # STRING_NUMBER_REGEXES is a dict where the values are a tuple of the compiled
        # regular expression for matching a string number e.g. 'one', 'two' and the
        # substitution numerical value for that string number.
        for regex, substitution in STRING_NUMBERS_REGEXES.values():
            text = regex.sub(rf"{substitution}", text)

        return text

    def _convert_string_number_qty(self) -> None:
        """Convert QTY tokens that are string numbers to numeric values

        This function modifies the tokens, labels and scores lists in place to replace
        any string numbers with QTY label with their numeric value.

        This function also collapses any quantities split by 'and' into a single
        number e.g.
        one and one-half -> 1 and 1/2 -> 1.5

        This function also collapses any string ranges into a single range e.g.
        one or two -> 1 or 2 -> 1-2
        """
        for i, (token, label) in enumerate(zip(self.tokens, self.labels)):
            if label == "QTY":
                self.tokens[i] = self._replace_string_numbers(token)

        QTY_idx = [i for i, label in enumerate(self.labels) if label == "QTY"]

        # Find any cases where a group of consecutive QTY tokens can be collapsed into
        # a single token. Modify the first token and score in the group and mark all
        # others in group for deletion.
        idx_to_remove = []
        for idx_group in group_consecutive_idx(QTY_idx):
            idx_group = list(idx_group)
            if len(idx_group) == 1:
                continue

            fragment = " ".join([self.tokens[i] for i in idx_group])

            replacement = combine_quantities_split_by_and(fragment)
            if replacement != fragment:
                mod_idx = idx_group[0]  # Index to replace with replacement
                self.scores[mod_idx] = mean([self.scores[i] for i in idx_group])
                self.tokens[mod_idx] = replacement

                idx_to_remove.extend(idx_group[1:])
                continue

            replacement = replace_string_range(fragment)
            if replacement != fragment:
                mod_idx = idx_group[0]  # Index to replace with replacement
                self.scores[mod_idx] = mean([self.scores[i] for i in idx_group])
                self.tokens[mod_idx] = replacement

                idx_to_remove.extend(idx_group[1:])
                continue

        if idx_to_remove:
            self.tokens = [
                self.tokens[i]
                for i, _ in enumerate(self.tokens)
                if i not in idx_to_remove
            ]
            self.labels = [
                self.labels[i]
                for i, _ in enumerate(self.labels)
                if i not in idx_to_remove
            ]
            self.scores = [
                self.scores[i]
                for i, _ in enumerate(self.scores)
                if i not in idx_to_remove
            ]

    def _sizable_unit_pattern(
        self, idx: list[int], tokens: list[str], labels: list[str], scores: list[float]
    ) -> list[IngredientAmount]:
        """Identify sentences which match the sizable unit pattern.

        This pattern is where there is a quantity-unit pair split by one or more
        quantity-unit pairs e.g.

        * 1 28 ounce can
        * 2 17.3 oz (484g) package

        Return the correct sets of quantities and units, or an empty list.

        For example, for the sentence: 1 28 ounce can; the correct amounts are:
        [
            IngredientAmount(quantity=Fraction(1, 1), unit="can", score=0.x...),
            IngredientAmount(quantity=Fraction(28, 1), unit="ounce", score=0.x...),
        ]

        Parameters
        ----------
        idx : list[int]
            List of indices of the tokens/labels/scores in the full tokenized sentence
        tokens : list[str]
            Tokens for input sentence
        labels : list[str]
            Labels for input sentence tokens
        scores : list[float]
            Scores for each label

        Returns
        -------
        list[IngredientAmount]
            List of IngredientAmount objects
        """
        # We assume that the pattern will not be longer than the longest list
        # defined here.
        patterns = [
            ["QTY", "QTY", "UNIT", "QTY", "UNIT", "QTY", "UNIT", "UNIT"],
            ["QTY", "QTY", "UNIT", "QTY", "UNIT", "UNIT"],
            ["QTY", "QTY", "UNIT", "UNIT"],
        ]

        # List of possible units at end of pattern that constitute a match
        end_units = [
            "bag",
            "block",
            "bottle",
            "box",
            "bucket",
            "can",
            "container",
            "envelope",
            "jar",
            "loaf",
            "package",
            "packet",
            "piece",
            "sachet",
            "slice",
            "tin",
        ]

        amounts = []
        for pattern in patterns:
            for match in self._match_pattern(labels, pattern, ignore_other_labels=True):
                # If the pattern ends with one of end_units, we have found a match for
                # this pattern!
                if tokens[match[-1]] in end_units:
                    # Get tokens and scores that are part of match
                    matching_tokens = [tokens[i] for i in match]
                    matching_scores = [scores[i] for i in match]

                    # Keep track of indices of matching elements so we don't use them
                    # again elsewhere
                    self.consumed.extend([idx[i] for i in match])

                    # The first amount is made up of the first and last items
                    # Note that this cannot be singular, but may be approximate
                    quantity = matching_tokens.pop(0)
                    unit = matching_tokens.pop(-1)
                    text = " ".join((quantity, unit)).strip()

                    first = ingredient_amount_factory(
                        quantity=quantity,
                        unit=unit,
                        text=text,
                        confidence=mean(
                            [matching_scores.pop(0), matching_scores.pop(-1)]
                        ),
                        starting_index=idx[match[0]],
                        APPROXIMATE=self._is_approximate(match[0], tokens, labels, idx),
                        string_units=self.string_units,
                        imperial_units=self.imperial_units,
                    )
                    amounts.append(first)
                    # Pop the first and last items from the list of matching indices
                    _ = match.pop(0)
                    _ = match.pop(-1)

                    # Now create the IngredientAmount objects for the pairs in between
                    # the first and last items
                    for i in range(0, len(matching_tokens), 2):
                        quantity = matching_tokens[i]
                        unit = matching_tokens[i + 1]
                        text = " ".join((quantity, unit)).strip()
                        confidence = mean(matching_scores[i : i + 1])

                        # If the first amount (e.g. 1 can) is approximate, so are all
                        # the pairs in between
                        amount = ingredient_amount_factory(
                            quantity=quantity,
                            unit=unit,
                            text=text,
                            confidence=confidence,
                            starting_index=idx[match[i]],
                            SINGULAR=True,
                            APPROXIMATE=first.APPROXIMATE,
                            string_units=self.string_units,
                            imperial_units=self.imperial_units,
                        )
                        amounts.append(amount)

        return amounts

    def _composite_amounts_pattern(
        self, idx: list[int], tokens: list[str], labels: list[str], scores: list[float]
    ) -> list[CompositeIngredientAmount]:
        """Identify sentences which match the pattern where there are composite amounts.

        This pattern is where there are adjacent amounts that need to be considered
        together, e.g.

        * 1 lb 2 oz
        * 1 pint 2 fl oz
        * 2 cups plus 1 tablespoon

        Return a composite amount object made from the adjacent amounts.

        For example, for the sentence: 1 lb 2 oz ...; the composite amount is:
        CompositeAmount(
            amounts=[
                IngredientAmount(quantity=Fraction(1, 1), unit="lb", score=0.x...),
                IngredientAmount(quantity=Fraction(2, 1), unit="oz", score=0.x...),
            ],
            join=""
        )

        Parameters
        ----------
        idx : list[int]
            List of indices of the tokens/labels/scores in the full tokenized sentence
        tokens : list[str]
            Tokens for input sentence
        labels : list[str]
            Labels for input sentence tokens
        scores : list[float]
            Scores for each label

        Returns
        -------
        list[CompositeIngredientAmount]
            List of IngredientAmount objects
        """
        # Define patterns for composite amounts based on a sequence of labels.
        # Also set the indices of the pattern sequence where the first and
        # second amounts start, set the string used to join the two amounts
        # together in text, and set whether the amounts combine subtractively or not.
        patterns = {
            "ptfloz": {
                "pattern": ["QTY", "UNIT", "QTY", "UNIT", "UNIT"],
                "conjunction": None,
                "conj_index": None,
                "start1": 0,
                "start2": 2,
                "join": "",
                "subtractive": False,
            },
            "lboz": {
                "pattern": ["QTY", "UNIT", "QTY", "UNIT"],
                "conjunction": None,
                "conj_index": None,
                "start1": 0,
                "start2": 2,
                "join": "",
                "subtractive": False,
            },
            "plus": {
                "pattern": ["QTY", "UNIT", "COMMENT", "QTY", "UNIT"],
                "conjunction": "plus",
                "conj_index": 2,
                "start1": 0,
                "start2": 3,
                "join": " plus ",
                "subtractive": False,
            },
            "plus_punc": {
                "pattern": ["QTY", "UNIT", "PUNC", "QTY", "UNIT"],
                "conjunction": "+",
                "conj_index": 2,
                "start1": 0,
                "start2": 3,
                "join": " + ",
                "subtractive": False,
            },
            "plus_punc_comment": {
                "pattern": ["QTY", "UNIT", "PUNC", "COMMENT", "QTY", "UNIT"],
                "conjunction": "plus",
                "conj_index": 3,
                "start1": 0,
                "start2": 4,
                "join": " plus ",
                "subtractive": False,
            },
            "and": {
                "pattern": ["QTY", "UNIT", "COMMENT", "QTY", "UNIT"],
                "conjunction": "and",
                "conj_index": 2,
                "start1": 0,
                "start2": 3,
                "join": " and ",
                "subtractive": False,
            },
            "minus": {
                "pattern": ["QTY", "UNIT", "COMMENT", "QTY", "UNIT"],
                "conjunction": "minus",
                "conj_index": 2,
                "start1": 0,
                "start2": 3,
                "join": " minus ",
                "subtractive": True,
            },
            "less": {
                "pattern": ["QTY", "UNIT", "COMMENT", "QTY", "UNIT"],
                "conjunction": "less",
                "conj_index": 2,
                "start1": 0,
                "start2": 3,
                "join": " minus ",
                "subtractive": True,
            },
        }

        # List of possible units for first and second amount matched for
        # pltfloz and lboz patterns.
        valid_first_units = {"lb", "pound", "pt", "pint"}
        valid_last_units = {"oz", "ounce"}

        composite_amounts = []
        for pattern_name, pattern_info in patterns.items():
            pattern = pattern_info["pattern"]
            start1 = pattern_info["start1"]
            start2 = pattern_info["start2"]
            join = pattern_info["join"]
            conj_index = pattern_info["conj_index"]
            subtractive = pattern_info["subtractive"]

            for match in self._match_pattern(
                labels, pattern, ignore_other_labels=False
            ):
                # Check if match fits with "ptfloz" or "lboz" pattern constraints
                if pattern_name in ["ptfloz", "lboz"]:
                    first_unit = tokens[match[start1 + 1]]
                    last_unit = tokens[match[-1]]
                    if (
                        first_unit not in valid_first_units
                        or last_unit not in valid_last_units
                    ):
                        # Units of match do not align with expectations for
                        # ptfloz or lboz patterns, so skip
                        continue

                # For other patterns, check if token at the conj_index in match matches
                # conjunction and skip if not.
                elif tokens[match[conj_index]].lower() != pattern_info["conjunction"]:
                    continue

                # First amount
                quantity_1 = tokens[match[start1]]
                unit_1 = tokens[match[start1 + 1]]
                score_1 = mean(scores[i] for i in match[start1 : start1 + 2])
                text_1 = " ".join((quantity_1, unit_1)).strip()

                first_amount = ingredient_amount_factory(
                    quantity=quantity_1,
                    unit=unit_1,
                    text=text_1,
                    confidence=score_1,
                    starting_index=idx[match[start1]],
                    string_units=self.string_units,
                    imperial_units=self.imperial_units,
                )

                # Second amount
                quantity_2 = tokens[match[start2]]
                unit_2 = " ".join([tokens[i] for i in match[start2 + 1 :]])
                score_2 = mean(scores[i] for i in match[start2:])
                text_2 = " ".join((quantity_2, unit_2)).strip()

                second_amount = ingredient_amount_factory(
                    quantity=quantity_2,
                    unit=unit_2,
                    text=text_2,
                    confidence=score_2,
                    starting_index=idx[match[start2]],
                    string_units=self.string_units,
                    imperial_units=self.imperial_units,
                )

                composite_amounts.append(
                    CompositeIngredientAmount(
                        amounts=[first_amount, second_amount],
                        join=join,
                        subtractive=subtractive,
                    )
                )

                # Keep track of indices of matching elements so we don't use them
                # again elsewhere
                self.consumed.extend([idx[i] for i in match])

        return composite_amounts

    def _match_pattern(
        self, labels: list[str], pattern: list[str], ignore_other_labels: bool = True
    ) -> list[list[int]]:
        """Find a pattern of labels, returning the indices of the matching labels.

        For example, consider the sentence:
        One 15-ounce can diced tomatoes, with liquid

        It has the tokens and labels:
        ['1', '15', 'ounce', 'can', 'diced', 'tomatoes', ',', 'with', 'liquid']
        ['QTY', 'QTY', 'UNIT', 'UNIT', 'COMMENT', 'NAME', 'COMMA', 'COMMENT', 'COMMENT']

        If we search for the pattern:
        ["QTY", "QTY", "UNIT", "UNIT"]

        Then we get:
        [[0, 1, 2, 3]]

        Parameters
        ----------
        labels : list[str]
            List of labels to find pattern within.
        pattern : list[str]
            Pattern to match inside labels.
        ignore_other_labels : bool
            If True, the pattern matching will ignore any labels not found in pattern
            meaning the indices of the match may not be consecutive.
            If False, the pattern must be found without any interruptions in the
            labels list.

        Returns
        -------
        list[list[int]]
            List of label index lists that match the pattern.
        """
        plen = len(pattern)
        plabels = set(pattern)

        if ignore_other_labels:
            # Select just the labels and indices of labels that are in the pattern.
            lbls = [label for label in labels if label in plabels]
            idx = [i for i, label in enumerate(labels) if label in plabels]
        else:
            # Consider all labels
            lbls = labels
            idx = [i for i, _ in enumerate(labels)]

        if len(pattern) > len(lbls):
            # We can never find a match.
            return []

        matches = []
        indices = iter(range(len(lbls)))
        for i in indices:
            # Short circuit: If lbls[i] is not equal to the first element
            # of pattern, skip to next iteration
            if lbls[i] == pattern[0] and lbls[i : i + plen] == pattern:
                matches.append(idx[i : i + plen])
                # Advance iterator to prevent overlapping matches
                consume(indices, plen - 1)

        return matches

    def _fallback_pattern(
        self,
        idx: list[int],
        tokens: list[str],
        labels: list[str],
        scores: list[float],
    ) -> list[IngredientAmount]:
        """Fallback pattern for grouping quantities and units into amounts.

        This is done simply by grouping a QTY with all following UNIT until
        the next QTY.

        A special case is the for when the token "dozen" is labelled as QTY and
        it follows a QTY. In this case, the quantity of previous amount is
        modified to include "dozen".

        Parameters
        ----------
        idx : list[int]
            List of indices of the tokens/labels/scores in the full tokenized sentence
        tokens : list[str]
            Tokens for input sentence
        labels : list[str]
            Labels for input sentence tokens
        scores : list[float]
            Scores for each label

        Returns
        -------
        list[IngredientAmount]
            List of IngredientAmount objects
        """
        amounts = []

        # If a new amount starts with the token after a (, / or [ then it we assume it
        # is related to the previous amount
        # We use idx+1 here so we can check the index in the iteration a new amount is
        # created and avoid needing to check things like i >= 0
        related_idx = [
            idx + 1 for idx, tok in enumerate(tokens) if tok in ["(", "/", "["]
        ]

        for i, (token, label, score) in enumerate(zip(tokens, labels, scores)):
            if label == "QTY":
                # Whenever we come across a new QTY, create new IngredientAmount,
                # unless the token is "dozen" and the previous label was QTY, in which
                # case we modify the quantity of the previous amount.
                if token == "dozen" and labels[i - 1] == "QTY":
                    amounts[-1].quantity = amounts[-1].quantity + " dozen"
                    amounts[-1].confidence.append(score)
                else:
                    amounts.append(
                        _PartialIngredientAmount(
                            quantity=token,
                            unit=[],
                            confidence=[score],
                            starting_index=idx[i],
                            related_to_previous=i in related_idx,
                        )
                    )

            if label == "UNIT":
                if amounts == []:
                    # Not come across a QTY yet, so create IngredientAmount
                    # with no quantity
                    amounts.append(
                        _PartialIngredientAmount(
                            quantity="",
                            unit=[],
                            confidence=[score],
                            starting_index=idx[i],
                        )
                    )

                # Append token and score for unit to last IngredientAmount
                amounts[-1].unit.append(token)
                amounts[-1].confidence.append(score)

            # Check if any flags should be set
            if self._is_approximate(i, tokens, labels, idx):
                amounts[-1].APPROXIMATE = True

            if self._is_singular(i, tokens, labels, idx):
                amounts[-1].SINGULAR = True

            if self._is_singular_and_approximate(i, tokens, labels, idx):
                amounts[-1].APPROXIMATE = True
                amounts[-1].SINGULAR = True

            if self._is_prepared(i, tokens, labels, idx):
                amounts[-1].PREPARED_INGREDIENT = True

        # Set APPROXIMATE, SINGULAR and PREPARED_INGREDIENT flags to be the same for all
        # related amounts.
        amounts = self._distribute_related_flags(amounts)

        # Loop through amounts list to fix unit and confidence
        # Unit needs converting to a string
        # Confidence needs averaging
        # Then convert to IngredientAmount object
        processed_amounts = []
        for amount in amounts:
            unit = " ".join(amount.unit)
            text = " ".join((amount.quantity, unit)).strip()

            # Convert to an IngredientAmount object for returning
            processed_amounts.append(
                ingredient_amount_factory(
                    quantity=amount.quantity,
                    unit=unit,
                    text=text,
                    confidence=mean(amount.confidence),
                    starting_index=amount.starting_index,
                    APPROXIMATE=amount.APPROXIMATE,
                    SINGULAR=amount.SINGULAR,
                    PREPARED_INGREDIENT=amount.PREPARED_INGREDIENT,
                    string_units=self.string_units,
                    imperial_units=self.imperial_units,
                )
            )

        return processed_amounts

    def _is_approximate(
        self, i: int, tokens: list[str], labels: list[str], idx: list[int]
    ) -> bool:
        """Return True is token at current index is approximate.

        This is determined by the token label being QTY and the previous token being in
        a list of approximate tokens.

        If returning True, also add index of i - 1 token to self.consumed list.

        Parameters
        ----------
        i : int
            Index of current token
        tokens : list[str]
            List of all tokens
        labels : list[str]
            List of all token labels
        idx : list[int]
            List of indices of the tokens/labels/scores in the full tokenized sentence

        Returns
        -------
        bool
            True if current token is approximate

        Examples
        --------
        >>> p = PostProcessor("", [], [], [])
        >>> p._is_approximate(
            1,
            ["about", "3", "cups"],
            ["COMMENT", "QTY", "UNIT"],
            [0, 1, 2]
        )
        True

        >>> p = PostProcessor("", [], [], [])
        >>> p._is_approximate(
            1,
            ["approx.", "250", "g"],
            ["COMMENT", "QTY", "UNIT"],
            [0, 1, 2]
        )
        True
        """
        if i == 0:
            return False

        if labels[i] == "QTY" and tokens[i - 1].lower() in APPROXIMATE_TOKENS:
            # Mark i - 1 element as consumed
            self.consumed.append(idx[i - 1])
            return True
        elif (
            labels[i] == "QTY"
            and tokens[i - 1] == "."
            and tokens[i - 2].lower() in APPROXIMATE_TOKENS
        ):
            # Special case for "approx."
            # Mark i - 1 and i - 2 elements as consumed
            self.consumed.append(idx[i - 1])
            self.consumed.append(idx[i - 2])
            return True

        return False

    def _is_singular(
        self, i: int, tokens: list[str], labels: list[str], idx: list[int]
    ) -> bool:
        """Return True is token at current index is singular.

        This is determined by the token label being UNIT and the next token being in
        a list of singular tokens.

        If returning True, also add index of i + 1 token to self.consumed list.

        Parameters
        ----------
        i : int
            Index of current token
        tokens : list[str]
            List of all tokens
        labels : list[str]
            List of all token labels
        idx : list[int]
            List of indices of the tokens/labels/scores in the full tokenized sentence

        Returns
        -------
        bool
            True if current token is singular

        Examples
        --------
        >>> p = PostProcessor("", [], [], [])
        >>> p._is_singular(
            1,
            ["3", "oz", "each"],
            ["QTY", "UNIT", "COMMENT"],
            [0, 1, 2]
        )
        True
        """
        if i == len(tokens) - 1:
            return False

        if labels[i] == "UNIT" and tokens[i + 1].lower() in SINGULAR_TOKENS:
            # Mark i - 1 element as consumed
            self.consumed.append(idx[i + 1])
            return True

        if i == len(tokens) - 2:
            return False

        # Case where the amount is in brackets
        if (
            labels[i] == "UNIT"
            and tokens[i + 1] in [")", "]"]
            and tokens[i + 2].lower() in SINGULAR_TOKENS
        ):
            # Mark i - 1 element as consumed
            self.consumed.append(idx[i + 2])
            return True

        return False

    def _is_singular_and_approximate(
        self, i: int, tokens: list[str], labels: list[str], idx: list[int]
    ) -> bool:
        """Return True if the current token is approximate and singular.

        This is determined by the token label being QTY and is preceded by a token in
        a list of singular tokens, then token in a list of approximate tokens.

        If returning True, also add index of i - 1 and i - 2 tokens to
        self.consumed list.

        e.g. each nearly 3 ...

        Parameters
        ----------
        i : int
            Index of current token
        tokens : list[str]
            List of all tokens
        labels : list[str]
            List of all token labels
        idx : list[int]
            List of indices of the tokens/labels/scores in the full tokenized sentence

        Returns
        -------
        bool
            True if current token is singular

        Examples
        --------
        >>> p = PostProcessor("", [], [], [])
        >>> p._is_approximate(
            1,
            ["each", nearly", "3", "oz"],
            ["COMMENT", "COMMENT", "QTY", "UNIT"],
            [0, 1, 2, 3]
        )
        True
        """
        if i < 2:
            return False

        if (
            labels[i] == "QTY"
            and tokens[i - 1].lower() in APPROXIMATE_TOKENS
            and tokens[i - 2].lower() in SINGULAR_TOKENS
        ):
            # Mark i - 1 and i - 2 elements as consumed
            self.consumed.append(idx[i - 1])
            self.consumed.append(idx[i - 2])
            return True

        return False

    def _is_prepared(
        self, i: int, tokens: list[str], labels: list[str], idx: list[int]
    ) -> bool:
        """Return True is token at current index refers to the prepared ingredient.

        This is determined by the token label being QTY and the previous tokens being in
        a list of prepared tokens.
        If the QTY is preceded by a token in APPROXIMATE_TOKENS, then the tokens prior
        to that are checked for matches against the prepared tokens list.

        If returning True, also add index of tokens from prepared token list to
        self.consumed list.

        Parameters
        ----------
        i : int
            Index of current token
        tokens : list[str]
            List of all tokens
        labels : list[str]
            List of all token labels
        idx : list[int]
            List of indices of the tokens/labels/scores in the full tokenized sentence

        Returns
        -------
        bool
            True if current token is approximate

        Examples
        --------
        >>> p = PostProcessor("", [], [], [])
        >>> p._is_approximate(
            2,
            ["to", "yield", "2", "cups"],
            ["COMMENT", "COMMENT", "QTY", "UNIT"],
            [0, 1, 2, 3]
        )
        True

        >>> p = PostProcessor("", [], [], [])
        >>> p._is_approximate(
            2,
            ["to", "make", "about", "250", "g"],
            ["COMMENT", "COMMENT, "COMMENT", "QTY", "UNIT"],
            [0, 1, 2, 3, 4]
        )
        True
        """
        # All PREPARED_INGREDIENT_TOKENS have length 2, so cannot be prepared if i < 2.
        if i < 2:
            return False

        if labels[i] != "QTY":
            return False

        for pattern in PREPARED_INGREDIENT_TOKENS:
            if [t.lower() for t in tokens[i - 2 : i]] == pattern:
                # Mark i - 1 and i - 2 elements as consumed
                self.consumed.append(idx[i - 1])
                self.consumed.append(idx[i - 2])
                return True
            elif (
                i > 2
                and tokens[i - 1] in APPROXIMATE_TOKENS
                and [t.lower() for t in tokens[i - 3 : i - 1]] == pattern
            ):
                # Mark i - 2 and i - 3 elements as consumed
                self.consumed.append(idx[i - 2])
                self.consumed.append(idx[i - 3])
                return True

        return False

    def _distribute_related_flags(
        self, amounts: list[_PartialIngredientAmount]
    ) -> list[_PartialIngredientAmount]:
        """Distribute all set flags to related amounts.

        Parameters
        ----------
        amounts : list[_PartialIngredientAmount]
            List of amounts

        Returns
        -------
        list[_PartialIngredientAmount]
            List of amount with all related amounts having the same flags
        """
        # Group amounts into related groups
        grouped = []
        for amount in amounts:
            if grouped and amount.related_to_previous:
                grouped[-1].append(amount)
            else:
                grouped.append([amount])

        # Set flags for all amounts in group if any amount has flag set
        for group in grouped:
            if any(am.APPROXIMATE for am in group):
                for am in group:
                    am.APPROXIMATE = True

            if any(am.SINGULAR for am in group):
                for am in group:
                    am.SINGULAR = True

            if any(am.PREPARED_INGREDIENT for am in group):
                for am in group:
                    am.PREPARED_INGREDIENT = True

        # Flatten list for return
        return list(chain.from_iterable(grouped))

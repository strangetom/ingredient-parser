#!/usr/bin/env python3

import logging
from dataclasses import dataclass
from typing import ClassVar, Literal

from ingredient_parser.dataclasses import Token

logger = logging.getLogger("ingredient-parser.ambiguity")

Feature = Literal["is_unit", "is_size"]


@dataclass
class FeatureDisambiguator:
    """Dataclass defining the data needed to disambiguate a feature for a token.

    Attributes
    ----------
    context_window : tuple[int, int]
        Number of tokens before and after the feature-ambiguous token to check for
        disambiguating tokens.
    disambiguating_tokens : frozenset[str]
        List of tokens that disambiguate the feature for the token.
    feature_applicability : bool
        If True, finding a disambiguating token within the context window means the
        feature applies to the token.
        If False, finding a disambiguating token within the context window means the
        feature does not apply to the token.
    plural : bool | None, optional.
        True = plural only.
        False = singular only.
        None = singular and plural.
        Default is None.
    same_segment_only : bool, optional
        If True, restrict context window to the same segment as the ambiguous token.
        Default is True.
    unambiguous_after_quantity : bool, optional
        If True, the feature is not considered ambiguous if the potentially ambiguous
        token follows a number.
        Default is False.
    """

    context_window: tuple[int, int]
    disambiguating_tokens: frozenset[str]
    feature_applicability: bool
    plural: bool | None = None
    same_segment_only: bool = True
    unambiguous_after_quantity: bool = False


def _create_rule(
    window: tuple[int, int], tokens: list[str], feature_applicability: bool, **kwargs
) -> FeatureDisambiguator:
    """Shortcut function to create a FeatureDisambiguator object."""
    return FeatureDisambiguator(
        window, frozenset(tokens), feature_applicability, **kwargs
    )


class Disambiguator:
    """Class to resolve ambiguity in tokens with respect to specific features.

    Some tokens are ambiguous with respect to certain features because the word has
    multiple homonyms. For example, "clove" is a unit in the context of garlic, or a
    spice without that context.

    This class identifies tokens that can be ambiguous for a given feature, and
    determines if the feature should apply to the token given the context of the
    surrounding tokens.

    Because units are made singular as part of the preprocessing, we have to account for
    whether the token is plural or not, since sometimes only the singular or plural
    version is an ambiguous homonym.

    Attributes
    ----------
    AMBIGUOUS_TOKENS : ClassVar[dict[tuple[str, Feature], FeatureDisambiguator]]
        Dict defining ambiguous tokens.
        The keys of the dict are a tuple of (token, feature).
    AMBIGUOUS_WORDS : ClassVar[frozenset[str]]
        Set of words that are considered ambiguous.
    """

    AMBIGUOUS_TOKENS: ClassVar[dict[tuple[str, Feature], FeatureDisambiguator]] = {
        # Clove is a spice.
        # If garlic appears anywhere in the sentence, assume clove is a unit, hence the
        # big context window and same_segment_only=False.
        ("clove", "is_unit"): _create_rule(
            (20, 20), ["garlic"], True, same_segment_only=False
        ),
        # Gelatine comes in leaves, so in this context is always a unit.
        ("leaf", "is_unit"): _create_rule((2, 2), ["gelatine"], True),
        # Slab bacon, singular only.
        ("slab", "is_unit"): _create_rule((0, 1), ["bacon"], False, plural=False),
        # Celery can be specified in units of ribs.
        # Other uses of ribs usually refer to the cut of meat.
        ("rib", "is_unit"): _create_rule((2, 2), ["celery"], True),
        # gram flour aka chickpea flour
        # This is unambiguous after a number e.g. 100 gram flour.
        ("gram", "is_unit"): _create_rule(
            (0, 1), ["flour"], False, plural=False, unambiguous_after_quantity=True
        ),
        # glass noodles are a type of noodle, singular only.
        ("glass", "is_unit"): _create_rule((0, 1), ["noodles"], False, plural=False),
        # stem ginger, singular only.
        ("stem", "is_unit"): _create_rule((0, 1), ["ginger"], False, plural=False),
        # pound cake, singular only.
        # This is unambiguous after a number e.g. 1 pound cake flour
        ("pound", "is_unit"): _create_rule(
            (0, 1), ["cake"], False, plural=False, unambiguous_after_quantity=True
        ),
        # Medium is usually a size, unless in the context of the specified tokens.
        # Singular only.
        ("medium", "is_size"): _create_rule(
            (0, 3),
            ["firm", "ripe", "dry", "roast", "curry", "strength", "heat", "rare"],
            False,
            plural=False,
        ),
    }

    # Fast reject set: most tokens are not ambiguous for any feature.
    AMBIGUOUS_WORDS: ClassVar[frozenset[str]] = frozenset(
        word for word, _ in AMBIGUOUS_TOKENS
    )

    def __init__(self, tokens: list[Token], singularised_indices: list[int]):
        """Initialise

        Parameters
        ----------
        tokens : list[Token]
            List of Tokens for current sentence.
        singularised_indices : list[int]
            List of indices of Tokens in current sentence that have been singularised.
        """
        self.tokens = tokens
        self.plural_tokens = singularised_indices
        self._lower = [t.text.lower() for t in tokens]

    def __repr__(self) -> str:
        return (
            f"Disambiguator(tokens={self._lower}, plural_tokens={self.plural_tokens})"
        )

    def _get_rule(self, index: int, feature: Feature) -> FeatureDisambiguator | None:
        """Return FeatureDisambiguator rule for token at given index with respect to
        given feature.

        If no rule applies, return None.

        Parameters
        ----------
        index : int
            Index of token to determine if feature is ambiguous.
        feature : Feature
            The feature under consideration.
        """
        word = self._lower[index]
        if word not in self.AMBIGUOUS_WORDS:
            # Not an ambiguous token.
            return None

        rule = self.AMBIGUOUS_TOKENS.get((word, feature))
        if rule is None:
            # No rule for this combination of word and feature, therefore not ambiguous.
            return None

        if rule.plural is not None and rule.plural != (index in self.plural_tokens):
            # The rule has a plurality constraint and it is different to the plurality
            # of the token at the given index, therefore not ambiguous.
            return None

        return rule

    def is_ambiguous(self, index: int, feature: Feature) -> bool:
        """Return True if the token is ambiguous with respect to the given feature.

        Parameters
        ----------
        index : int
            Index of token to determine if feature is ambiguous.
        feature : Feature
            The feature under consideration.

        Returns
        -------
        bool
            True if token is ambiguous, else False.
        """
        return self._get_rule(index, feature) is not None

    def does_feature_apply(self, index: int, feature: Feature) -> bool:
        """Return True if feature applies to token at given index.

        Parameters
        ----------
        index : int
            Index of token to determine feature applicability of.
        feature : Feature
            Feature to determine applicability of.
        """
        word = self._lower[index]
        rule = self._get_rule(index, feature)
        if rule is None:
            logger.debug("%s is not ambiguous for %s", word, feature)
            # By default, assume feature applies is there is no rule.
            return True

        return self._apply_rule(index, rule)

    def _apply_rule(self, index: int, rule: FeatureDisambiguator) -> bool:
        """Apply rule to token at given index.

        Parameters
        ----------
        index : int
            Token index to apply rule to.
        rule : FeatureDisambiguator
            Disambiguating rule.

        Returns
        -------
        bool
            True, if feature apples to token at index, else False.
        """
        if (
            rule.unambiguous_after_quantity
            and index > 0
            and self.tokens[index - 1].feat_text == "!num"
        ):
            # If the rule states that the feature is unambiguous if the token is
            # directly after a number token, then return True because the feature
            # applies at this index.
            return True

        before, after = rule.context_window
        segment = self.tokens[index].segment
        # Find the limits of the context window to consider.
        context_min = max(index - before, 0)
        context_max = min(index + after + 1, len(self.tokens))
        for context_index in range(context_min, context_max):
            if context_index == index:
                # No need check the token we're interested in.
                continue

            if rule.same_segment_only and self.tokens[context_index].segment != segment:
                # Context token is in a different segment and the rule requires that
                # we only consider tokens in the same segment.
                continue

            if self._lower[context_index] in rule.disambiguating_tokens:
                # This context token resolves the ambiguity, so return the rule's
                # feature applicability
                return rule.feature_applicability

        # None of the context tokens resolved the ambiguity so return the inverse of the
        # rules feature applicability.
        return not rule.feature_applicability

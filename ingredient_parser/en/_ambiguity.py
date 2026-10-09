#!/usr/bin/env python3


from dataclasses import dataclass
from typing import ClassVar

from ingredient_parser.dataclasses import Token


@dataclass
class FeatureDisambiguator:
    """Dataclass defining the data needed to disambiguate a feature for a token.

    Attributes
    ----------
    context_window : tuple[int, int]
        Number of tokens before and after the feature-ambiguous token to check for
        disambiguating tokens.
    disambiguating_tokens : list[str]
        List of tokens that disambiguate the feature for the token.
    feature_applicability : bool
        If True, finding a disambiguating token within the context window means the
        feature applies to the token.
        If False, finding a disambiguating token within the context window means the
        feature does not apply to the token.
    """

    context_window: tuple[int, int]
    disambiguating_tokens: list[str]
    feature_applicability: bool


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
    AMBIGUOUS_TOKENS : ClassVar[dict[tuple[str, bool, str], FeatureDisambiguator]]
        Dict defining ambiguous tokens.
        The keys of the dict are a tuple of (token, plurality, feature).
    """

    AMBIGUOUS_TOKENS: ClassVar[dict[tuple[str, bool, str], FeatureDisambiguator]] = {
        # Clove is a spice.
        # If garlic appears anywhere in the sentence, assume clove is a unit, hence the
        # big context window.
        ("clove", False, "is_unit"): FeatureDisambiguator(
            context_window=(20, 20),
            disambiguating_tokens=["garlic"],
            feature_applicability=True,
        ),
        ("clove", True, "is_unit"): FeatureDisambiguator(
            context_window=(20, 20),
            disambiguating_tokens=["garlic"],
            feature_applicability=True,
        ),
        # Gelatine comes in leaves, so in this context is always a unit.
        ("leaf", False, "is_unit"): FeatureDisambiguator(
            context_window=(2, 2),
            disambiguating_tokens=["gelatine"],
            feature_applicability=True,
        ),
        ("leaf", True, "is_unit"): FeatureDisambiguator(
            context_window=(2, 2),
            disambiguating_tokens=["gelatine"],
            feature_applicability=True,
        ),
        # Slab bacon
        ("slab", False, "is_unit"): FeatureDisambiguator(
            context_window=(0, 2),
            disambiguating_tokens=["bacon"],
            feature_applicability=False,
        ),
        # Celery can specified in units of ribs.
        # Other uses of ribs usually refer to the cut of meat.
        ("rib", False, "is_unit"): FeatureDisambiguator(
            context_window=(3, 3),
            disambiguating_tokens=["celery"],
            feature_applicability=True,
        ),
        ("rib", True, "is_unit"): FeatureDisambiguator(
            context_window=(3, 3),
            disambiguating_tokens=["celery"],
            feature_applicability=True,
        ),
        # gram flour aka chickpea flour
        # split gram aka chana dal
        ("gram", False, "is_unit"): FeatureDisambiguator(
            context_window=(3, 3),
            disambiguating_tokens=["flour"],
            feature_applicability=False,
        ),
        # glass noodles are a type of noodle
        ("glass", False, "is_unit"): FeatureDisambiguator(
            context_window=(0, 1),
            disambiguating_tokens=["noodles"],
            feature_applicability=False,
        ),
        # stem ginger
        ("stem", False, "is_unit"): FeatureDisambiguator(
            context_window=(0, 1),
            disambiguating_tokens=["ginger"],
            feature_applicability=False,
        ),
        # pound cake
        ("pound", False, "is_unit"): FeatureDisambiguator(
            context_window=(0, 1),
            disambiguating_tokens=["cake"],
            feature_applicability=False,
        ),
        # Medium is usually a size, unless in the context
        ("medium", False, "is_size"): FeatureDisambiguator(
            context_window=(0, 5),
            disambiguating_tokens=["firm", "ripe", "dry", "roast", "curry", "strength"],
            feature_applicability=False,
        ),
    }

    def __init__(self, tokens: list[Token], singularised_indices: list[int]):
        self.tokens = tokens
        self.plural_tokens = singularised_indices

    def __repr__(self) -> str:
        tokens = [t.text for t in self.tokens]
        return f"Disambiguator(tokens={tokens}, plural_tokens={self.plural_tokens})"

    @classmethod
    def is_ambiguous(cls, token: Token, plural: bool, feature: str) -> bool:
        """Return True if the token is ambiguous with respect to the given feature.

        Parameters
        ----------
        token : Token
            Token to determine if ambiguous.

        Returns
        -------
        bool
            True if token is ambiguous, else False.
        """
        return (token.text, plural, feature) in cls.AMBIGUOUS_TOKENS

    def does_feature_apply(self, index: int, feature: str) -> bool:
        """Return True is feature applies to token at given index.

        Parameters
        ----------
        index : int
            Index of token to determine feature applicability of.
        feature : str
            Feature to determine applicability of.
        """
        token = self.tokens[index]
        plural = index in self.plural_tokens
        ambiguity_data = self.AMBIGUOUS_TOKENS.get((token.text, plural, feature))
        if ambiguity_data is None:
            # If, for some reason, there is not ambiguity data, then assume the feature
            # applies.
            return True

        before, after = ambiguity_data.context_window
        context_window = self.tokens[max(index - before, 0) : index + after + 1]

        for context_token in context_window:
            if context_token.index == index:
                # No need check the token we're interested in.
                continue
            if context_token.text in ambiguity_data.disambiguating_tokens:
                return ambiguity_data.feature_applicability

        return not ambiguity_data.feature_applicability

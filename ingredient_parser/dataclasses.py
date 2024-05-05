#!/usr/bin/env python3

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

import pint
import pycrfsuite


@dataclass
class IngredientAmount:
    """Dataclass for holding a parsed ingredient amount.

    On instantiation, the unit is made plural if necessary.

    Attributes
    ----------
    quantity : float | str
        Parsed ingredient quantity, as a float where possible, otherwise a string.
        If the amount if a range, this is the lower limit of the range.
    quantity_max : float | str
        If the amount is a range, this is the upper limit of the range.
        Otherwise, this is the same as the quantity field.
        This is set automatically depending on the type of quantity.
    unit : str | pint.Unit
        Unit of parsed ingredient quantity.
        If the quantity is recognised in the pint unit registry, a pint.Unit
        object is used.
    text : str
        String describing the amount e.g. "1 cup"
    confidence : float
        Confidence of parsed ingredient amount, between 0 and 1.
        This is the average confidence of all tokens that contribute to this object.
    starting_index : int
        Index of token in sentence that starts this amount
    APPROXIMATE : bool, optional
        When True, indicates that the amount is approximate.
        Default is False.
    SINGULAR : bool, optional
        When True, indicates if the amount refers to a singular item of the ingredient.
        Default is False.
    RANGE : bool, optional
        When True, indicates the amount is a range e.g. 1-2.
        Default is False.
    MULTIPLIER : bool, optional
        When True, indicates the amount is a multiplier e.g. 1x, 2x.
        Default is False.
    """

    quantity: float | str
    quantity_max: float | str
    unit: str | pint.Unit
    text: str
    confidence: float
    starting_index: int
    APPROXIMATE: bool = False
    SINGULAR: bool = False
    RANGE: bool = False
    MULTIPLIER: bool = False


@dataclass
class CompositeIngredientAmount:
    """Dataclass for a composite ingredient amount.

    This is an amount comprising more than one IngredientAmount object
    e.g. "1 lb 2 oz" or "1 cup plus 1 tablespoon".

    Attributes
    ----------
    amounts : list[IngredientAmount]
        List of IngredientAmount objects that make up the composite amount. The order
        in this list is the order they appear in the sentence.
    join : str
        String of text that joins the amounts, e.g. "plus".
    text : str
        Composite amount as a string, automatically generated the amounts and
        join attributes.
    confidence : float
        Confidence of parsed ingredient amount, between 0 and 1.
        This is the average confidence of all tokens that contribute to this object.
    starting_index : int
        Index of token in sentence that starts this amount
    """

    amounts: list[IngredientAmount]
    join: str
    text: str = field(init=False)
    confidence: float = field(init=False)
    starting_index: int = field(init=False)

    def __post_init__(self):
        """On dataclass instantiation, generate the text field."""
        if self.join == "":
            self.text = " ".join([amount.text for amount in self.amounts])
        else:
            self.text = f"{ self.join }".join([amount.text for amount in self.amounts])

        # Set starting_index for composite amount to minimum starting_index for
        # amounts that make up the composite amount.
        self.starting_index = min(amount.starting_index for amount in self.amounts)

        # Set confidence to average of confidence values for amounts that make up the
        # composite amount.
        self.confidence = mean(amount.confidence for amount in self.amounts)

    def combined(self) -> pint.Quantity:
        """Return the combined amount in a single unit for the composite amount.

        The combined amount is returned as a pint.Quantity object.

        Returns
        -------
        pint.Quantity
            Combined amount
        """
        return sum(amount.quantity * amount.unit for amount in self.amounts)


@dataclass
class IngredientText:
    """Dataclass for holding a parsed ingredient string.

    Attributes
    ----------
    text : str
        Parsed text from ingredient.
        This is comprised of all tokens with the same label.
    confidence : float
        Confidence of parsed ingredient amount, between 0 and 1.
        This is the average confidence of all tokens that contribute to this object.
    """

    text: str
    confidence: float


@dataclass
class ParsedIngredient:
    """Dataclass for holding the parsed values for an input sentence.

    Attributes
    ----------
    name : IngredientText | None
        Ingredient name parsed from input sentence.
        If no ingredient name was found, this is None.
    size : IngredientText | None
        Size modifer of ingredients, such as small or large.
        If no size modifier, this is None.
    amount : List[IngredientAmount]
        List of IngredientAmount objects, each representing a matching quantity and
        unit pair parsed from the sentence.
    preparation : IngredientText | None
        Ingredient preparation instructions parsed from sentence.
        If no ingredient preparation instruction was found, this is None.
    comment : IngredientText | None
        Ingredient comment parsed from input sentence.
        If no ingredient comment was found, this is None.
    purpose : IngredientText | None
        The purpose of the ingredient parsed from the sentence.
        If no purpose was found, this is None.
    sentence : str
        Normalised input sentence
    """

    name: IngredientText | None
    size: IngredientText | None
    amount: list[IngredientAmount]
    preparation: IngredientText | None
    comment: IngredientText | None
    purpose: IngredientText | None
    sentence: str


@dataclass
class ParserDebugInfo:
    """Dataclass for holding intermediate objects generated during parsing.

    Attributes
    ----------
    sentence : str
        Input ingredient sentence.
    PreProcessor : PreProcessor
        PreProcessor object created using input sentence.
    PostProcessor : PostProcessor
        PostProcessor object created using tokens, labels and scores from
        input sentence.
    Tagger : pycrfsuite.Tagger
        CRF model tagger object.
    """

    sentence: str
    PreProcessor: Any
    PostProcessor: Any
    tagger: pycrfsuite.Tagger

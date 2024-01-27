#!/usr/bin/env python3

from dataclasses import InitVar, dataclass, field
from statistics import mean

from ingredient_parser._utils import pluralise_units


@dataclass
class _PartialIngredientAmount:
    """Dataclass for holding the information for an ingredient amount whilst it's being
    built up.

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
        Index of token that starts this amount
    related_to_previous : bool, optional
        If True, indicates it is related to the previous IngredientAmount object. All
        related objects should have the same APPROXIMATE and SINGULAR flags
    APPROXIMATE : bool, optional
        When True, indicates that the amount is approximate.
        Default is False.
    SINGULAR : bool, optional
        When True, indicates if the amount refers to a singular item of the ingredient.
        Default is False.
    """

    quantity: str
    unit: list[str]
    confidence: list[float]
    _starting_index: int
    related_to_previous: bool = False
    APPROXIMATE: bool = False
    SINGULAR: bool = False


@dataclass
class IngredientAmount:
    """Dataclass for holding a parsed ingredient amount, comprising the following
    attributes.

    On instantiation, the unit is made plural if necessary.

    Attributes
    ----------
    quantity : str
        Parsed ingredient quantity
    unit : str
        Unit of parsed ingredient quantity
    text : str
        Amount as a string, automatically generated from the quantity and unit
    confidence : float
        Confidence of parsed ingredient amount, between 0 and 1.
        This is the average confidence of all tokens that contribute to this object.
    APPROXIMATE : bool, optional
        When True, indicates that the amount is approximate.
        Default is False.
    SINGULAR : bool, optional
        When True, indicates if the amount refers to a singular item of the ingredient.
        Default is False.
    """

    quantity: str
    unit: str
    text: str = field(init=False)
    confidence: float
    starting_index: InitVar[int]
    APPROXIMATE: bool = False
    SINGULAR: bool = False

    def __post_init__(self, starting_index):
        """
        On dataclass instantiation, make the unit plural if required, and generate the
        text field.
        """
        if self.quantity != "1" and self.quantity != "":
            self.unit = pluralise_units(self.unit)

        self.text = " ".join((self.quantity, self.unit)).strip()

        # Assign starting_index to _starting_index
        self._starting_index = starting_index


@dataclass
class CompositeIngredientAmount:
    """Dataclass for a composite ingredient amount. This is an amount comprising
    more than one IngredientAmount object e.g. "1 lb 2 oz" or "1 cup plus 1 tablespoon".

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
    """

    amounts: list[IngredientAmount]
    join: str
    text: str = field(init=False)

    def __post_init__(self):
        """
        On dataclass instantiation, generate the text field.
        """
        if self.join == "":
            self.text = " ".join([amount.text for amount in self.amounts])
        else:
            self.text = f"{ self.join }".join([amount.text for amount in self.amounts])

        # Set starting_index for composite amount to minimum _starting_index for
        # amounts that make up the composite amount.
        self._starting_index = min(amount._starting_index for amount in self.amounts)

        # Set confidence to average of confidence values for amounts that make up the
        # composite amount.
        self.confidence = mean(amount.confidence for amount in self.amounts)


@dataclass
class IngredientText:
    """Dataclass for holding a parsed ingredient string, comprising the following
    attributes.

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
    amount : List[IngredientAmount]
        List of IngredientAmount objects, each representing a matching quantity and
        unit pair parsed from the sentence.
    preparation : IngredientText | None
        Ingredient preparation instructions parsed from sentence.
        If not ingredient preparation instruction was found, this is None.
    comment : IngredientText | None
        Ingredient comment parsed from input sentence.
        If no ingredient comment was found, this is None.
    sentence : str
        Normalised input sentence
    """

    name: IngredientText | None
    amount: list[IngredientAmount]
    preparation: IngredientText | None
    comment: IngredientText | None
    sentence: str

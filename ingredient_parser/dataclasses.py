#!/usr/bin/env python3

import copy
import operator
from dataclasses import dataclass, field
from fractions import Fraction
from functools import reduce
from statistics import mean
from typing import Any

import pint
import pycrfsuite

from ._common import UREG


@dataclass
class IngredientAmount:
    """Dataclass for holding a parsed ingredient amount.

    On instantiation, the unit is made plural if necessary.

    Attributes
    ----------
    quantity : Fraction | str
        Parsed ingredient quantity, as a Fraction where possible, otherwise a string.
        If the amount if a range, this is the lower limit of the range.
    quantity_max : Fraction | str
        If the amount is a range, this is the upper limit of the range.
        Otherwise, this is the same as the quantity field.
        This is set automatically depending on the type of quantity.
    unit : str | pint.Unit
        Unit of parsed ingredient quantity.
        If the quantity is recognised in the pint unit registry, a pint.Unit
        object is used.
    text : str
        String describing the amount e.g. "1 cup", "8 oz"
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
    PREPARED_INGREDIENT : bool, optional
        When True, indicates the amount applies to the prepared ingredient.
        When False, indicates the amount applies to the ingredient before preparation.
        Default is False.
    """

    quantity: Fraction | str
    quantity_max: Fraction | str
    unit: str | pint.Unit
    text: str
    confidence: float
    starting_index: int
    APPROXIMATE: bool = False
    SINGULAR: bool = False
    RANGE: bool = False
    MULTIPLIER: bool = False
    PREPARED_INGREDIENT: bool = False

    def _copy(self):
        """Return deepcopy of current object.

        Returns
        -------
        Self
            Deep copy of self
        """
        return copy.deepcopy(self)

    def convert_to(self, unit: str, density: pint.Quantity = 1000 * UREG("kg/m^3")):
        """Convert units of IngredientAmount object to given unit.

        Conversion is only possible if none of the quantity, quantity_max and unit are
        strings.

        Conversion between mass and volume is supported using the density parameter, but
        otherwise a DimensionalityError is raised if attempting to convert units of
        different dimensionality.

        .. warning::

            When a conversion between mass <-> volume is performed, the quantities will
            be converted to floats.

        Parameters
        ----------
        unit : str
            Unit to convert to.
        density : pint.Quantity, optional
            Density used for conversion between volume and mass.
            Default is the density of water.

        Returns
        -------
        Self
            Copy of IngredientAmount object with units converted to given unit.

        Raises
        ------
        TypeError
            Raised if unit, quantity or quantity_max are str
        """
        if (
            isinstance(self.unit, str)
            or isinstance(self.quantity, str)
            or isinstance(self.quantity_max, str)
        ):
            raise TypeError("Cannot convert where quantity or unit is a string.")

        q: pint.Quantity = self.quantity * self.unit  # type: ignore
        q_max: pint.Quantity = self.quantity_max * self.unit  # type: ignore

        # Apply density context for conversion.
        # This is only relevant if converting between mass <-> volume.
        with UREG.context("density", p=density):
            q_converted = q.to(unit)  # type: ignore
            q_max_converted = q_max.to(unit)  # type: ignore

        converted_amount = self._copy()
        converted_amount.quantity = q_converted.magnitude
        converted_amount.quantity_max = q_max_converted.magnitude
        converted_amount.unit = q_converted.units  # type: ignore

        # Fraction object don't support float-style formatting until Python 3.12, so we
        # can't just use f"{q_converted:P}"
        converted_amount.text = (
            f"{float(q_converted.magnitude):g} " + f"{q_converted.units:P}"
        )

        return converted_amount


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
    subtractive : bool
        If True, the amounts combine subtractively. If False, the amounts combine
        additively.
    text : str
        Composite amount as a string, automatically generated the amounts and
        join attributes.
    confidence : float
        Confidence of parsed ingredient amount, between 0 and 1.
        This is the average confidence of all tokens that contribute to this object.
    starting_index : int
        Index of token in sentence that starts this amount.
    """

    amounts: list[IngredientAmount]
    join: str
    subtractive: bool
    text: str = field(init=False)
    confidence: float = field(init=False)
    starting_index: int = field(init=False)

    def __post_init__(self):
        """On dataclass instantiation, generate the text field."""
        if self.join == "":
            self.text = " ".join([amount.text for amount in self.amounts])
        else:
            self.text = f"{self.join}".join([amount.text for amount in self.amounts])

        # Set starting_index for composite amount to minimum starting_index for
        # amounts that make up the composite amount.
        self.starting_index = min(amount.starting_index for amount in self.amounts)

        # Set confidence to average of confidence values for amounts that make up the
        # composite amount.
        self.confidence = mean(amount.confidence for amount in self.amounts)

    def combined(self) -> pint.Quantity:
        """Return the combined amount in a single unit for the composite amount.

        The amounts that comprise the composite amount are combined according to whether
        the composite amount is subtractive or not.
        The combined amount is returned as a pint.Quantity object.

        Returns
        -------
        pint.Quantity
            Combined amount

        Raises
        ------
        TypeError
            Raised if any of the amounts in the object do not comprise a float quantity
            and a pint.Unit unit. In these cases, they amounts cannot be combined.
        """
        # Check amounts are compatible for combination
        for amount in self.amounts:
            if not (
                isinstance(amount.quantity, Fraction)
                and isinstance(amount.unit, pint.Unit)
            ):
                q_type = type(amount.quantity).__name__
                u_type = type(amount.unit).__name__
                raise TypeError(
                    (
                        f"Incompatible quantity <{q_type}> "
                        f"and unit <{u_type}> for combining."
                    )
                )

        if self.subtractive:
            op = operator.sub
        else:
            op = operator.add

        return reduce(
            op,
            (amount.quantity * amount.unit for amount in self.amounts),  # type: ignore
        )

    def convert_to(self, unit: str, density: pint.Quantity = 1000 * UREG("kg/m^3")):
        """Convert units of the combined CompositeIngredientAmount object to given unit.

        Conversion is only possible if none of the quantity, quantity_max and unit are
        strings.

        Conversion between mass and volume is supported using the density parameter, but
        otherwise a DimensionalityError is raised if attempting to convert units of
        different dimensionality.

        .. warning::

            When a conversion between mass <-> volume is performed, the quantities will
            be converted to floats.

        Parameters
        ----------
        unit : str
            Unit to convert to.
        density : pint.Quantity, optional
            Density used for conversion between volume and mass.
            Default is the density of water.

        Returns
        -------
        pint.Quantity
            Combined amount converted to given units

        """
        # Apply density context for conversion.
        # This is only relevant if converting between mass <-> volume.
        with UREG.context("density", p=density):
            return self.combined().to(unit)


@dataclass
class IngredientText:
    """Dataclass for holding a parsed ingredient string.

    Attributes
    ----------
    text : str
        Parsed text from ingredient.
        This is comprised of all tokens with the same label.
    confidence : float
        Confidence of parsed ingredient text, between 0 and 1.
        This is the average confidence of all tokens that contribute to this object.
    starting_index : int
        Index of token in sentence that starts this text
    """

    text: str
    confidence: float
    starting_index: int


@dataclass
class FoundationFood:
    """Dataclass for the attributes of an entry in the Food Data Central database that
    matches an ingredient name from an ingredient sentence.

    Attributes
    ----------
    text : str
        Description FDC database entry.
    confidence : float
        Confidence of the match, between 0 and 1.
    fdc_id : int
        ID of the FDC database entry.
    category: str
        Category of FDC database entry.
    data_type : str
        Food Data Central data set the entry belongs to.
    url : str
        URL for FDC database entry.
    """

    text: str
    confidence: float
    fdc_id: int
    category: str
    data_type: str
    url: str = field(init=False)

    def __post_init__(self):
        self.url = f"https://fdc.nal.usda.gov/food-details/{self.fdc_id}/nutrients"

    def __eq__(self, other):
        return isinstance(other, FoundationFood) and self.fdc_id == other.fdc_id

    def __hash__(self):
        return hash(self.fdc_id)


@dataclass
class ParsedIngredient:
    """Dataclass for holding the parsed values for an input sentence.

    Attributes
    ----------
    name : list[IngredientText]
        List of IngredientText objects, each representing an ingreident name parsed from
        input sentence.
        If no ingredient names are found, this is an empty list.
    size : IngredientText | None
        Size modifier of ingredients, such as small or large.
        If no size modifier, this is None.
    amount : List[IngredientAmount | CompositeIngredientAmount]
        List of IngredientAmount objects, each representing a matching quantity and
        unit pair parsed from the sentence.
        If no ingredient amounts are found, this is an empty list.
    preparation : IngredientText | None
        Ingredient preparation instructions parsed from sentence.
        If no ingredient preparation instruction was found, this is None.
    comment : IngredientText | None
        Ingredient comment parsed from input sentence.
        If no ingredient comment was found, this is None.
    purpose : IngredientText | None
        The purpose of the ingredient parsed from the sentence.
        If no purpose was found, this is None.
    foundation_foods : list[FoundationFood]
        List of foundation foods from the parsed sentence.
    sentence : str
        Normalised input sentence
    """

    name: list[IngredientText]
    size: IngredientText | None
    amount: list[IngredientAmount | CompositeIngredientAmount]
    preparation: IngredientText | None
    comment: IngredientText | None
    purpose: IngredientText | None
    foundation_foods: list[FoundationFood]
    sentence: str

    def __post_init__(self):
        """Set PREPARED_INGREDIENT flag for amounts.

        The flag is set if:
         * the amount is before the preparation instructions AND
         * the preparation instructions are before the name(s)
        e.g. 100 g sifted flour

        OR
         * the preparation instruction is after the name(s) AND
         * the amount is after the preparation instruction
        e.g. Onion, thinly sliced (about 1 cup)


        Assumes that any preparation text appear entirely before or entirely after all
        names.
        """
        if not self.name or not self.preparation:
            return

        first_name_starting_index = min(n.starting_index for n in self.name)
        last_name_starting_index = max(n.starting_index for n in self.name)

        for amount in self.amount:
            if (
                amount.starting_index
                < self.preparation.starting_index
                < first_name_starting_index
            ) or (
                last_name_starting_index
                < self.preparation.starting_index
                < amount.starting_index
            ):
                if isinstance(amount, CompositeIngredientAmount):
                    for composite_amount in amount.amounts:
                        composite_amount.PREPARED_INGREDIENT = True
                else:
                    amount.PREPARED_INGREDIENT = True


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
    tagger: pycrfsuite.Tagger  # type: ignore

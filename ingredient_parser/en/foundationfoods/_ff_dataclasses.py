#!/usr/bin/env python3

from dataclasses import dataclass
from typing import NamedTuple


class IngredientToken(NamedTuple):
    token: str
    pos_tag: str


@dataclass
class FDCIngredient:
    """Dataclass for details of an ingredient from the FoodDataCentral database."""

    fdc_id: int
    data_type: str
    description: str
    category: str
    tokens: list[str]
    embedding_tokens: list[str]
    embedding_weights: list[float]

    def __eq__(self, other):
        return isinstance(other, FDCIngredient) and self.fdc_id == other.fdc_id

    def __hash__(self):
        return hash(self.fdc_id)


@dataclass
class FDCIngredientMatch:
    """Dataclass for details of a matching FDC ingredient."""

    fdc: FDCIngredient
    score: float

    def __eq__(self, other):
        return (
            isinstance(other, FDCIngredientMatch)
            and self.score == other.score
            and self.fdc.fdc_id == other.fdc.fdc_id
        )

    def __hash__(self):
        return hash((self.score, self.fdc.fdc_id))

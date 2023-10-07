import pytest

from ingredient_parser import PostProcessor
from ingredient_parser.postprocess import (
    IngredientAmount,
    IngredientText,
    ParsedIngredient,
)


@pytest.fixture
def p():
    """Define a PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    sentence = "2 14 ounce cans coconut milk"
    tokens = ["2", "14", "ounce", "can", "coconut", "milk"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "NAME", "NAME"]
    scores = [
        0.9991370577083561,
        0.9725378063405858,
        0.9978510889596651,
        0.9922350007952175,
        0.9886087821704076,
        0.9969237827902526,
    ]

    return PostProcessor(sentence, tokens, labels, scores)


class TestPostProcessor__builtins__:
    def test__str__(self, p):
        """
        Test PostProcessor __str__
        """
        truth = """Post-processed recipe ingredient sentence
\t[('2', 'QTY'), ('14', 'QTY'), ('ounce', 'UNIT'), ('can', 'UNIT'), \
('coconut', 'NAME'), ('milk', 'NAME')]"""
        assert str(p) == truth

    def test__repr__(self, p):
        """
        Test PostProessor __repr__
        """
        assert repr(p) == 'PostProcessor("2 14 ounce cans coconut milk")'


class TestPostProcessor_parsed:
    def test(self, p):
        """
        Test fixture returns expected ParsedIngredient object
        """
        expected = ParsedIngredient(
            name=IngredientText(text="coconut milk", confidence=0.992766),
            amount=[
                IngredientAmount(
                    quantity="2",
                    unit="cans",
                    confidence=0.9956860292517868,
                    APPROXIMATE=False,
                    SINGULAR=False,
                ),
                IngredientAmount(
                    quantity="14",
                    unit="ounces",
                    confidence=0.9725378063405858,
                    APPROXIMATE=False,
                    SINGULAR=True,
                ),
            ],
            preparation=None,
            comment=None,
            other=None,
            sentence="2 14 ounce cans coconut milk",
        )
        assert p.parsed() == expected

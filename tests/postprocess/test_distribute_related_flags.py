import pytest

from ingredient_parser import PostProcessor
from ingredient_parser.postprocess import (
    _PartialIngredientAmount,
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


class TestPostProcessor_distribute_related_flags:
    def test_distribute_approximate(self, p):
        """
        Test that all amounts get the APPROXIMATE flag set to True
        """
        amounts = [
            _PartialIngredientAmount("", [""], [0], 0, APPROXIMATE=True),
            _PartialIngredientAmount("", [""], [0], 0, related_to_previous=True),
            _PartialIngredientAmount("", [""], [0], 0, related_to_previous=True),
        ]
        outputs = p._distribute_related_flags(amounts)
        approximate_flags = [am.APPROXIMATE for am in outputs]
        singular_flags = [am.SINGULAR for am in outputs]

        assert all(approximate_flags)
        assert not all(singular_flags)

    def test_distribute_singular(self, p):
        """
        Test that all amounts get the SINGULAR flag set to True
        """
        amounts = [
            _PartialIngredientAmount("", [""], [0], 0),
            _PartialIngredientAmount("", [""], [0], 0, related_to_previous=True),
            _PartialIngredientAmount(
                "", [""], [0], 0, related_to_previous=True, SINGULAR=True
            ),
        ]
        outputs = p._distribute_related_flags(amounts)
        approximate_flags = [am.APPROXIMATE for am in outputs]
        singular_flags = [am.SINGULAR for am in outputs]

        assert not all(approximate_flags)
        assert all(singular_flags)

    def test_no_distribute(self, p):
        """
        Test that all amounts get the SINGULAR flag set to True
        """
        amounts = [
            _PartialIngredientAmount("", [""], [0], 0, APPROXIMATE=True),
            _PartialIngredientAmount("", [""], [0], 0),
            _PartialIngredientAmount("", [""], [0], 0, SINGULAR=True),
        ]
        outputs = p._distribute_related_flags(amounts)

        assert [a.APPROXIMATE for a in outputs] == [True, False, False]
        assert [a.SINGULAR for a in outputs] == [False, False, True]

    def test_mixed_distribute(self, p):
        """
        Test that all amounts get the SINGULAR flag set to True
        """
        amounts = [
            _PartialIngredientAmount("", [""], [0], 0),
            _PartialIngredientAmount("", [""], [0], 0, APPROXIMATE=True),
            _PartialIngredientAmount(
                "", [""], [0], 0, related_to_previous=True, SINGULAR=True
            ),
        ]
        outputs = p._distribute_related_flags(amounts)

        assert [a.APPROXIMATE for a in outputs] == [False, True, True]
        assert [a.SINGULAR for a in outputs] == [False, True, True]

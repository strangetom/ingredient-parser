import pytest

from ingredient_parser.dataclasses import (
    IngredientText,
    ParsedIngredient,
)
from ingredient_parser.en import PostProcessor
from ingredient_parser.en._utils import ingredient_amount_factory


@pytest.fixture
def p():
    """Define a PostProcessor object with discard_isolated_stop_words set to True
    to use for testing the PostProcessor class methods.
    """
    sentence = "2 14 ounce cans of coconut milk"
    tokens = ["2", "14", "ounce", "can", "of", "coconut", "milk"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "COMMENT", "NAME", "NAME"]
    scores = [
        0.9995971493946465,
        0.9941502269360797,
        0.9978571790476597,
        0.9343053167729019,
        0.8352859914316577,
        0.9907929042080257,
        0.9954196827665529,
    ]

    return PostProcessor(
        sentence, tokens, labels, scores, discard_isolated_stop_words=True
    )


@pytest.fixture
def p_string_numbers():
    """Define a PostProcessor object with discard_isolated_stop_words set to True
    to use for testing the PostProcessor class methods.
    """
    sentence = "2 butternut squash, about one and one-half pounds each"
    tokens = [
        "2",
        "butternut",
        "squash",
        ",",
        "about",
        "one",
        "and",
        "one-half",
        "pound",
        "each",
    ]
    labels = [
        "QTY",
        "NAME",
        "NAME",
        "PUNC",
        "COMMENT",
        "QTY",
        "QTY",
        "QTY",
        "UNIT",
        "COMMENT",
    ]
    scores = [
        0.9984380824450226,
        0.9978651159111281,
        0.9994189046396519,
        0.9999962272946663,
        0.9922077606027025,
        0.8444345718042952,
        0.711112570789477,
        0.7123166610204924,
        0.7810746702425934,
        0.9447105511029686,
    ]

    return PostProcessor(
        sentence, tokens, labels, scores, discard_isolated_stop_words=True
    )


@pytest.fixture
def p_quantity_fractions():
    """Define a PostProcessor object with quantity_fractions set to True
    to use for testing the PostProcessor class methods.
    """
    sentence = "2 butternut squash, about one and one-half pounds each"
    tokens = [
        "2",
        "butternut",
        "squash",
        ",",
        "about",
        "one",
        "and",
        "one-half",
        "pound",
        "each",
    ]
    labels = [
        "QTY",
        "NAME",
        "NAME",
        "PUNC",
        "COMMENT",
        "QTY",
        "QTY",
        "QTY",
        "UNIT",
        "COMMENT",
    ]
    scores = [
        0.9984380824450226,
        0.9978651159111281,
        0.9994189046396519,
        0.9999962272946663,
        0.9922077606027025,
        0.8444345718042952,
        0.711112570789477,
        0.7123166610204924,
        0.7810746702425934,
        0.9447105511029686,
    ]

    return PostProcessor(sentence, tokens, labels, scores, quantity_fractions=True)


@pytest.fixture
def p_postprep():
    """Define a PostProcessor object with discard_isolated_stop_words set to False
    to use for testing the PostProcessor class methods.
    """
    sentence = "1 tbsp chopped pistachios"
    tokens = ["1", "tbsp", "chopped", "pistachios"]
    labels = ["QTY", "UNIT", "PREP", "NAME"]
    scores = [
        0.9997566777785302,
        0.9975314001146002,
        0.9936702913782429,
        0.9988409678348467,
    ]

    return PostProcessor(
        sentence, tokens, labels, scores, discard_isolated_stop_words=False
    )


@pytest.fixture
def p_no_discard():
    """Define a PostProcessor object with discard_isolated_stop_words set to False
    to use for testing the PostProcessor class methods.
    """
    sentence = "2 14 ounce cans of coconut milk"
    tokens = ["2", "14", "ounce", "can", "of", "coconut", "milk"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "COMMENT", "NAME", "NAME"]
    scores = [
        0.9995971493946465,
        0.9941502269360797,
        0.9978571790476597,
        0.9343053167729019,
        0.8352859914316577,
        0.9907929042080257,
        0.9954196827665529,
    ]

    return PostProcessor(
        sentence, tokens, labels, scores, discard_isolated_stop_words=False
    )


class TestPostProcessor__builtins__:
    def test__str__(self, p):
        """
        Test PostProcessor __str__
        """
        truth = """Post-processed recipe ingredient sentence
\t[('2', 'QTY'), ('14', 'QTY'), ('ounce', 'UNIT'), ('can', 'UNIT'), ('of', 'COMMENT'), \
('coconut', 'NAME'), ('milk', 'NAME')]"""
        assert str(p) == truth

    def test__repr__(self, p):
        """
        Test PostProessor __repr__
        """
        assert repr(p) == 'PostProcessor("2 14 ounce cans of coconut milk")'


class TestPostProcessor_parsed:
    def test(self, p):
        """
        Test fixture returns expected ParsedIngredient object, with the word "of"
        discarded due to discard_isolated_stop_words being set to True.
        """
        expected = ParsedIngredient(
            name=IngredientText(
                text="coconut milk", confidence=0.993106, starting_index=5
            ),
            size=None,
            amount=[
                ingredient_amount_factory(
                    quantity="2",
                    unit="cans",
                    text="2 cans",
                    confidence=0.966951,
                    starting_index=0,
                    APPROXIMATE=False,
                    SINGULAR=False,
                ),
                ingredient_amount_factory(
                    quantity="14",
                    unit="ounce",
                    text="14 ounces",
                    confidence=0.994150,
                    starting_index=1,
                    APPROXIMATE=False,
                    SINGULAR=True,
                ),
            ],
            preparation=None,
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence="2 14 ounce cans of coconut milk",
        )

        assert p.parsed == expected

    def test_string_numbers(self, p_string_numbers):
        """
        Test fixture returns expected ParsedIngredient object, with the string
        numbers replaced with numeric range.
        """
        expected = ParsedIngredient(
            name=IngredientText(
                text="butternut squash", confidence=0.998642, starting_index=1
            ),
            size=None,
            amount=[
                ingredient_amount_factory(
                    quantity="2",
                    unit="",
                    text="2",
                    confidence=0.998438,
                    starting_index=0,
                    APPROXIMATE=False,
                    SINGULAR=False,
                ),
                ingredient_amount_factory(
                    quantity="1.5",
                    unit="pound",
                    text="1 1/2 pounds",
                    confidence=0.768515,
                    starting_index=5,
                    APPROXIMATE=True,
                    SINGULAR=True,
                ),
            ],
            preparation=None,
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence="2 butternut squash, about one and one-half pounds each",
        )

        assert p_string_numbers.parsed == expected

    def test_quantity_fractions(self, p_quantity_fractions):
        """
        Test fixture returns expected ParsedIngredient object, with the string
        numbers replaced with numeric range.
        """
        expected = ParsedIngredient(
            name=IngredientText(
                text="butternut squash", confidence=0.998642, starting_index=1
            ),
            size=None,
            amount=[
                ingredient_amount_factory(
                    quantity="2",
                    unit="",
                    text="2",
                    confidence=0.998438,
                    starting_index=0,
                    APPROXIMATE=False,
                    SINGULAR=False,
                    quantity_fractions=True,
                ),
                ingredient_amount_factory(
                    quantity="1.5",
                    unit="pound",
                    text="1 1/2 pounds",
                    confidence=0.768515,
                    starting_index=5,
                    APPROXIMATE=True,
                    SINGULAR=True,
                    quantity_fractions=True,
                ),
            ],
            preparation=None,
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence="2 butternut squash, about one and one-half pounds each",
        )

        assert p_quantity_fractions.parsed == expected

    def test_postprep_amounts(self, p_postprep):
        """ """
        expected = ParsedIngredient(
            name=IngredientText(
                text="pistachios", confidence=0.998841, starting_index=3
            ),
            size=None,
            amount=[
                ingredient_amount_factory(
                    quantity="1",
                    unit="tbsp",
                    text="1 tbsp",
                    confidence=0.998644,
                    starting_index=0,
                )
            ],
            preparation=IngredientText(
                text="chopped", confidence=0.99367, starting_index=2
            ),
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence="1 tbsp chopped pistachios",
        )

        assert p_postprep.parsed == expected

    def test_no_discard_isolated_stop_words(self, p_no_discard):
        """
        Test fixture returns expected ParsedIngredient object, with the word "of"
        kept due to discard_isolated_stop_words being set to False.
        """
        expected = ParsedIngredient(
            name=IngredientText(
                text="coconut milk", confidence=0.993106, starting_index=5
            ),
            size=None,
            amount=[
                ingredient_amount_factory(
                    quantity="2",
                    unit="cans",
                    text="2 cans",
                    confidence=0.966951,
                    starting_index=0,
                    APPROXIMATE=False,
                    SINGULAR=False,
                ),
                ingredient_amount_factory(
                    quantity="14",
                    unit="ounce",
                    text="14 ounces",
                    confidence=0.994150,
                    starting_index=1,
                    APPROXIMATE=False,
                    SINGULAR=True,
                ),
            ],
            preparation=None,
            comment=IngredientText(text="of", confidence=0.835286, starting_index=4),
            purpose=None,
            foundation_foods=[],
            sentence="2 14 ounce cans of coconut milk",
        )

        assert p_no_discard.parsed == expected

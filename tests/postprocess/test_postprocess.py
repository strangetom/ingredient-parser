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
    pos_tags = ["CD", "CD", "NN", "MD", "VB", "NN", "NN"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "COMMENT", "B_NAME_TOK", "I_NAME_TOK"]
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
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        discard_isolated_stop_words=True,
    )


@pytest.fixture
def p_string_numbers():
    """Define a PostProcessor object with discard_isolated_stop_words set to True
    to use for testing the PostProcessor class methods.

    This sentence includes numbers written as words.
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
    pos_tags = ["CD", "NN", "NN", ",", "IN", "CD", "CC", "JJ", "NN", "DT"]
    labels = [
        "QTY",
        "B_NAME_TOK",
        "I_NAME_TOK",
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
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        discard_isolated_stop_words=True,
    )


@pytest.fixture
def p_string_numbers_range():
    """Define a PostProcessor object with discard_isolated_stop_words set to True
    to use for testing the PostProcessor class methods.

    This sentence includes a number range written in words.
    """
    sentence = "2 butternut squash, about one or two pounds each"
    tokens = [
        "2",
        "butternut",
        "squash",
        ",",
        "about",
        "one",
        "or",
        "two",
        "pounds",
        "each",
    ]
    pos_tags = ["CD", "NN", "NN", ",", "IN", "CD", "CC", "CD", "NNS", "DT"]
    labels = [
        "QTY",
        "B_NAME_TOK",
        "I_NAME_TOK",
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
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        discard_isolated_stop_words=True,
    )


@pytest.fixture
def p_postprep():
    """Define a PostProcessor object with discard_isolated_stop_words set to False
    to use for testing the PostProcessor class methods.

    This sentence has the name after the preparation instruction.
    """
    sentence = "1 tbsp chopped pistachios"
    tokens = ["1", "tbsp", "chopped", "pistachios"]
    pos_tags = ["CD", "NN", "VBD", "NNS"]
    labels = ["QTY", "UNIT", "PREP", "B_NAME_TOK"]
    scores = [
        0.9997566777785302,
        0.9975314001146002,
        0.9936702913782429,
        0.9988409678348467,
    ]

    return PostProcessor(
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        discard_isolated_stop_words=False,
    )


@pytest.fixture
def p_no_discard():
    """Define a PostProcessor object with discard_isolated_stop_words set to False
    to use for testing the PostProcessor class methods.
    """
    sentence = "2 14 ounce cans of coconut milk"
    tokens = ["2", "14", "ounce", "can", "of", "coconut", "milk"]
    pos_tags = ["CD", "CD", "NN", "MD", "IN", "NN", "NN"]
    labels = ["QTY", "QTY", "UNIT", "UNIT", "COMMENT", "B_NAME_TOK", "I_NAME_TOK"]
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
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        discard_isolated_stop_words=False,
    )


@pytest.fixture
def p_fraction_in_prep():
    """Define a PostProcessor object for sentence with a fraction in prep
    to use for testing the PostProcessor class methods.

    This sentence includes a fraction in the preparation instructions.
    """
    sentence = "3 carrots, peeled and sliced into 5mm (¼in) coins"
    tokens = [
        "3",
        "carrots",
        ",",
        "peeled",
        "and",
        "sliced",
        "into",
        "5",
        "mm",
        "(",
        "#1$4",
        "in",
        ")",
        "coins",
    ]
    pos_tags = [
        "CD",
        "NNS",
        ",",
        "VBD",
        "CC",
        "VBD",
        "IN",
        "CD",
        "NN",
        "(",
        "NNP",
        "IN",
        ")",
        "NNS",
    ]
    labels = [
        "QTY",
        "B_NAME_TOK",
        "PUNC",
        "PREP",
        "PREP",
        "PREP",
        "PREP",
        "PREP",
        "PREP",
        "PUNC",
        "PREP",
        "PREP",
        "PUNC",
        "PREP",
    ]
    scores = [
        0.9994675946370136,
        0.9982121821692039,
        0.9999986664162547,
        0.9999349193863984,
        0.999720763986239,
        0.9999682855629554,
        0.9999116643460678,
        0.9998989415285744,
        0.9994126452404396,
        0.999365113705119,
        0.649315853101702,
        0.651598144547812,
        0.9992304409607873,
        0.660356736493678,
    ]

    return PostProcessor(sentence, tokens, pos_tags, labels, scores)


@pytest.fixture
def p_fraction_range_in_prep():
    """Define a PostProcessor object for sentence with a fraction range in prep
    to use for testing the PostProcessor class methods.

    This sentence includes a number range in the preparation instructions.
    """
    sentence = "3 carrots, peeled and sliced into 5-10mm (¼-½in) coins"
    tokens = [
        "3",
        "carrots",
        ",",
        "peeled",
        "and",
        "sliced",
        "into",
        "5-10",
        "mm",
        "(",
        "#1$4-#1$2",
        "in",
        ")",
        "coins",
    ]
    pos_tags = [
        "CD",
        "NNS",
        ",",
        "VBD",
        "CC",
        "VBD",
        "IN",
        "JJ",
        "NN",
        "(",
        "JJ",
        "IN",
        ")",
        "NNS",
    ]
    labels = [
        "QTY",
        "B_NAME_TOK",
        "PUNC",
        "PREP",
        "PREP",
        "PREP",
        "PREP",
        "PREP",
        "PREP",
        "PUNC",
        "PREP",
        "PREP",
        "PUNC",
        "PREP",
    ]
    scores = [
        0.9994675946370136,
        0.9982121821692039,
        0.9999986664162547,
        0.9999349193863984,
        0.999720763986239,
        0.9999682855629554,
        0.9999116643460678,
        0.9998989415285744,
        0.9994126452404396,
        0.999365113705119,
        0.649315853101702,
        0.651598144547812,
        0.9992304409607873,
        0.660356736493678,
    ]

    return PostProcessor(sentence, tokens, pos_tags, labels, scores)


@pytest.fixture
def p_split_name():
    """Define a PostProcessor object with discard_isolated_stop_words set to False
    to use for testing the PostProcessor class methods.

    This sentence has the name split by a token with a non-name label.
    """
    sentence = "5 fresh large basil leaves"
    tokens = ["5", "fresh", "large", "basil", "leaves"]
    pos_tags = ["CD", "JJ", "JJ", "NN", "NN"]
    labels = ["QTY", "B_NAME_TOK", "SIZE", "B_NAME_TOK", "I_NAME_TOK"]
    scores = [
        0.99938548647492,
        0.968725226931013,
        0.9588222550056443,
        0.5092435116086577,
        0.9877923155569212,
    ]

    return PostProcessor(
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        discard_isolated_stop_words=False,
    )


class TestPostProcessor__builtins__:
    def test__str__(self, p):
        """
        Test PostProcessor __str__
        """
        truth = """Post-processed recipe ingredient sentence
\t[('2', 'QTY'), ('14', 'QTY'), ('ounce', 'UNIT'), ('can', 'UNIT'), ('of', 'COMMENT'), \
('coconut', 'B_NAME_TOK'), ('milk', 'I_NAME_TOK')]"""
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
            name=[
                IngredientText(
                    text="coconut milk", confidence=0.993106, starting_index=5
                )
            ],
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
            name=[
                IngredientText(
                    text="butternut squash", confidence=0.998642, starting_index=1
                )
            ],
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

    def test_string_numbers_range(self, p_string_numbers_range):
        """
        Test fixture returns expected ParsedIngredient object, with the string
        numbers replaced with numeric range.
        """
        expected = ParsedIngredient(
            name=[
                IngredientText(
                    text="butternut squash", confidence=0.998642, starting_index=1
                )
            ],
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
                    quantity="1-2",
                    unit="pounds",
                    text="1-2 pounds",
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
            sentence="2 butternut squash, about one or two pounds each",
        )

        assert p_string_numbers_range.parsed == expected

    def test_postprep_amounts(self, p_postprep):
        """
        Test fixture returns expected ParsedIngredient object, with the preparation
        tokens before the ingredient name.
        """
        expected = ParsedIngredient(
            name=[
                IngredientText(text="pistachios", confidence=0.998841, starting_index=3)
            ],
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
            name=[
                IngredientText(
                    text="coconut milk", confidence=0.993106, starting_index=5
                )
            ],
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

    def test_fraction_in_prep(self, p_fraction_in_prep):
        """
        Test fixture returns expected ParsedIngredient object, with the fraction in the
        preparation instruction retained.
        """
        expected = ParsedIngredient(
            name=[
                IngredientText(text="carrots", confidence=0.998212, starting_index=1)
            ],
            size=None,
            amount=[
                ingredient_amount_factory(
                    quantity="3",
                    unit="",
                    text="3",
                    confidence=0.999468,
                    starting_index=0,
                )
            ],
            preparation=IngredientText(
                text="peeled and sliced into 5 mm (1/4 in) coins",
                confidence=0.905338,
                starting_index=3,
            ),
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence="3 carrots, peeled and sliced into 5mm (¼in) coins",
        )

        assert p_fraction_in_prep.parsed == expected

    def test_fraction_range_in_prep(self, p_fraction_range_in_prep):
        """
        Test fixture returns expected ParsedIngredient object, with the fraction range
        in the preparation instruction retained.
        """
        expected = ParsedIngredient(
            name=[
                IngredientText(text="carrots", confidence=0.998212, starting_index=1)
            ],
            size=None,
            amount=[
                ingredient_amount_factory(
                    quantity="3",
                    unit="",
                    text="3",
                    confidence=0.999468,
                    starting_index=0,
                )
            ],
            preparation=IngredientText(
                text="peeled and sliced into 5-10 mm (1/4-1/2 in) coins",
                confidence=0.905338,
                starting_index=3,
            ),
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence="3 carrots, peeled and sliced into 5-10mm (¼-½in) coins",
        )

        assert p_fraction_range_in_prep.parsed == expected

    def test_split_ingredient_name(self, p_split_name):
        """
        Test fixture returns expected ParsedIngredient object, with a single name
        despite a SIZE token splitting the name.
        """
        expected = ParsedIngredient(
            name=[
                IngredientText(
                    text="fresh basil leaves",
                    confidence=0.858621,
                    starting_index=1,
                )
            ],
            size=IngredientText(text="large", confidence=0.958822, starting_index=2),
            amount=[
                ingredient_amount_factory(
                    quantity="5",
                    unit="",
                    text="5",
                    confidence=0.999385,
                    starting_index=0,
                )
            ],
            preparation=None,
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence="5 fresh large basil leaves",
        )

        assert p_split_name.parsed == expected

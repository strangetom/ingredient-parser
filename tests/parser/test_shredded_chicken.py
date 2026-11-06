import pytest

from ingredient_parser import inspect_parser, parse_ingredient


@pytest.mark.model_dependent
@pytest.mark.parametrize("separate_names", [True, False])
@pytest.mark.parametrize(
    ("sentence", "expected_name", "expected_prepared"),
    [
        ("1 shredded chicken", "chicken", True),
        ("1 shredded whole chicken", "whole chicken", True),
        ("1 whole shredded chicken", "whole chicken", False),
        ("1 whole chicken shredded", "whole chicken", False),
        ("1 whole chicken, shredded", "whole chicken", False),
    ],
)
def test_shredded_chicken_preparation(
    sentence, expected_name, expected_prepared, separate_names
):
    """Word order must not hide preparation or remove whole from the name."""
    parsed = parse_ingredient(sentence, separate_names=separate_names)

    assert [name.text for name in parsed.name] == [expected_name]
    assert parsed.preparation is not None
    assert parsed.preparation.text == "shredded"
    assert parsed.size is None
    assert len(parsed.amount) == 1
    assert parsed.amount[0].quantity == 1
    assert parsed.amount[0].unit == ""
    assert parsed.amount[0].PREPARED_INGREDIENT is expected_prepared


@pytest.mark.model_dependent
@pytest.mark.parametrize(
    "sentence",
    [
        "1 shredded chicken",
        "1 shredded whole chicken",
        "1 whole shredded chicken",
        "1 whole chicken shredded",
        "1 whole chicken, shredded",
    ],
)
def test_shredded_token_is_preparation(sentence):
    """The token label itself must identify preparation before postprocessing."""
    debug = inspect_parser(sentence)
    shredded = next(t for t in debug.PostProcessor.tokens if t.text == "shredded")

    assert shredded.label == "PREP"


@pytest.mark.model_dependent
@pytest.mark.parametrize(
    ("sentence", "expected_name", "expected_preparation"),
    [
        ("1 cup whole milk", "whole milk", None),
        ("1 cup whole wheat flour", "whole wheat flour", None),
        ("1 whole bay leaf", "whole bay leaf", None),
        ("1 whole onion, diced", "whole onion", "diced"),
    ],
)
def test_whole_remains_in_name(sentence, expected_name, expected_preparation):
    parsed = parse_ingredient(sentence)

    assert [name.text for name in parsed.name] == [expected_name]
    assert (parsed.preparation.text if parsed.preparation else None) == (
        expected_preparation
    )
    assert parsed.size is None

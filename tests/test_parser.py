import json
from itertools import zip_longest

import pytest

from ingredient_parser import parse_ingredient
from ingredient_parser.postprocess import (
    IngredientAmount,
    IngredientText,
    ParsedIngredient,
)


def dict_to_ParsedIngredient(data: dict[str, str]) -> ParsedIngredient:
    """Convert test data dictionary to ParsedIngredient object

    Parameters
    ----------
    data : dict[str, str]
        Dictionary of test data containing input sentence and true labels.

    Returns
    -------
    ParsedIngredient
        Object of sentence and true labels in same format as output from
        parse_ingredient function.
    """
    sentence = data["sentence"]
    labels = data["labels"]

    if true_name := labels.get("name", None):
        name = IngredientText(text=true_name, confidence=0)
    else:
        name = None

    if true_prep := labels.get("preparation", None):
        preparation = IngredientText(text=true_prep, confidence=0)
    else:
        preparation = None

    if true_comment := labels.get("comment", None):
        comment = IngredientText(text=true_comment, confidence=0)
    else:
        comment = None

    amount = IngredientAmount(
        quantity=labels.get("quantity", ""),
        unit=labels.get("unit", ""),
        confidence=0,
    )

    return ParsedIngredient(
        name=name,
        amount=[amount],
        preparation=preparation,
        comment=comment,
        other=None,
        sentence=sentence,
    )


def load_test_cases(file: str):
    """Load newline delimited json file of test cases

    Parameters
    ----------
    file : str
        Filename

    Returns
    -------
    List[Dict[str,str]]
        List of dicts of test cases.
        Each dict contains:
            sentence: the input sentence to parse
            labels: the correct labels
    """
    sample_data = []
    with open(file, "r") as f:
        test_cases = f.read().splitlines()
        for case in test_cases:
            if case.startswith("#"):
                continue
            data = json.loads(case)
            obj = dict_to_ParsedIngredient(data)
            sample_data.append(obj)

    return sample_data


class TestParser:
    @pytest.mark.parametrize("truth", load_test_cases("tests/test_parser_simple.json"))
    def test_parser_simple(self, truth):
        """Test simple cases of ingredient sentences that the parser should have no
        issues getting correct

        Parameters
        ----------
        truth : ParsedIngredient
            ParsedIngredient object containing input sentence and true parsed data
        """
        parsed = parse_ingredient(truth.sentence)

        if truth.name is not None:
            assert parsed.name.text == truth.name.text
        else:
            assert parsed.name is None

        if truth.comment is not None:
            assert parsed.comment.text == truth.comment.text
        else:
            assert parsed.comment is None

        if truth.other is not None:
            assert parsed.other.text == truth.other.text
        else:
            assert parsed.other is None

        for output, expected in zip_longest(truth.amount, parsed.amount):
            assert output.quantity == expected.quantity
            assert output.unit == expected.unit

    @pytest.mark.parametrize(
        "truth", load_test_cases("tests/test_parser_alternate_unit_position.json")
    )
    def test_parser_alternate_unit_position(self, truth):
        """Test cases where the unit appears after the ingredient name

        Parameters
        ----------
        truth : ParsedIngredient
            ParsedIngredient object containing input sentence and true parsed data
        """
        parsed = parse_ingredient(truth.sentence)

        if truth.name is not None:
            assert parsed.name.text == truth.name.text
        else:
            assert parsed.name is None

        if truth.comment is not None:
            assert parsed.comment.text == truth.comment.text
        else:
            assert parsed.comment is None

        if truth.other is not None:
            assert parsed.other.text == truth.other.text
        else:
            assert parsed.other is None

        for output, expected in zip_longest(truth.amount, parsed.amount):
            assert output.quantity == expected.quantity
            assert output.unit == expected.unit

    @pytest.mark.parametrize(
        "truth", load_test_cases("tests/test_parser_ambiguous_unit.json")
    )
    def test_parser_ambiguous_unit(self, truth):
        """Test cases where the same word could be a unit or an ingredient,
        depending on context e.g. clove

        Parameters
        ----------
        truth : ParsedIngredient
            ParsedIngredient object containing input sentence and true parsed data
        """
        parsed = parse_ingredient(truth.sentence)

        if truth.name is not None:
            assert parsed.name.text == truth.name.text
        else:
            assert parsed.name is None

        if truth.comment is not None:
            assert parsed.comment.text == truth.comment.text
        else:
            assert parsed.comment is None

        if truth.other is not None:
            assert parsed.other.text == truth.other.text
        else:
            assert parsed.other is None

        for output, expected in zip_longest(truth.amount, parsed.amount):
            assert output.quantity == expected.quantity
            assert output.unit == expected.unit


#    @pytest.mark.parametrize(
#        "data", load_test_cases("tests/test_parser_comment_before_name.json")
#    )
#    def test_parser_comment_before_name(self, data):
#        """Test cases where the comment appears before the ingredient name,
#        e.g. 1 chopped carrot
#
#        Parameters
#        ----------
#        data : Dict[str, Dict[str, str]]
#            Dictionary of sample data with the following keys
#                sentence - the input sentence
#                labels - the correct labels the parser should return
#        """
#        sentence = data["sentence"]
#        true_labels = data["labels"]
#        parsed = parse_ingredient(sentence)
#
#        # parse_ingredient returns a dict with more keys than just the labels
#        # so iterate through each label in true_labels and only check them.
#        for key in true_labels:
#            assert parsed.__dict__[key] == true_labels[key]
#
#    @pytest.mark.parametrize(
#        "data", load_test_cases("tests/test_parser_multiple_units.json")
#    )
#    def test_parser_multiple_units(self, data):
#        """Test cases where there are multiple units in the sentence
#
#        Parameters
#        ----------
#        data : Dict[str, Dict[str, str]]
#            Dictionary of sample data with the following keys
#                sentence - the input sentence
#                labels - the correct labels the parser should return
#        """
#        sentence = data["sentence"]
#        true_labels = data["labels"]
#        parsed = parse_ingredient(sentence)
#
#        # parse_ingredient returns a dict with more keys than just the labels
#        # so iterate through each label in true_labels and only check them.
#        for key in true_labels:
#            assert parsed.__dict__[key] == true_labels[key]

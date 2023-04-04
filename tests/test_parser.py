import json

import pytest

from ingredient_parser import parse_ingredient, parse_ingredient_regex


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
            sample_data.append(data)

    return sample_data


class TestParser:
    @pytest.mark.parametrize("data", load_test_cases("tests/test_parser_simple.json"))
    def test_parser_simple(self, data):
        """Test simple cases of ingredient sentences that the parser should have no
        issues getting correct

        Parameters
        ----------
        data : Dict[str, Dict[str, str]]
            Dictionary of sample data with the following keys
                sentence - the input sentence
                labels - the correct labels the parser should return
        """
        sentence = data["sentence"]
        true_labels = data["labels"]
        parsed = parse_ingredient(sentence)

        # parse_ingredient returns a dict with more keys than just the labels
        # so iterate through each label in true_labels and only check them.
        for key in true_labels:
            assert parsed[key] == true_labels[key]


class TestRegexParser:
    @pytest.mark.parametrize("data", load_test_cases("tests/test_parser_simple.json"))
    def test_parser_simple(self, data):
        """Test simple cases of ingredient sentences that the regex parser should have
        no issues getting correct

        Parameters
        ----------
        data : Dict[str, Dict[str, str]]
            Dictionary of sample data with the following keys
                sentence - the input sentence
                labels - the correct labels the parser should return
        """
        sentence = data["sentence"]
        true_labels = data["labels"]
        parsed = parse_ingredient_regex(sentence)

        # parse_ingredient returns a dict with more keys than just the labels
        # so iterate through each label in true_labels and only check them.
        for key in true_labels:
            assert parsed[key] == true_labels[key]

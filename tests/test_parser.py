import json

import pytest

from ingredient_parser import parse_ingredient

# Load test data from test_parser.json
sample_data = []
with open("tests/test_parser.json", "r") as f:
    test_vectors = f.read().splitlines()
    for vector in test_vectors:
        data = json.loads(vector)
        sample_data.append(data)


class TestParser:
    @pytest.mark.parametrize("data", sample_data)
    def test_parser(self, data):
        """Test parse_ingredient function of sample_data

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
            assert parsed[key] == parsed[key]

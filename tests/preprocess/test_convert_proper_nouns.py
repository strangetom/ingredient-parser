import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor(".", custom_units={})


class TestPreProcessor_convert_proper_nouns:
    def test_can_sizes(self, p: PreProcessor):

        # number 1
        input_sentences_dict = {
            "1 number_one_can tomato puree": [
                "1 number 1 can tomato puree",
                "1 no 1 can tomato puree",
                "1 no. 1 can tomato puree",
            ],
            "1 number_two_can tomato puree": [
                "1 number 2 can tomato puree",
                "1 no 2 can tomato puree",
                "1 no. 2 can tomato puree",
            ],
            "1 number_three_can tomato puree": [
                "1 number 3 can tomato puree",
                "1 no 3 can tomato puree",
                "1 no. 3 can tomato puree",
            ],
            "1 number_ten_can tomato puree": [
                "1 number 10 can tomato puree",
                "1 no 10 can tomato puree",
                "1 no. 10 can tomato puree",
            ],
            "1 number_two_half_can tomato puree": [
                "1 number 2.5 can tomato puree",
                "1 number 2#1$2 can tomato puree",
                "1 no 2.5 can tomato puree",
                "1 no. 2.5 can tomato puree",
            ],
            "1 number_three_hundred_can tomato puree": [
                "1 number 300 can tomato puree",
                "1 no 300 can tomato puree",
                "1 no. 300 can tomato puree",
            ],
        }

        for output_sentence, input_sentences in input_sentences_dict.items():
            for sentence in input_sentences:
                assert p._convert_unit_phrases(sentence) == output_sentence, (
                    f"{sentence} was not converted to {output_sentence}"
                )
        # number 300

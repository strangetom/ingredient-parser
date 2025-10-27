import pytest

from ingredient_parser.en import PostProcessor


@pytest.fixture
def p_mulitple_names():
    """Define a PostProcessor object with discard_isolated_stop_words set to False
    to use for testing the PostProcessor class methods.

    This sentence has the name split by a token with a non-name label.
    """
    sentence = "2 cups beef or chicken stock"
    tokens = ["2", "cup", "beef", "or", "chicken", "stock"]
    pos_tags = ["CD", "NNS", "NN", "CC", "NN", "NN"]
    labels = ["QTY", "UNIT", "NAME_VAR", "NAME_SEP", "NAME_VAR", "B_NAME_TOK"]
    scores = [
        0.9999916198218641,
        0.9999194173062287,
        0.9455381513097211,
        0.9996235422364157,
        0.9649807293441203,
        0.9668959628659927,
    ]

    return PostProcessor(
        sentence,
        tokens,
        pos_tags,
        labels,
        scores,
        discard_isolated_stop_words=False,
        foundation_foods=True,
    )


class TestPostProcessor_ordering:
    def test_split_ingredient_name(self, p_mulitple_names):
        """
        Test that the foundation foods matched to each ingredient name have mapped to
        the correct index in the name list.
        """
        assert p_mulitple_names.parsed.name[0].text == "beef stock"
        assert p_mulitple_names.parsed.foundation_foods[0].fdc_id == 172883
        assert p_mulitple_names.parsed.foundation_foods[0].name_index == 0

        assert p_mulitple_names.parsed.name[1].text == "chicken stock"
        assert p_mulitple_names.parsed.foundation_foods[1].fdc_id == 172884
        assert p_mulitple_names.parsed.foundation_foods[1].name_index == 1

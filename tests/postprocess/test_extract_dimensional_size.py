from ingredient_parser.en import PostProcessor
from ingredient_parser.en._utils import ingredient_amount_factory


class TestPostProcessor_extract_dimensional_size:
    def test_skips_when_no_name_tokens(self):
        """Without a NAME token the dimensional measurement is more likely a
        primary measurement, so the transformation is skipped."""
        amounts = [
            ingredient_amount_factory(
                quantity="6",
                unit="inch",
                text="6 inches",
                confidence=0.9,
                starting_index=0,
            ),
        ]
        p = PostProcessor(
            "6-inch",
            ["6", "inch"],
            ["CD", "NN"],
            ["QTY", "UNIT"],
            [0.9] * 2,
            custom_units={},
        )
        result_amounts, size = p._extract_dimensional_size(amounts)

        assert result_amounts == amounts
        assert size is None

    def test_transforms_multi_word_dimensional_unit(self):
        """When the fallback pattern joins multiple UNIT tokens into a single
        amount (e.g. "inches strips"), the transformation still recognises
        the leading dimensional word."""
        amounts = [
            ingredient_amount_factory(
                quantity="3",
                unit="inches strips",
                text="3 inches strips",
                confidence=0.9,
                starting_index=0,
            ),
        ]
        p = PostProcessor(
            "3-inch strip lemon zest",
            ["3", "inch", "strip", "lemon", "zest"],
            ["CD", "NN", "NN", "NN", "NN"],
            ["QTY", "UNIT", "UNIT", "B_NAME_TOK", "I_NAME_TOK"],
            [0.9] * 5,
            custom_units={},
        )
        result_amounts, size = p._extract_dimensional_size(amounts)

        assert len(result_amounts) == 1
        assert result_amounts[0].quantity == 1
        assert size.text == "3 inches strips"

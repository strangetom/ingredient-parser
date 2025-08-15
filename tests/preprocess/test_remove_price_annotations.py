import pytest

from ingredient_parser.en import PreProcessor


@pytest.fixture
def p():
    """Define an empty PreProcessor object to use for testing the PreProcessor
    class methods.
    """
    return PreProcessor("")


class TestPreProcessor_remove_price_annotations:
    def test_remove_dollar_price(self, p):
        input_sentence = "1 cup flour ($0.20)"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour "

    def test_remove_pound_price(self, p):
        input_sentence = "2 eggs (£1.50)"
        assert p._remove_price_annotations(input_sentence) == "2 eggs "

    def test_remove_euro_price(self, p):
        input_sentence = "3 tomatoes (€2.00)"
        assert p._remove_price_annotations(input_sentence) == "3 tomatoes "

    def test_remove_yen_price(self, p):
        input_sentence = "1 onion (¥100)"
        assert p._remove_price_annotations(input_sentence) == "1 onion "

    def test_remove_rupee_price(self, p):
        input_sentence = "1 potato (₹10.50)"
        assert p._remove_price_annotations(input_sentence) == "1 potato "

    def test_multiple_prices(self, p):
        input_sentence = "1 apple ($0.50) and 1 orange (£0.30)"
        assert p._remove_price_annotations(input_sentence) == "1 apple  and 1 orange "

    def test_no_price_annotation(self, p):
        input_sentence = "1 cup sugar"
        assert p._remove_price_annotations(input_sentence) == "1 cup sugar"

    def test_malformed_price_annotation(self, p):
        input_sentence = "1 cup flour ($0.20"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour ($0.20"

    def test_price_with_comma(self, p):
        input_sentence = "1 steak (€1,200.00)"
        assert p._remove_price_annotations(input_sentence) == "1 steak "

    def test_price_with_multiple_decimals(self, p):
        input_sentence = "1 cheese ($1.99) and 1 bread ($2.49)"
        assert p._remove_price_annotations(input_sentence) == "1 cheese  and 1 bread "

    def test_price_annotation_at_start(self, p):
        input_sentence = "($0.20) 1 cup flour"
        assert p._remove_price_annotations(input_sentence) == " 1 cup flour"

    def test_price_annotation_in_middle(self, p):
        input_sentence = "1 cup ($0.20) flour"
        assert p._remove_price_annotations(input_sentence) == "1 cup  flour"

    def test_price_annotation_at_end(self, p):
        input_sentence = "1 cup flour ($0.20)"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour "

    def test_price_annotation_with_leading_space(self, p):
        input_sentence = "1 cup flour ( $0.20)"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour "

    def test_price_annotation_with_inner_spaces(self, p):
        input_sentence = "1 cup flour ( $ 0.20 )"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour "

    def test_price_annotation_with_multiple_spaces(self, p):
        input_sentence = "1 cup flour (  $  0.20  )"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour "

    def test_price_annotation_with_tab_spaces(self, p):
        input_sentence = "1 cup flour (\t$0.20\t)"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour "

    def test_price_annotation_with_mixed_whitespace(self, p):
        input_sentence = "1 cup flour ( \t $ 0.20  )"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour "

    def test_price_annotation_with_asterisk_suffix(self, p):
        input_sentence = "1 cup flour ($0.20**)"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour "

    def test_non_price_parenthetical_remains(self, p):
        input_sentence = "1 cup flour (organic)"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour (organic)"

    def test_multiple_non_price_parentheticals(self, p):
        input_sentence = "2 eggs (free-range) (large)"
        assert (
            p._remove_price_annotations(input_sentence) == "2 eggs (free-range) (large)"
        )

    def test_mixed_price_and_non_price_parentheticals(self, p):
        input_sentence = "1 cup flour ($0.20) (organic)"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour  (organic)"

    def test_non_price_parenthetical_with_spaces(self, p):
        input_sentence = "1 cup flour ( see note )"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour ( see note )"

    def test_non_price_parenthetical_with_numbers(self, p):
        input_sentence = "1 cup flour (2nd batch)"
        assert p._remove_price_annotations(input_sentence) == "1 cup flour (2nd batch)"

import pytest

from ingredient_parser import parse_ingredient


class Test_prepared_ingredient:
    @pytest.mark.model_dependent
    def test_no_preparation(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is False
        """
        sentence = "3 cups (750 g) flour"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert not amount.PREPARED_INGREDIENT

    @pytest.mark.model_dependent
    def test_preparation_between_amount_and_name(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is True
        """
        sentence = "3 cups (750 g) sifted flour"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    @pytest.mark.model_dependent
    def test_preparation_between_name_and_amount(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is True
        """
        sentence = "Onion, finely chopped (about 1 cup)"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    @pytest.mark.model_dependent
    def test_preparation_after_amount_and_name(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is False
        """
        sentence = "3 cups (750 g) flour, sifted"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert not amount.PREPARED_INGREDIENT

    @pytest.mark.model_dependent
    def test_multiple_names(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is True
        """
        sentence = "3 cups (750 ml) diced red or yellow pepper"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

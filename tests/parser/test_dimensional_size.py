import pytest

from ingredient_parser import parse_ingredient


class TestParser_dimensional_size:
    @pytest.mark.parametrize(
        ("sentence", "expected_size_prefix"),
        [
            ("6-inch tortilla", "6 inch"),
            ("5cm cinnamon stick", "5 cm"),
            ("5 cm cinnamon stick", "5 cm"),
            ("1 to 2-inch cinnamon stick", "1-2 inch"),
        ],
    )
    def test_no_count(self, sentence, expected_size_prefix):
        """Dimensional measurement with no leading count produces an implied
        count of 1 and the measurement becomes a size descriptor."""
        parsed = parse_ingredient(sentence)

        assert len(parsed.amount) == 1
        assert parsed.amount[0].quantity == 1
        assert str(parsed.amount[0].unit) == ""
        assert parsed.size is not None
        assert parsed.size.text.startswith(expected_size_prefix)

    @pytest.mark.parametrize(
        ("sentence", "expected_qty", "expected_unit", "expected_size_prefix"),
        [
            ("2 6-inch flour tortillas", 2, "", "6 inch"),
            ("1 3-inch piece fresh ginger", 1, "piece", "3 inch"),
            ("1/2-inch piece fresh ginger", 1, "piece", "1/2 inch"),
        ],
    )
    def test_with_non_dimensional_primary(
        self, sentence, expected_qty, expected_unit, expected_size_prefix
    ):
        """A non-dimensional primary amount (count, or count + container unit
        like "piece") is preserved; only the dimensional component moves to
        the size descriptor."""
        parsed = parse_ingredient(sentence)

        assert len(parsed.amount) == 1
        assert parsed.amount[0].quantity == expected_qty
        assert str(parsed.amount[0].unit) == expected_unit
        assert parsed.size is not None
        assert parsed.size.text.startswith(expected_size_prefix)

    def test_merges_with_size_adjective(self):
        """A SIZE-labelled adjective and a dimensional measurement both
        populate the size field, joined by a comma."""
        parsed = parse_ingredient("large 6-inch tortilla")

        assert parsed.size is not None
        assert "large" in parsed.size.text
        assert "inch" in parsed.size.text


class TestParser_dimensional_size_not_transformed:
    """Inputs that must NOT trigger the dimensional-size transformation."""

    @pytest.mark.parametrize(
        ("sentence", "expected_qty", "expected_unit"),
        [
            # Pluralised form with space indicates primary length measurement
            ("12 inches cheesecloth", 12, "inch"),
            ("6 inches of fresh ginger", 6, "inch"),
            # foot/feet excluded (commonly primary length: twine, cheesecloth)
            ("2 feet butcher twine", 2, "foot"),
        ],
    )
    def test_primary_length_preserved(self, sentence, expected_qty, expected_unit):
        parsed = parse_ingredient(sentence)

        assert parsed.amount[0].quantity == expected_qty
        assert str(parsed.amount[0].unit) == expected_unit
        assert parsed.size is None

    def test_container_pattern_preserved(self):
        """Compound container patterns produce two structured amounts, not a
        dimensional-size transformation."""
        parsed = parse_ingredient("15 ounce can black beans")

        assert len(parsed.amount) == 2
        assert str(parsed.amount[0].unit) == "can"
        assert str(parsed.amount[1].unit) == "ounce"
        assert parsed.size is None

    def test_prep_inch_preserved(self):
        """Inch used in a preparation phrase (PREP-labelled) is unaffected."""
        parsed = parse_ingredient("1 pound chicken, cut into 2-inch cubes")

        assert str(parsed.amount[0].unit) == "pound"
        assert parsed.size is None
        assert parsed.preparation is not None

    def test_parenthesized_dimensional_preserved(self):
        """Parenthesized dimensional forms go through the COMMENT path and
        are not transformed."""
        parsed = parse_ingredient("5 (8 inch) flour tortillas")

        assert len(parsed.amount) == 1
        assert parsed.amount[0].quantity == 5

    def test_size_adjective_preserved(self):
        """SIZE-labelled adjectives on non-dimensional inputs are unaffected."""
        parsed = parse_ingredient("3 large eggs")

        assert parsed.amount[0].quantity == 3
        assert parsed.size is not None
        assert parsed.size.text == "large"

import pytest

from ingredient_parser import parse_ingredient


class TestParserArgumentValidation:
    def test_unsupported_language(self):
        """
        Test that a ValueError is raised when an unsupported language is specified
        """
        with pytest.raises(ValueError, match="Unsupported language"):
            _ = parse_ingredient("1 apple", lang="es")

    def test_imperial_units_warning(self):
        """
        Test that a DeprecationWarning is raised when imperial_units argument is
        specified.
        """
        with pytest.warns(
            DeprecationWarning, match="imperial_units=True argument is deprecated."
        ):
            _ = parse_ingredient("1 apple", imperial_units=True)

    def test_unsupported_volumetric_units_system(self):
        """
        Test that a ValueError is raised when an unsupported volumetric units system is
        specified.
        """
        with pytest.raises(ValueError, match="Unsupported volumetric_units_system"):
            _ = parse_ingredient("1 apple", volumetric_units_system="uk")

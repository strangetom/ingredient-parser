#!/usr/bin/env python3

import warnings
from collections.abc import Iterable

from ingredient_parser.en import inspect_parser_en, parse_ingredient_en

from . import SUPPORTED_LANGUAGES
from .dataclasses import ParsedIngredient, ParserDebugInfo

warnings.simplefilter("always", DeprecationWarning)


SUPPORTED_VOLUMEETRIC_UNITS_SYSTEMS = {
    "us_customary",
    "imperial",
    "metric",
    "australian",
    "japanese",
}


def parse_ingredient(
    sentence: str,
    lang: str = "en",
    separate_names: bool = True,
    discard_isolated_stop_words: bool = True,
    expect_name_in_output: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
    volumetric_units_system: str = "us_customary",
    foundation_foods: bool = False,
    custom_units: dict[str, str] | None = None,
) -> ParsedIngredient:
    """Parse an ingredient sentence to return structured data.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse.
    lang : str
        Language of sentence.
        Currently supported options are: en.
    separate_names : bool, optional
        If True and the sentence contains multiple alternative ingredients, return an
        IngredientText object for each ingredient name, otherwise return a single
        IngredientText object.
        Default is True.
    discard_isolated_stop_words : bool, optional
        If True, any isolated stop words in the name, preparation, or comment fields
        are discarded.
        Default is True.
    expect_name_in_output : bool, optional
        If True, if the model doesn't label any words in the sentence as the name,
        fallback to selecting the most likely name from all tokens even though the
        model gives it a different label. Note that this does guarantee the output
        contains a name.
        Default is True.
    string_units : bool, optional
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Default is False.
    imperial_units : bool, optional
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.

        .. deprecated:: v2.5.0

            Use ``volumetric_units_system="imperial"`` for the same functionality.

    volumetric_units_system : str, optional
        Sets the units system for volumetric measurements, like "cup" or "tablespoon".
        Available options are "us_customary" (default), "imperial", "metric",
        "australian", "japanese".
        This has no effect if string_units=True.

        .. versionadded:: v2.5.0

    foundation_foods : bool, optional
        If True, extract foundation foods from ingredient name. Foundation foods are
        the fundamental foods without any descriptive terms, e.g. 'cucumber' instead
        of 'organic cucumber'.
        Default is False.
    custom_units : dict[str, str] | None, optional
        Provide custom units to aid the parser in identifying units.
        The custom units should be provided as a dict of plural: singular pairs.
        If a unit does not have a plural form, provide the singular form as the key for
        the pair.
        The units should not start with a capital letter, but may contain capital
        letters at other positions.

        .. versionadded:: v2.6.0

    Returns
    -------
    ParsedIngredient
        ParsedIngredient object of structured data parsed from input string.
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f'Unsupported language "{lang}"')

    if imperial_units:
        warnings.warn(
            (
                "imperial_units=True argument is deprecated. "
                "Use volumetric_units_system='imperial'"
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        volumetric_units_system = "imperial"

    if volumetric_units_system not in SUPPORTED_VOLUMEETRIC_UNITS_SYSTEMS:
        raise ValueError(
            f'Unsupported volumetric_units_system "{volumetric_units_system}"'
        )

    match lang:
        case "en":
            return parse_ingredient_en(
                sentence,
                separate_names=separate_names,
                discard_isolated_stop_words=discard_isolated_stop_words,
                expect_name_in_output=expect_name_in_output,
                string_units=string_units,
                volumetric_units_system=volumetric_units_system,
                foundation_foods=foundation_foods,
                custom_units=custom_units,
            )
        case _:
            raise ValueError(f'Unrecognised value "{lang}"')


def parse_multiple_ingredients(
    sentences: Iterable[str],
    lang: str = "en",
    separate_names: bool = True,
    discard_isolated_stop_words: bool = True,
    expect_name_in_output: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
    volumetric_units_system: str = "us",
    foundation_foods: bool = False,
    custom_units: dict[str, str] | None = None,
) -> list[ParsedIngredient]:
    """Parse multiple ingredient sentences.

    This function accepts a list of sentences and returns a list of ParsedIngredient
    objects.

    Parameters
    ----------
    sentences : Iterable[str]
        Iterable of sentences to parse.
    lang : str
        Language of sentence.
        Currently supported options are: en.
    separate_names : bool, optional
        If True and the sentence contains multiple alternative ingredients, return an
        IngredientText object for each ingredient name, otherwise return a single
        IngredientText object.
        Default is True.
    discard_isolated_stop_words : bool, optional
        If True, any isolated stop words in the name, preparation, or comment fields
        are discarded.
        Default is True.
    expect_name_in_output : bool, optional
        If True, if the model doesn't label any words in the sentence as the name,
        fallback to selecting the most likely name from all tokens even though the
        model gives it a different label. Note that this does guarantee the output
        contains a name.
        Default is True.
    string_units : bool
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Default is False.
    imperial_units : bool
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.

        .. deprecated:: v2.5.0

            Use ``volumetric_units_system="imperial"`` for the same functionality.

    volumetric_units_system : str, optional
        Sets the units system for volumetric measurements, like "cup" or "tablespoon".
        Available options are "us_customary" (default), "imperial", "metric",
        "australian", "japanese".
        This has no effect if string_units=True.

        .. versionadded:: v2.5.0

    foundation_foods : bool, optional
        If True, extract foundation foods from ingredient name. Foundation foods are
        the fundamental foods without any descriptive terms, e.g. 'cucumber' instead
        of 'organic cucumber'.
        Default is False.
    custom_units : dict[str, str] | None, optional
        Provide custom units to aid the parser in identifying units.
        The custom units should be provided as a dict of plural: singular pairs.
        If a unit does not have a plural form, provide the singular form as the key for
        the pair.
        The units should not start with a capital letter, but may contain capital
        letters at other positions.

        .. versionadded:: v2.6.0

    Returns
    -------
    list[ParsedIngredient]
        List of ParsedIngredient objects of structured data parsed from input sentences.
    """
    return [
        parse_ingredient(
            sentence,
            lang=lang,
            separate_names=separate_names,
            discard_isolated_stop_words=discard_isolated_stop_words,
            expect_name_in_output=expect_name_in_output,
            string_units=string_units,
            imperial_units=imperial_units,
            volumetric_units_system=volumetric_units_system,
            foundation_foods=foundation_foods,
            custom_units=custom_units,
        )
        for sentence in sentences
    ]


def inspect_parser(
    sentence: str,
    lang: str = "en",
    separate_names: bool = True,
    discard_isolated_stop_words: bool = True,
    expect_name_in_output: bool = True,
    string_units: bool = False,
    imperial_units: bool = False,
    volumetric_units_system: str = "us_customary",
    foundation_foods: bool = False,
    custom_units: dict[str, str] | None = None,
) -> ParserDebugInfo:
    """Return intermediate objects generated during parsing for inspection.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to parse.
    lang : str
        Language of sentence.
        Currently supported options are: en.
    separate_names : bool, optional
        If True and the sentence contains multiple alternative ingredients, return an
        IngredientText object for each ingredient name, otherwise return a single
        IngredientText object.
        Default is True.
    discard_isolated_stop_words : bool, optional
        If True, any isolated stop words in the name, preparation, or comment fields
        are discarded.
        Default is True.
    expect_name_in_output : bool, optional
        If True, if the model doesn't label any words in the sentence as the name,
        fallback to selecting the most likely name from all tokens even though the
        model gives it a different label. Note that this does guarantee the output
        contains a name.
        Default is True.
    string_units : bool
        If True, return all IngredientAmount units as strings.
        If False, convert IngredientAmount units to pint.Unit objects where possible.
        Default is False.
    imperial_units : bool
        If True, use imperial units instead of US customary units for pint.Unit objects
        for the the following units: fluid ounce, cup, pint, quart, gallon.
        Default is False, which results in US customary units being used.
        This has no effect if string_units=True.

        .. deprecated:: v2.5.0

            Use ``volumetric_units_system="imperial"`` for the same functionality.

    volumetric_units_system : str, optional
        Sets the units system for volumetric measurements, like "cup" or "tablespoon".
        Available options are "us_customary" (default), "imperial", "metric",
        "australian", "japanese".
        This has no effect if string_units=True.

        .. versionadded:: v2.5.0

    foundation_foods : bool, optional
        If True, extract foundation foods from ingredient name. Foundation foods are
        the fundamental foods without any descriptive terms, e.g. 'cucumber' instead
        of 'organic cucumber'.
        Default is False.
    custom_units : dict[str, str] | None, optional
        Provide custom units to aid the parser in identifying units.
        The custom units should be provided as a dict of plural: singular pairs.
        If a unit does not have a plural form, provide the singular form as the key for
        the pair.
        The units should not start with a capital letter, but may contain capital
        letters at other positions.

        .. versionadded:: v2.6.0

    Returns
    -------
    ParserDebugInfo
        ParserDebugInfo object containing the PreProcessor object, PostProcessor
        object and Tagger.
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f'Unsupported language "{lang}"')

    if imperial_units:
        warnings.warn(
            (
                "imperial_units=True argument is deprecated. "
                "Use volumetric_units_system='imperal'"
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        volumetric_units_system = "imperial"

    if volumetric_units_system not in SUPPORTED_VOLUMEETRIC_UNITS_SYSTEMS:
        raise ValueError(
            f'Unsupported volumetric_units_system "{volumetric_units_system}"'
        )

    match lang:
        case "en":
            return inspect_parser_en(
                sentence,
                separate_names=separate_names,
                discard_isolated_stop_words=discard_isolated_stop_words,
                expect_name_in_output=expect_name_in_output,
                string_units=string_units,
                volumetric_units_system=volumetric_units_system,
                foundation_foods=foundation_foods,
                custom_units=custom_units,
            )
        case _:
            raise ValueError(f'Unrecognised value "{lang}"')

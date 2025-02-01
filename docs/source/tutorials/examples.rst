Examples
========

Multiple ingredient sentences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`parse_multiple_ingredients <ingredient_parser.parsers.parse_multiple_ingredients>` function is provided for convenience. It accepts a list of ingredient sentences as it's input and returns a list of :class:`ParsedIngredient <ingredient_parser.dataclasses.ParsedIngredient>` objects with the parsed information. It has the same optional arguments as :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>`.

.. code:: python

    >>> from ingredient_parser import parse_multiple_ingredients
    >>> sentences = [
        "3 lime wedges, for serving",
        "2 tablespoons extra-virgin olive oil",
        "2 large garlic cloves, finely grated",
    ]
    >>> parse_multiple_ingredients(sentences)
    [
        ParsedIngredient(
            name=IngredientText(text='lime wedges',
                                confidence=0.894776),
            size=None,
            amount=[IngredientAmount(quantity=Fraction(3, 1),
                                     quantity_max=Fraction(3, 1),
                                     unit="",
                                     text='3',
                                     confidence=0.999499,,
                                     APPROXIMATE=False,
                                     SINGULAR=False,
                                     RANGE=False,
                                     MULTIPLIER=False,
                                     PREPARED_INGREDIENT=False)],
            preparation=None,
            comment=None,
            purpose=IngredientText(text='for serving',
                                   confidence=0.999462),
            foundation_foods=[],
            sentence='3 lime wedges, for serving'
        ),
        ParsedIngredient(
            name=IngredientText(text='extra-virgin olive oil',
                                confidence=0.996531),
            size=None,
            amount=[IngredientAmount(quantity=Fraction(2, 1),
                                     quantity_max=Fraction(2, 1),
                                     unit=<Unit('tablespoon')>,
                                     text='2 tablespoons',
                                     confidence=0.999783,
                                     starting_index=0,
                                     APPROXIMATE=False,
                                     SINGULAR=False,
                                     RANGE=False,
                                     MULTIPLIER=False,
                                     PREPARED_INGREDIENT=False)],
            preparation=None,
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence='2 tablespoons extra-virgin olive oil'
        ),
        ParsedIngredient(
            name=IngredientText(text='garlic',
                                confidence=0.992021),
            size=None,
            amount=[IngredientAmount(quantity=Fraction(2, 1),
                                     quantity_max=Fraction(2, 1),
                                     unit='large cloves',
                                     text='2 large cloves',
                                     confidence=0.975306,
                                     starting_index=0,
                                     APPROXIMATE=False,
                                     SINGULAR=False,
                                     RANGE=False,
                                     MULTIPLIER=False,
                                     PREPARED_INGREDIENT=False)],
            preparation=IngredientText(text='finely grated',
                                       confidence=0.997482),
            comment=None,
            purpose=None,
            foundation_foods=[],
            sentence='2 large garlic cloves, finely grated'
        )
    ]

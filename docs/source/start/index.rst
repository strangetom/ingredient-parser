Getting Started
===============

The Ingredient Parser package is a Python package for parsing structured information from recipe ingredient sentences.

Given a recipe ingredient such as

    200 g plain flour, sifted

we want to extract information about the quantity, units, name, preparation and comment. For the example above:

.. list-table::

    * - Quantity
      - Unit
      - Name
      - Preparation
      - Comment
    * - 200
      - g
      - plain flour
      - sifted
      -

This package uses a Conditional Random Fields model trained on 60,000 example ingredient sentences. The model has been trained on data from three sources:

* The New York Times released a large dataset when they did some similar work in 2015 in their `Ingredient Phrase Tagger <https://github.com/nytimes/ingredient-phrase-tagger>`_ repository.
* A dump of recipes taken from Cookstr in 2017.
* A dump of recipe taken from BBC Food in 2017.

More information on how the model is trained and the output interpreted can be found in the :doc:`Model Guide </guide/index>`.

Installation
^^^^^^^^^^^^

You can install Ingredient Parser from PyPi with ``pip``:

.. code::

    $ python -m pip install ingredient_parser_nlp

This will download and install the package and it's dependencies:

* `NLTK <https://www.nltk.org/>`_
* `python-crfsuite <https://python-crfsuite.readthedocs.io/en/latest/>`_
* `pint <https://pint.readthedocs.io/en/stable/>`_

Usage
^^^^^

The primary functionality of this package is provided by the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function.

The :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function takes an ingredient sentence and return the structured data extracted from it.

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("3 pounds pork shoulder, cut into 2-inch chunks")
    ParsedIngredient(
        name=IngredientText(text='pork shoulder',
                            confidence=0.999773),
        size=None,
        amount=[IngredientAmount(quantity=3.0,
                                 quantity_max=3.0,
                                 unit=<Unit('pound')>,
                                 text='3 pounds',
                                 confidence=0.999739,
                                 starting_index=0,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False))],
        preparation=IngredientText(text='cut into 2 inch chunks',
                                   confidence=0.999193),
        comment=None,
        purpose=None,
        sentence='3 pounds pork shoulder, cut into 2-inch chunks'
    )


The returned :class:`ParsedIngredient <ingredient_parser.dataclasses.ParsedIngredient>` object contains the following fields:

+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field           | Description                                                                                                                                                          |
+=================+======================================================================================================================================================================+
| **name**        | The name of the ingredient sentence, or ``None``.                                                                                                                    |
+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **size**        | A size modifier for the ingredient, such as small or large, or ``None``.                                                                                             |
|                 |                                                                                                                                                                      |
|                 | This size modifier only applies to the ingredient, not the unit. For example, *1 large pinch of salt* would have the unit as *large pinch* and size of ``None``.     |
+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **amount**      | The amounts parsed from the sentence. Each amount has a quantity and a unit, plus optional flags indicating if the amount is approximate or is for a singular item.  |
|                 |                                                                                                                                                                      |
|                 | By default the unit field is a :class:`pint.Unit` object, if the unit can be matched to a unit in the pint unit registry.                                            |
+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **preparation** | The preparation notes for the ingredient. This is a string, or ``None`` is there are no preparation notes for the ingredient.                                        |
+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **comment**     | The comment from the ingredient sentence. This is a string, or ``None`` if there is no comment.                                                                      |
+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **purpose**     | The purpose of the ingredient. This is a string, or ``None`` if there is no purpose.                                                                                 |
+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **sentence**    | The input sentence passed to the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function.                                                     |
+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Each of the fields (except sentence) has a confidence value associated with it. This is a value between 0 and 1, where 0 represents no confidence and 1 represent full confidence. This is the confidence that the natural language model has that the given label is correct, averaged across all tokens that contribute to that particular field.

Optional parameters
~~~~~~~~~~~~~~~~~~~

The :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function has the following optional boolean parameters:

- ``discard_isolated_stop_words``

  If True (default), then any stop words that appear in isolation in the name, preparation, size or comment fields are discarded. If False, then all words from the input sentence are retained in the parsed output. For example:

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("2 tbsp of olive oil", discard_isolated_stop_words=True) # default
    ParsedIngredient(
        name=IngredientText(text='olive oil',
                            confidence=0.990498),
        size=None,
        amount=[IngredientAmount(quantity=2.0,
                                 quantity_max=2.0,
                                 unit=<Unit('tablespoon')>,
                                 text='2 tbsps',
                                 confidence=0.999773,
                                 starting_index=0,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False)],
        preparation=None,
        comment=None,
        purpose=None,
        sentence='2 tbsp of olive oil'
    )
    >>> parse_ingredient("2 tbsp of olive oil", discard_isolated_stop_words=False)
    ParsedIngredient(
        name=IngredientText(text='olive oil',
                            confidence=0.990498),
        size=None,
        amount=[IngredientAmount(quantity=2.0,
                                 quantity_max=2.0,
                                 unit=<Unit('tablespoon')>,
                                 text='2 tbsps',
                                 confidence=0.999773,
                                 starting_index=0,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False)],
        preparation=None,
        purpose=None,
        comment=IngredientText(text='of',
                               confidence=0.915292),  # <-- Note the difference here
        sentence='2 tbsp of olive oil'
    )

- ``expect_name_in_output``

  Sometimes the model won't label any tokens as NAME, often due to the sentence structure being unusual.

  If True (default), fallback to guessing the ingredient name based on the token(s) most likely to have the NAME label compared to the other tokens (above a minimum confidence threshold), even though the model thinks those tokens are more likely to have a different label. This does not guarantee that output contains a name, particularly in cases where the model is very confident in the labels it has assigned.

  If False, the returned :class:`ParsedIngredient` object will have the name field set to ``None`` in these cases.

- ``string_units``

  If True, units in the :class:`IngredientAmount <ingredient_parser.dataclasses.IngredientAmount>` objects are returned as strings. The default is False, where units will be :class:`pint.Unit` objects.

- ``imperial_unts``

  If True, then any :class:`pint.Unit` objects for fluid ounces, cups, pints, quarts or gallons will be the Imperial measurement. The default is False, where the US customary measurements are used.

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
            amount=[IngredientAmount(quantity='3.0',
                                     quantity_max=3.0,
                                     unit="",
                                     text='3',
                                     confidence=0.999499,,
                                     APPROXIMATE=False,
                                     SINGULAR=False,
                                     RANGE=False,
                                     MULTIPLIER=False)],
            preparation=None,
            comment=None,
            purpose=IngredientText(text='for serving',
                                   confidence=0.999462),
            sentence='3 lime wedges, for serving'
        ),
        ParsedIngredient(
            name=IngredientText(text='extra-virgin olive oil',
                                confidence=0.996531),
            size=None,
            amount=[IngredientAmount(quantity=2.0,
                                     quantity_max=2.0,
                                     unit=<Unit('tablespoon')>,
                                     text='2 tablespoons',
                                     confidence=0.999783,
                                     starting_index=0,
                                     APPROXIMATE=False,
                                     SINGULAR=False,
                                     RANGE=False,
                                     MULTIPLIER=False)],
            preparation=None,
            comment=None,
            purpose=None,
            sentence='2 tablespoons extra-virgin olive oil'
        ),
        ParsedIngredient(
            name=IngredientText(text='garlic',
                                confidence=0.992021),
            size=None,
            amount=[IngredientAmount(quantity=2.0,
                                     quantity_max=2.0,
                                     unit='large cloves',
                                     text='2 large cloves',
                                     confidence=0.975306,
                                     starting_index=0,
                                     APPROXIMATE=False,
                                     SINGULAR=False,
                                     RANGE=False,
                                     MULTIPLIER=False)],
            preparation=IngredientText(text='finely grated',
                                       confidence=0.997482),
            comment=None,
            purpose=None,
            sentence='2 large garlic cloves, finely grated'
        )
    ]

.. _reference-tutorials-index:

Getting Started
===============

The Ingredient Parser package is a Python package for parsing structured information from recipe ingredient sentences.

The following parts of an ingredient sentence can be extracted:

+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field                | Description                                                                                                                                                          |
+======================+======================================================================================================================================================================+
| **name**             | The name of the ingredient, or names if multiple names are given.                                                                                                    |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **size**             | A size modifier for the ingredient, such as small or large.                                                                                                          |
|                      |                                                                                                                                                                      |
|                      | This size modifier only applies to the ingredient name, not the unit.                                                                                                |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **amount**           | The amounts parsed from the sentence. Each amount has a quantity and a unit, plus additional flags that provide extra information about the amount.                  |
|                      |                                                                                                                                                                      |
|                      | Where possible units are given as :class:`pint.Unit` objects, which allows for convenient programmatic manipulation such as conversion to other units.               |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **preparation**      | The preparation notes for the ingredient.                                                                                                                            |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **comment**          | The comment from the ingredient sentence, such as examples or asides.                                                                                                |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **purpose**          | The purpose of the ingredient, such as for garnish.                                                                                                                  |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **foundation foods** | The core or fundamental item of an ingredient sentence, without any other words like descriptive adjectives or brand names.                                          |
|                      | See :doc:`Foundation Foods </explanation/foundation>` for more details.                                                                                              |
|                      |                                                                                                                                                                      |
|                      | Note that this is not extracted by default, but can be enabled using the ``foundation_foods`` keyword argument.                                                      |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Installation
^^^^^^^^^^^^

You can install Ingredient Parser from PyPi with ``pip``:

.. code::

    $ python -m pip install ingredient_parser_nlp

Ingredient Parser depends on the following

* `python-crfsuite <https://python-crfsuite.readthedocs.io/en/latest/>`_
* `NLTK <https://www.nltk.org/>`_
* `Pint <https://pint.readthedocs.io/en/stable/>`_
* `Numpy <https://numpy.org/>`_

.. note::

    To use the companion web app, a.k.a. **webtools**, :ref:`follow the steps in this section <reference-tutorials-web-app>`.


Usage
^^^^^

The primary functionality of this package is provided by the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function.

This function takes a single ingredient sentence and returns a :class:`ParsedIngredient <ingredient_parser.dataclasses.ParsedIngredient>` object containing the extracted information.

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("3 pounds pork shoulder, cut into 2-inch chunks")
    ParsedIngredient(
        name=[IngredientText(text='pork shoulder',
                             confidence=0.996256,
                             starting_index=2)],
        size=None,
        amount=[IngredientAmount(quantity=Fraction(3, 1),
                                 quantity_max=Fraction(3, 1),
                                 unit=<Unit('pound')>,
                                 text='3 pounds',
                                 confidence=0.999829,
                                 starting_index=0,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False,
                                 PREPARED_INGREDIENT=False)],
        preparation=IngredientText(text='cut into 2 inch chunks',
                                   confidence=0.999803,
                                   starting_index=5),
        comment=None,
        purpose=None,
        foundation_foods=[],
        sentence='3 pounds pork shoulder, cut into 2-inch chunks'
    )

Each of the fields (except sentence) has a confidence value associated with it. This is a value between 0 and 1, where 0 represents no confidence and 1 represent full confidence. This is the confidence that the natural language model has that the given label is correct, averaged across all tokens that contribute to that particular field.

.. toctree::
   :maxdepth: 1
   :hidden:

   Options <options>
   Examples <examples>
   Web app <webtools>

Getting Started
===============

The Ingredient Parser package is a Python package for parsing structured information out of recipe ingredient sentences.

Given a recipe ingredient such as 

    200 g plain flour, sifted

we want to extract information about the quantity, units, name and comment. For the example above:

.. list-table::

    * - Quantity
      - Unit
      - Name
      - Comment
    * - 200
      - g
      - plain flour
      - sifted

This package uses a natural language model trained on thousands of example ingredient sentences. A Condition Random Fields model has been trained on data from three sources. The New York Times released a large dataset when they did some similar work in 2015 in their `Ingredient Phrase Tagger <https://github.com/nytimes/ingredient-phrase-tagger>`_ repository. A dump of recipes taken from Cookstr in 2017. I have also gathered a (much smaller) dataset from recipes, which is also used to train the model.

Installation
^^^^^^^^^^^^

You can install ``ingredient_parser`` from PyPi with ``pip``:

.. code:: bash
    
    $ python -m pip install ingredient_parser_nlp

This will download and install the package and it's dependencies:

* `NLTK <https://www.nltk.org/>`_
* `python-crfsuite <https://python-crfsuite.readthedocs.io/en/latest/>`_

Usage
^^^^^

The primary functionality of this package is provided by the :func:`parse_ingredient` function.

The :func:`parse_ingredient` function takes an ingredient sentence and return the structered data extracted from it.

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("2 yellow onions, finely chopped")
        ParsedIngredient(
            name=IngredientText(text='yellow onions', confidence=0.967262),
            amount=[IngredientAmount(quantity='2',
                                     unit='',
                                     confidence=0.997084,
                                     APPROXIMATE=False,
                                     SINGULAR=False)],
            preparation=IngredientText(text='finely chopped',
                                       confidence=0.995751),
            comment=None,
            other=None,
            sentence='2 yellow onions, finely chopped'
        )


The returned dataclass contains the following fields:

sentence
    The input sentence passed to the :func:`parse_ingredient` function.

amount
    The amounts parsed from the sentence. Each amount has a quantity and a unit, plus optional flags indicating if the amount is approximate or is for a singular item.

name
    The name of the ingredient sentence, or None.

comment
    The comment from the ingredient sentence. This is a string, or None if there is no comment.

other
    Anything else not identified in one of the other fields. This is a string, or None is there is nothing identified as other.

Each of the fields (except sentence) has a confidence value associated with it. This is a value between 0 and 1, where 0 represents no confidence and 1 represent full confidence. This is the confidence that the natural language model has that the given label is correct.


Multiple ingredient sentences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`parse_multiple_ingredients` function is provided as a convenience function. It accepts a list of ingredient sentences as it's input and returns a list of dictionaries with the parsed information.

.. code:: python

    >>> from ingredient_parser import parse_multiple_ingredients
    >>> sentences = [
        "3 tablespoons fresh lime juice, plus lime wedges for serving",
        "2 tablespoons extra-virgin olive oil",
        "2 large garlic cloves, finely grated",
    ]
    >>> parse_multiple_ingredients(sentences)
    [
        ParsedIngredient(
            name=IngredientText(text='fresh lime juice', confidence=0.991891),
            amount=[IngredientAmount(quantity='3', 
                                     unit='tablespoons', 
                                     confidence=0.999459, 
                                     APPROXIMATE=False, 
                                     SINGULAR=False)], 
            preparation=None, 
            comment=IngredientText(text='plus lime wedges for serving', confidence=0.995029),
            other=None, 
            sentence='3 tablespoons fresh lime juice, plus lime wedges for serving'
        ), 
        ParsedIngredient(
            name=IngredientText(text='extra-virgin olive oil', confidence=0.996531), 
            amount=[IngredientAmount(quantity='2', 
                                     unit='tablespoons', 
                                     confidence=0.999259, 
                                     APPROXIMATE=False, 
                                     SINGULAR=False)], 
            preparation=None, 
            comment=None, 
            other=None, 
            sentence='2 tablespoons extra-virgin olive oil'
        ), 
        ParsedIngredient(
            name=IngredientText(text='garlic', confidence=0.992021), 
            amount=[IngredientAmount(quantity='2', 
                                     unit='large cloves', 
                                     confidence=0.983268, 
                                     APPROXIMATE=False, 
                                     SINGULAR=False)], 
            preparation=IngredientText(text='finely grated', confidence=0.997482), 
            comment=None, 
            other=None, 
            sentence='2 large garlic cloves, finely grated'
        )
    ]

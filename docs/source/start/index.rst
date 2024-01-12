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
      - Preparation
      - Comment
    * - 200
      - g
      - plain flour
      - sifted
      - 

This package uses a natural language model trained on thousands of example ingredient sentences. A Conditional Random Fields model has been trained on data from three sources: 

* The New York Times released a large dataset when they did some similar work in 2015 in their `Ingredient Phrase Tagger <https://github.com/nytimes/ingredient-phrase-tagger>`_ repository. 
* A dump of recipes taken from Cookstr in 2017. 
* A dump of recipe taken from BBC Food in 2017.

More information on how the natural language model is trained and the output interpreted can be found in the :doc:`Model Guide </guide/index>`.

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
        name=IngredientText(text='yellow onions', confidence=0.0.982988),
        amount=[IngredientAmount(quantity='2',
                                 unit='',
                                 text='2',
                                 confidence=0.998804,,
                                 APPROXIMATE=False,
                                 SINGULAR=False)],
        preparation=IngredientText(text='finely chopped',
                                   confidence=0.995613),
        comment=None,
        sentence='2 yellow onions, finely chopped'
    )


The returned dataclass contains the following fields:

sentence
    The input sentence passed to the :func:`parse_ingredient` function.

amount
    The amounts parsed from the sentence. Each amount has a quantity and a unit, plus optional flags indicating if the amount is approximate or is for a singular item.

name
    The name of the ingredient sentence, or None.

preparation
    The preparation notes for the ingredient. This is a string, or None is there are no preparation notes for the ingredient.

comment
    The comment from the ingredient sentence. This is a string, or None if there is no comment.

Each of the fields (except sentence) has a confidence value associated with it. This is a value between 0 and 1, where 0 represents no confidence and 1 represent full confidence. This is the confidence that the natural language model has that the given label is correct, averaged across all tokens that contribute to a particular field.

:func:`parse_ingredient()` take an additional, optional parameter: ``discard_isolated_stop_words``. If set to True (default), then any stop words that appear in isolation in the name, preparation, or comment fields are discarded. For example:

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("2 tbsp of olive oil", discard_isolated_stop_words=True) # default
    ParsedIngredient(name=IngredientText(text='olive oil', confidence=0.993415),
        amount=[IngredientAmount(quantity='2',
                                 unit='tbsps',
                                 text='2 tbsps',
                                 confidence=0.999329,
                                 APPROXIMATE=False,
                                 SINGULAR=False)],
        preparation=None,
        comment=None,
        sentence='2 tbsp of olive oil'
    )
    >>> parse_ingredient("2 tbsp of olive oil", discard_isolated_stop_words=False)
    ParsedIngredient(name=IngredientText(text='olive oil', confidence=0.993415),
        amount=[IngredientAmount(quantity='2',
                                 unit='tbsps',
                                 text='2 tbsps',
                                 confidence=0.999329,
                                 APPROXIMATE=False,
                                 SINGULAR=False)],
        preparation=None,
        comment=IngredientText(text='of', confidence=0.836912),
        sentence='2 tbsp of olive oil'
    )



Multiple ingredient sentences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`parse_multiple_ingredients` function is provided as a convenience function. It accepts a list of ingredient sentences as it's input and returns a list of dictionaries with the parsed information. :func:`parse_multiple_ingredients` also has the same ``discard_isolated_stop_words`` optional argument.

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
                                     text='3 tablespoons',
                                     confidence=0.999459, 
                                     APPROXIMATE=False, 
                                     SINGULAR=False)], 
            preparation=None, 
            comment=IngredientText(text='plus lime wedges for serving', confidence=0.995029),
            sentence='3 tablespoons fresh lime juice, plus lime wedges for serving'
        ), 
        ParsedIngredient(
            name=IngredientText(text='extra-virgin olive oil', confidence=0.996531), 
            amount=[IngredientAmount(quantity='2', 
                                     unit='tablespoons', 
                                     text='2 tablespoons',
                                     confidence=0.999259, 
                                     APPROXIMATE=False, 
                                     SINGULAR=False)], 
            preparation=None, 
            comment=None, 
            sentence='2 tablespoons extra-virgin olive oil'
        ), 
        ParsedIngredient(
            name=IngredientText(text='garlic', confidence=0.992021), 
            amount=[IngredientAmount(quantity='2', 
                                     unit='large cloves', 
                                     text='2 large cloves',
                                     confidence=0.983268, 
                                     APPROXIMATE=False, 
                                     SINGULAR=False)], 
            preparation=IngredientText(text='finely grated', confidence=0.997482), 
            comment=None, 
            sentence='2 large garlic cloves, finely grated'
        )
    ]

Getting Started
===============

The Ingredient Parser package is a Python package for parsing structured information out of recipe ingredient sentences.

Given a recipe ingredient such as 

    200 g plain flour, sifted

we want to extract information about the quantity, units, name and comment. For the example above:

.. code:: python

    {
        "quantity": "200",
        "unit": "g",
        "name": "plain flour",
        "comment": "sifted",
    }

This package uses a natural language model trained on thousands of example ingredient sentence. The condition random fields model has been trained on data from two main sources. The New York Times released a large dataset when they did some similar work in 2015 in their `Ingredient Phrase Tagger <https://github.com/nytimes/ingredient-phrase-tagger>`_ repository. I have also gathered a (much smaller) dataset from recipes, which is also used to train the model.

Installation
^^^^^^^^^^^^

You can install ``ingredient_parser`` from PyPi with ``pip``:

.. code:: bash
    
    python -m pip install ingredient_parser_nlp

This will download and install the package,  plus it's dependencies.


Usage
^^^^^

The primary functionality of this package is provided by the ``parse_ingredient`` function.

The ``parse_ingredient`` function takes an ingredient sentence and return the structered data extracted from it.

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("2 yellow onions, finely chopped")
    ParsedIngredient(sentence='2 yellow onions, finely chopped', quantity='2', unit='', name='yellow onions', comment='finely chopped', other='', confidence=ParsedIngredientConfidence(quantity=0.9978, unit=0, name=0.9575, comment=0.9992, other=0))

The returned dataclass contains the following fields:

sentence
    The input sentence passed to the ``parse_ingredient`` function.

quantity
    The quantity of the ingredient sentence, or an empty string. This will always be a numeric in a string.

unit
    The units of the ingredient sentence, or an empty string.

name
    The name of the ingredient sentence, or an empty string.

comment
    The comment from the ingredient sentence. This is a string, or a list or strings if the words that make the comments are not all adjacent in the input.

other
    Anything else not identified in one of the other fields. This is a string, or a list or strings if the words that are identified as other are not all adjacent in the input.

confidence
    The confience associated with the parsed data in each of the other fields (except sentence). The confidence is a value between 0 (no confidence) and 1 (complete confidence).


Multiple ingredient sentences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``parse_multiple_ingredients`` function is provided as a convenience function. It accepts a list of ingredient sentences as it's input and returns a list of dictionaries with the parsed information.

.. code:: python

    >>> from ingredient_parser import parse_multiple_ingredients
    >>> sentences = [
        "3 tablespoons fresh lime juice, plus lime wedges for serving",
        "2 tablespoons extra-virgin olive oil",
        "2 large garlic cloves, finely grated",
    ]
    >>> parse_multiple_ingredients(sentences)
    [
        ParsedIngredient(sentence='3 tablespoons fresh lime juice, plus lime wedges for serving', quantity='3', unit='tablespoons', name='fresh lime juice', comment='plus lime wedges for serving', other='', confidence=ParsedIngredientConfidence(quantity=0.9994, unit=0.9995, name=0.9917, comment=0.992, other=0)),
        ParsedIngredient(sentence='2 tablespoons extra-virgin olive oil', quantity='2', unit='tablespoons', name='extra-virgin olive oil', comment='', other='', confidence=ParsedIngredientConfidence(quantity=0.9997, unit=0.9985, name=0.9929, comment=0, other=0)),
        ParsedIngredient(sentence='2 large garlic cloves, finely grated', quantity='2', unit='large cloves', name='garlic', comment='finely grated', other='', confidence=ParsedIngredientConfidence(quantity=0.9993, unit=0.943, name=0.9903, comment=0.9993, other=0))
    ]

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

.. error::
    
    This doesn't actually work yet beacuse I haven't uploaded to pypi.

You can install ``ingredient_parser`` from PyPi with ``pip``:

.. code:: bash
    
    python -m pip install ingredient_parser_mlp

This will download and install the package,  plus it's dependencies.


Usage
^^^^^

The primary functionality of this package is provided by the ``parse_ingredient`` function.

The ``parse_ingredient`` function takes an ingredient sentence and return the structered data extracted from it.

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("2 yellow onions, finely chopped")
    {'sentence': '2 yellow onions, finely chopped', 'quantity': '2', 'unit': '', 'name': 'yellow onions', 'comment': 'finely chopped', 'other': ''}

The returned dictionary contains the following fields:

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


An optional ``confidence`` argument can be passed to the ``parse_ingredient`` function, which will include an extra entry in the returned dictionary containing the confidence associated with each field. The confidence is a value between 0 (no confidence) and 1 (complete confidence).

.. code:: python

    >>> parse_ingredient("2 yellow onions, finely chopped", confidence=True)
    {'sentence': '2 yellow onions, finely chopped', 'quantity': '2', 'unit': '', 'name': 'yellow onions', 'comment': 'finely chopped', 'other': '', 'confidence': {'quantity': 0.9941, 'unit': 0, 'name': 0.9281, 'comment': 0.9957, 'other': 0}}

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
    [{'sentence': '3 tablespoons fresh lime juice, plus lime wedges for serving', 'quantity': '3', 'unit': 'tablespoon', 'name': 'lime juice', 'comment': ['fresh', 'plus lime wedges for serving'], 'other': ''}, {'sentence': '2 tablespoons extra-virgin olive oil', 'quantity': '2', 'unit': 'tablespoon', 'name': 'extra-virgin olive oil', 'comment': '', 'other': ''}, {'sentence': '2 large garlic cloves, finely grated', 'quantity': '2', 'unit': 'clove', 'name': 'garlic', 'comment': 'finely grated', 'other': 'large'}]

This function also accepts the optional ``confidence`` argument which, when ``True`` will return the confidence for each field in the dictionaries.
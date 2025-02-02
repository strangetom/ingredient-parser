.. currentmodule:: ingredient_parser.parsers

Examples
========

This page lists a number of example that showcase the capability of the library, and also highlights some limitations.

Basic example
~~~~~~~~~~~~~

A basic example to show the full output from :func:`parse_ingredient`.

.. code:: python

    >>> parse_ingredient("1 large red onion, finely diced")
    ParsedIngredient(name=[IngredientText(text='red onion',
                                          confidence=0.994235,
                                          starting_index=2)],
                     size=IngredientText(text='large',
                                         confidence=0.997111,
                                         starting_index=1),
                     amount=[IngredientAmount(quantity=Fraction(1, 1),
                                              quantity_max=Fraction(1, 1),
                                              unit='',
                                              text='1',
                                              confidence=0.999933,
                                              starting_index=0,
                                              APPROXIMATE=False,
                                              SINGULAR=False,
                                              RANGE=False,
                                              MULTIPLIER=False,
                                              PREPARED_INGREDIENT=False)],
                     preparation=IngredientText(text='finely diced',
                                                confidence=0.998908,
                                                starting_index=5),
                     comment=None,
                     purpose=None,
                     foundation_foods=[],
                     sentence='1 large red onion, finely diced')

Multiple amounts
~~~~~~~~~~~~~~~~

A common pattern used in ingredient sentences is to specifiy amounts in terms of a fixed size item, e.g. 2 28 ounce cans.
In these cases, the outer amount (2 cans) and inner amount (28 ounce) are separated.
The inner amount has the ``SINGULAR`` flag set to True to indicate that it applies to a singular item of the outer amount.

.. code:: python

    >>> parse_ingredient("2 28 ounce cans whole tomatoes")
    ParsedIngredient(name=[IngredientText(text='whole tomatoes',
                                          confidence=0.999044,
                                          starting_index=4)],
                     size=None,
                     amount=[IngredientAmount(quantity=Fraction(2, 1),
                                              quantity_max=Fraction(2, 1),
                                              unit='cans',
                                              text='2 cans',
                                              confidence=0.999825,
                                              starting_index=0,
                                              APPROXIMATE=False,
                                              SINGULAR=False,
                                              RANGE=False,
                                              MULTIPLIER=False,
                                              PREPARED_INGREDIENT=False),
                             IngredientAmount(quantity=Fraction(28, 1),
                                              quantity_max=Fraction(28, 1),
                                              unit=<Unit('ounce')>,
                                              text='28 ounces',
                                              confidence=0.999437,
                                              starting_index=1,
                                              APPROXIMATE=False,
                                              SINGULAR=True,
                                              RANGE=False,
                                              MULTIPLIER=False,
                                              PREPARED_INGREDIENT=False)],
                     preparation=None,
                     comment=None,
                     purpose=None,
                     foundation_foods=[],
                     sentence='2 28 ounce cans whole tomatoes')

Approximate amounts
~~~~~~~~~~~~~~~~~~~

Approximate amounts, indicate by the use of words like `approximately`, `about`, `roughly` etc., have the ``APPROXIMATE`` flag set.

.. code:: python

    >>> parse_ingredient("4 pork chops, about 400 g each")
    ParsedIngredient(name=[IngredientText(text='pork chops',
                                          confidence=0.9961,
                                          starting_index=1)],
                     size=None,
                     amount=[IngredientAmount(quantity=Fraction(4, 1),
                                              quantity_max=Fraction(4, 1),
                                              unit='',
                                              text='4',
                                              confidence=0.999876,
                                              starting_index=0,
                                              APPROXIMATE=False,
                                              SINGULAR=False,
                                              RANGE=False,
                                              MULTIPLIER=False,
                                              PREPARED_INGREDIENT=False),
                             IngredientAmount(quantity=Fraction(400, 1),
                                              quantity_max=Fraction(400, 1),
                                              unit=<Unit('gram')>,
                                              text='400 g',
                                              confidence=0.995449,
                                              starting_index=5,
                                              APPROXIMATE=True,
                                              SINGULAR=True,
                                              RANGE=False,
                                              MULTIPLIER=False,
                                              PREPARED_INGREDIENT=False)],
                     preparation=None,
                     comment=None,
                     purpose=None,
                     foundation_foods=[],
                     sentence='4 pork chops, about 400 g each')

Prepared ingredients
~~~~~~~~~~~~~~~~~~~~

The order in which the amount, name and preparation instructions are given can change the amount of the ingredient specified by the sentence.

For example, **1 cup flour, sifted** instructs the chef to measure 1 cup of flour and then sift it.
Conversely, **1 cup sifted flour** instructs the chef to sift flour to obtain 1 cup, which would have a different mass to the first case.
For this second case, the ``PREPARED_INGREDIENT`` flag will be set to True.

.. code:: python

    >>> parse_ingredient("1 cup flour, sifted")
    ParsedIngredient(name=[IngredientText(text='flour',
                                          confidence=0.998215,
                                          starting_index=2)],
                     size=None,
                     amount=[IngredientAmount(quantity=Fraction(1, 1),
                                              quantity_max=Fraction(1, 1),
                                              unit=<Unit('cup')>,
                                              text='1 cup',
                                              confidence=0.999959,
                                              starting_index=0,
                                              APPROXIMATE=False,
                                              SINGULAR=False,
                                              RANGE=False,
                                              MULTIPLIER=False,
                                              PREPARED_INGREDIENT=False)],
                     preparation=IngredientText(text='sifted',
                                                confidence=0.999754,
                                                starting_index=4),
                     comment=None,
                     purpose=None,
                     foundation_foods=[],
                     sentence='1 cup flour, sifted')

    >>> parse_ingredient("1 cup sifted flour")
    ParsedIngredient(name=[IngredientText(text='flour',
                                          confidence=0.986433,
                                          starting_index=3)],
                     size=None,
                     amount=[IngredientAmount(quantity=Fraction(1, 1),
                                              quantity_max=Fraction(1, 1),
                                              unit=<Unit('cup')>,
                                              text='1 cup',
                                              confidence=0.99918,
                                              starting_index=0,
                                              APPROXIMATE=False,
                                              SINGULAR=False,
                                              RANGE=False,
                                              MULTIPLIER=False,
                                              PREPARED_INGREDIENT=True)],
                     preparation=IngredientText(text='sifted',
                                                confidence=0.990133,
                                                starting_index=2),
                     comment=None,
                     purpose=None,
                     foundation_foods=[],
                     sentence='1 cup sifted flour')

Alternative ingredients
~~~~~~~~~~~~~~~~~~~~~~~

Sometimes an ingredient sentence will include a number of alternative ingredients that can be used in the same quantities.

The library attempts to ensure that each of the identified ingredient names makes sense on it's own. For example in the sentence **2 tbsp olive or sunflower oil**, it would be incorrect to identify the two ingredient names as **olive** and **sunflower oil**. The actual names are **olive oil** and **sunflower oil**.

.. code:: python

    >>> parse_ingredient("2 tbsp olive or sunflower oil")
    ParsedIngredient(name=[IngredientText(text='olive oil',
                                          confidence=0.989134,
                                          starting_index=2),
                           IngredientText(text='sunflower oil',
                                          confidence=0.982565,
                                          starting_index=4)],
                     size=None,
                     amount=[IngredientAmount(quantity=Fraction(2, 1),
                                              quantity_max=Fraction(2, 1),
                                              unit=<Unit('tablespoon')>,
                                              text='2 tbsps',
                                              confidence=0.999819,
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
                     sentence='2 tbsp olive or sunflower oil')

Alternative ingredients with different amounts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes a single ingredient sentence will contain multiple phrases, each specifying a different ingredient with a different amount.

.. admonition:: Limitation

    This library assumes an ingredient sentence does not contain different ingredient with different amounts.

    For cases where the sentence contains multiple phrases, specifiying different ingredients in different amounts, everything after the first phrase will be returned in the comment field.

.. code:: python

    >>> parse_ingredient("1 cup peeled and cooked fresh chestnuts (about 20), or 1 cup canned, unsweetened chestnuts")
    ParsedIngredient(name=[IngredientText(text='fresh chestnuts',
                                      confidence=0.977679,
                                      starting_index=5)],
                 size=None,
                 amount=[IngredientAmount(quantity=Fraction(1, 1),
                                          quantity_max=Fraction(1, 1),
                                          unit=<Unit('cup')>,
                                          text='1 cup',
                                          confidence=0.999549,
                                          starting_index=0,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=True),
                         IngredientAmount(quantity=Fraction(20, 1),
                                          quantity_max=Fraction(20, 1),
                                          unit='',
                                          text='20',
                                          confidence=0.887524,
                                          starting_index=9,
                                          APPROXIMATE=True,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False)],
                 preparation=IngredientText(text='peeled and cooked',
                                            confidence=0.999523,
                                            starting_index=2),
                 comment=IngredientText(text='or 1 cup canned, unsweetened '
                                             'chestnuts',
                                        confidence=0.925894,
                                        starting_index=12),
                 purpose=None,
                 foundation_foods=[],
                 sentence='1 cup peeled and cooked fresh chestnuts (about 20), '
                          'or 1 cup canned, unsweetened chestnuts')


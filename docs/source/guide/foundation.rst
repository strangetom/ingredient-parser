Foundation foods
================

Explanation
^^^^^^^^^^^

The ``foundation_foods`` optional keyword argument for the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function enables the functionality that extracts the foundation foods from the ingredient sentence.

A foundation food is the core or fundamental item of an ingredient sentence, without any other words like descriptive adjectives or brand names. For example, in the sentence

    1 large organic cucumber

the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function will identify the name as **organic cucumber**. The foundation food is **cucumber**.

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("1 large organic cucumber", foundation_foods=True)
    ParsedIngredient(
        name=IngredientText(text='organic cucumber',
                            confidence=0.997585),
        size=IngredientText(text='large',
                            confidence=0.987387),
        amount=[IngredientAmount(quantity=1.0,
                                 quantity_max=1.0,
                                 unit='',
                                 text='1',
                                 confidence=0.999895,
                                 starting_index=0,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False)],
        preparation=None,
        comment=None,
        purpose=None,
        foundation_foods=[IngredientText(text='cucumber',
                                         confidence=0.997391)],
        sentence='1 large organic cucumber'
    )

Examples
~~~~~~~~

The table below gives some examples of the foundation foods for different ingredient names.

+-----------------------------------------+-----------------+
| Name                                    | Foundation Food |
+=========================================+=================+
| canned plum tomatoes with juice         | tomatoes        |
+-----------------------------------------+-----------------+
| seedless grapes                         | grapes          |
+-----------------------------------------+-----------------+
| all-purpose flour                       | flour           |
+-----------------------------------------+-----------------+
| Granny Smith apples                     | apples          |
+-----------------------------------------+-----------------+
| Market Pantry™ Shredded Parmesan Cheese | Parmesan Cheese |
+-----------------------------------------+-----------------+
| roasted red pepper strips               | red pepper      |
+-----------------------------------------+-----------------+

.. attention::

    The foundation foods are based on the USDA's `FoodData Central Foundation Foods <https://fdc.nal.usda.gov/fdc-app.html#/food-search?type=Foundation&query=>`_ database. However, that database does not perfectly align with how ingredients are referred to in recipes so you may find that examples where a foundation food from the :abbr:`FDC (FoodData Central)` database is not identified, or an identified foundation food is not in the :abbr:`FDC (FoodData Central)` database.

    Interpretation and extrapolation has been applied in the development of this functionality.

Model
^^^^^

Identification of foundation foods is implemented as a separate :abbr:`CRF (Conditional Random Fields)` model. This model is trained on just the NAME tokens for each sentence in the training data, using the same features as the main parser model for each token. The model has two labels:

- FF: the token is a foundation food
- NF: the token is not a foundation food

The model can be trained using the following command

.. code::

    $ python train.py train --model foundationfoods --database train/data/training.sqlite3

.. tip::

    All the same options that can be used when training the parser model can also be used when training the foundation foods model. See :doc:`Training the model <training>` for more details.

.. note::

    See the `Foundation Food Model Card <https://github.com/strangetom/ingredient-parser/blob/master/ingredient_parser/en/FF_ModelCard.en.md>`_ for the current model performance.

The identified foundation foods are defined as the consecutive NAME tokens labelled with FF by the foundation foods model.

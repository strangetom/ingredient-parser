Foundation foods
================

.. versionchanged:: v2.1.0

    This functionality now matches ingredients to the FDC database.

    Whilst the changes are API compatible with earlier versions, the contents of the fields in the :class:`FoundationFood <ingredient_parser.dataclasses.FoundationFood>` objects are different.

The goal of the foundation foods functionality is to match the ingredient names identified from the ingredient sentence to entries in the USDA's `Food Data Central <https://fdc.nal.usda.gov/>`_ (:abbr:`FDC (Food Data Central)`) database.

The ``foundation_foods`` optional keyword argument for the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function enables this functionality when set to ``True``.

For example, in the sentence

    24 fresh basil leaves or dried basil

the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function will identify two names: **fresh basil leaves** and **dried basil**. The matching FDC entries are `Basil, fresh <https://fdc.nal.usda.gov/food-details/172232/nutrients>`_ and `Spices, basil, dried <https://fdc.nal.usda.gov/food-details/171317/nutrients>`_.

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("1 large organic cucumber", foundation_foods=True)
    ParsedIngredient(
        name=[IngredientText(text='fresh basil leaves',
                             confidence=0.970321,
                             starting_index=1),
              IngredientText(text='dried basil',
                             confidence=0.843839,
                             starting_index=5)],
        size=None,
        amount=[IngredientAmount(quantity=Fraction(24, 1),
                                 quantity_max=Fraction(24, 1),
                                 unit='',
                                 text='24',
                                 confidence=0.999585,
                                 starting_index=0,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False,
                                 PREPARED_INGREDIENT=False)],
        preparation=None,
        comment=None,
        purpose=None,
        foundation_foods=[FoundationFood(text='Basil, fresh',
                                         confidence=0.838445,
                                         fdc_id=172232,
                                         category='Spices and Herbs',
                                         data_type='sr_legacy_food'),
                          FoundationFood(text='Spices, basil, dried',
                                         confidence=0.839727,
                                         fdc_id=171317,
                                         category='Spices and Herbs',
                                         data_type='sr_legacy_food')],
        sentence='24 fresh basil leaves or dried basil'
    )


Explanation
^^^^^^^^^^^

The matching of the ingredient names to entries in the :abbr:`FDC (Food Data Central)` database is a difficult problem.
This is due to the descriptions of the entries in the :abbr:`FDC (Food Data Central)` database being quite different to the way the ingredients are commonly referred to in recipes.

For example,  the matching entry for **red pepper** has a description of **peppers, bell, red, raw**.

The approach taken is based on the paper `A Word Embedding Model for Mapping Food Composition Databases Using Fuzzy Logic <https://dx.doi.org/10.1007/978-3-030-50143-3_50>`_.
The same word embeddings model used to provide semantic features for the :abbr:`CRF (Conditional Random Fields)` parser model is used provide the word vectors for each token in the ingredient name and each token in the description of the :abbr:`FDC (Food Data Central)` entries.
These vectors are used to compute a fuzzy distance score between the ingredient name tokens and each :abbr:`FDC (Food Data Central)` entry, which is used to find the best matching :abbr:`FDC (Food Data Central)` entry.

The full process is as follows:

#. Load the :abbr:`FDC (Food Data Central)` data. Tokenize the description for each entry and remove tokens that don't provide useful semantic information*.

#. Prepare the ingredient name tokens in the same way.

#. Check the ingredient name tokens against a list of override matches and return the matching result if there is one.
   This is done because this approach does not work very well if the ingredient name only contains a single token.

#. Iterate through each of the :abbr:`FDC (Food Data Central)` data types in turn, in order of preference.

   #. Compute the fuzzy distance score between each :abbr:`FDC (Food Data Central)` entry and the ingredient name tokens.

   #. Sort the :abbr:`FDC (Food Data Central)` by their score.

   #. If there is a match with a score below the threshold, return the best match.

   #. If there are not any matches with a good enough score, store the best match for fallback matching.

#. If none of the :abbr:`FDC (Food Data Central)` datasets contained a good enough match, attempt fallback matching.

   #. Sort the best match from each :abbr:`FDC (Food Data Central)` data set.

   #. If the score for the best of these matches is below a threshold, return this match.

#. If no match is good enough, return ``None``.

.. note::

    Tokens that do not provide useful semantic information are as follows: numbers, white space, punctuation, stop words, single character words.




Limitations
^^^^^^^^^^^

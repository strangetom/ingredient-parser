.. _reference-explanation-foundation-foods:

Foundation foods
================

.. versionchanged:: v2.1.0

    This functionality matches ingredients to the FDC database.

    Whilst the changes are API compatible with earlier versions, the contents of the fields in the :class:`FoundationFood <ingredient_parser.dataclasses.FoundationFood>` objects are different.

The goal of the foundation foods functionality is to match the ingredient names identified from the ingredient sentence to entries in the USDA's `Food Data Central <https://fdc.nal.usda.gov/>`_ (:abbr:`FDC (Food Data Central)`) database.

The ``foundation_foods`` optional keyword argument for the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function enables this functionality when set to ``True``.

For example, in the sentence

    24 fresh basil leaves or dried basil

the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function will identify two names: **fresh basil leaves** and **dried basil**. The matching FDC entries are `Basil, fresh <https://fdc.nal.usda.gov/food-details/172232/nutrients>`_ and `Spices, basil, dried <https://fdc.nal.usda.gov/food-details/171317/nutrients>`_.

.. code:: python

    >>> from ingredient_parser import parse_ingredient
    >>> parse_ingredient("24 fresh basil leaves or dried basil", foundation_foods=True)
    ParsedIngredient(
        name=[IngredientText(text='fresh basil leaves',
                             confidence=0.973058,
                             starting_index=1),
              IngredientText(text='dried basil',
                             confidence=0.87027,
                             starting_index=5)],
        size=None,
        amount=[IngredientAmount(quantity=Fraction(24, 1),
                                 quantity_max=Fraction(24, 1),
                                 unit='',
                                 text='24',
                                 confidence=0.999702,
                                 starting_index=0,
                                 unit_system=<UnitSystem.NONE: 'none'>,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False,
                                 PREPARED_INGREDIENT=False)],
        preparation=None,
        comment=None,
        purpose=None,
        foundation_foods=[FoundationFood(text='Basil, fresh',
                                         confidence=0.862222,
                                         fdc_id=172232,
                                         category='Spices and Herbs',
                                         data_type='sr_legacy_food',
                                         url='https://fdc.nal.usda.gov/food-details/172232/nutrients'),
                           FoundationFood(text='Spices, basil, dried',
                                          confidence=0.856791,
                                          fdc_id=171317,
                                          category='Spices and Herbs',
                                          data_type='sr_legacy_food',
                                          url='https://fdc.nal.usda.gov/food-details/171317/nutrients')],
        sentence='24 fresh basil leaves or dried basil'
    )

This functionality works entirely offline.
A subset of the `full download <https://fdc.nal.usda.gov/download-datasets>`_ of the :abbr:`FDC (Food Data Central)` database is distributed with this library, which includes the foudation_food, sr_legacy_food and survey_fndds_food data sets.
This data is used when matching an ingredient name to an `FDC (Food Data Central)` entry.

Explanation
^^^^^^^^^^^

The matching of the ingredient names to entries in the :abbr:`FDC (Food Data Central)` database is a difficult problem.
The descriptions of the entries in the :abbr:`FDC (Food Data Central)` database are quite different to the way the ingredients are commonly referred to in recipes, therefore matching one to the other is a challenge.
For example, the matching entry for **spring onions** has a description of **Onions, spring or scallions (includes tops and bulb), raw**.

Typical fuzzy matching approaches that use character or token level changes to scores matches will not work well because difference in string lengths.
In addition, there may be more than one word for a particular ingredient and the word used in the :abbr:`FDC (Food Data Central)` entry description might not be the same as the word used in the ingredient sentence.
In these cases, we still want to select the correct entry.

The approach taken attempts to match ingredient names to :abbr:`FDC (Food Data Central)` entries based on semantic similarity, that is, selecting the entry that is closest in meaning to the ingredient name even where the words used are not the identical.
Two semantic matching techniques are used, based on [Ethayarajh]_ and [Morales-Garzón]_.
Both techniques make use of a word embeddings model.
A `GloVe <https://nlp.stanford.edu/projects/glove/>`_ embeddings model trained on text from a large corpus of recipes and is used to provide the information for the semantic similarity techniques.

Unsupervised Smooth Inverse Frequency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The technique described in [Ethayarajh]_ is called Unsupervised Smooth Inverse Frequency (uSIF).
This technique calculates an embedding vector for a sentence from the weighted vectors of the words, where the weight is related to the probability of encountering the word (related to the inverse frequency of the word).
The technique also removes common components in the word vectors, although this is not implemented here (primarily due to not wanting to include a further runtime dependency of sklearn - this may change in the future if it proves to be helpful).

This approach is applied to the descriptions for each of the :abbr:`FDC (Food Data Central)` entries and ingredient name we are trying to find the closest match to.
The best match is selected using the cosine similarity metric.

In practice, this technique is generally pretty good at finding a reasonable matching :abbr:`FDC (Food Data Central)` entry.
However, in some cases the match with the best score is not an appropriate match.
The reason for this is likely due to limitations in the quality of the embeddings used.

Fuzzy Document Distance
~~~~~~~~~~~~~~~~~~~~~~~

The fuzzy document distance metric is described in [Morales-Garzón]_.
Each sentence is considered as a set of tokens, and the distance is calculated from the Euclidean distance between tokens in two sentences being compared.
By considering the embedding vector for each token individually, this metric yields different results to :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` but is quote effective nonetheless.

The results using this approach are more explainable than the result from :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)`, however the implementation of this metric has the downside of being significantly slower.

Combined
~~~~~~~~

The two techniques are combined to perform the matching of an ingredient name to an :abbr:`FDC (Food Data Central)` entry.

First, :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` is used to down select a list of *n* candidate matches from the full set of :abbr:`FDC (Food Data Central)` entries

Second, the fuzzy document distance is calculated for the down selected candidate matches.

Finally the best scoring match is selected, accounting for the preference in :abbr:`FDC (Food Data Central)` data type.
In summary, if there are other :abbr:`FDC (Food Data Central)` entries with fuzzy document distances that are very similar to the best, then the select entry is based on the preferred data type rather than just based on the best score.

Limitations
^^^^^^^^^^^

The current implementation has a some limitations.

#. The fuzzy distance scoring will sometimes result in returning an :abbr:`FDC (Food Data Central)` entry that has a good score but is not a good match.
   Work is ongoing to improve this, and suggestions and contributions are welcome.

#. Enabling this functionality is much slower than when not enabled.
   When enabled, parsing a sentence is roughly 75x slower than if disabled .

References
^^^^^^^^^^

.. [Ethayarajh] Kawin Ethayarajh. 2018. Unsupervised Random Walk Sentence Embeddings: A Strong but Simple Baseline. In Proceedings of the Third Workshop on Representation Learning for NLP, pages 91–100, Melbourne, Australia. Association for Computational Linguistics. https://aclanthology.org/W18-3012/

.. [Morales-Garzón] Morales-Garzón, A., Gómez-Romero, J., Martin-Bautista, M.J. (2020). A Word Embedding Model for Mapping Food Composition Databases Using Fuzzy Logic. In: Lesot, MJ., et al. Information Processing and Management of Uncertainty in Knowledge-Based Systems. IPMU 2020. Communications in Computer and Information Science, vol 1238. Springer, Cham. https://doi.org/10.1007/978-3-030-50143-3_50

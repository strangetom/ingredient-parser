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
This data is used when matching an ingredient name to an :abbr:`FDC (Food Data Central)` entry.

Explanation
^^^^^^^^^^^

The matching of the ingredient names to entries in the :abbr:`FDC (Food Data Central)` database is a difficult problem.
The descriptions of the entries in the :abbr:`FDC (Food Data Central)` database are quite different to the way the ingredients are commonly referred to in recipes, therefore matching one to the other is a challenge.
For example, the matching entry for **spring onions** has a description of **Onions, spring or scallions (includes tops and bulb), raw**.

Therefore a number of search engine ranking functions are used, and the results fused together to obtain the best (and hopefully most relevant) result.
The different search engine ranking function have different characteristics:

* BM25 [#Robertson]_ considers exact matching tokens, and weights tokens according the relevance of the information each token conveys.
* :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` [#Ethayarajh]_ is a semantic ranking function that uses `GloVe <https://nlp.stanford.edu/projects/glove/>`_ embeddings to rank FDC ingredients based semantic similarity.
* Fuzzy [#Morales]_ is an alternative approach to semantic ranking, also use the `GloVe <https://nlp.stanford.edu/projects/glove/>`_ embeddings.

For the semantic raking functions, a `GloVe <https://nlp.stanford.edu/projects/glove/>`_ embeddings model trained on text from a large corpus of recipes is used to provide the information for the semantic similarity techniques.

The flow chart below outlines the process of matching an :abbr:`FDC (Food Data Central)` ingredient to an ingredient name.

.. figure:: /_static/diagrams/ff_search.png
  :class: dark-light
  :width: 400
  :alt: Foundation food matching process.

  Foundation food matching process.

1. Normalize tokens
~~~~~~~~~~~~~~~~~~~

The ingredient name tokens are normalized by taking the following steps:

* Splitting tokens containing hyphens into separate tokens.
* Discarding tokens that are numbers, white space or only a single character.
* Stemming the remaining tokens.

In addition, any ambiguous adjectives that occur at the start of the ingredient name are removed.
Ambiguous adjectives are those that have multiple meaning which can cause confusion in the subsequent scoring steps.
For example, **hot** can refer to temperature or spiciness.
It is removed to prevent ingredients with a hot temperature being confusing with :abbr:`FDC (Food Data Central)` entries that are spicy.

.. note::

    The same normalization process is also applied to the :abbr:`FDC (Food Data Central)` entry descriptions.

2. Check overrides
~~~~~~~~~~~~~~~~~~

The foundation food matching process can sometimes struggle with simple ingredient names because the relevant :abbr:`FDC (Food Data Central)` entry often do not have a simple description.

A list of overrides that map simple of ingredient names to the relevant :abbr:`FDC (Food Data Central)` entry is used to ensure a correct match for these cases.

3. Score using :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` matcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The technique is called Unsupervised Smooth Inverse Frequency (uSIF) [#Ethayarajh]_.
This technique calculates an embedding vector for a sentence from the weighted vectors of the words, where the weight is related to the probability of encountering the word (related to the inverse frequency of the word).
The technique also removes common components in the word vectors, although this is not implemented here (primarily due to not wanting to include a further runtime dependency of sklearn - this may change in the future if it proves to be helpful).

This approach is applied to the descriptions for each of the :abbr:`FDC (Food Data Central)` entries and ingredient name we are trying to find the closest match to.
Rankings are obtained by calculating the cosine similarity between the ingredient name vector and each :abbr:`FDC (Food Data Central)` description vector.

In practice, this technique is generally pretty good at finding a reasonable matching :abbr:`FDC (Food Data Central)` entry.
However, in some cases the match with the best score is not an appropriate match.
The reason for this is likely due to limitations in the quality of the embeddings used.

.. hint::

    Add explanation of the phrase weighting scheme, assuming it's provably useful.

.. code:: python

    >>> from ingredient_parser.en.foundationfoods._usif import get_usif_matcher
    >>> usif = get_usif_matcher()
    >>> rankings = usif.score_matches(["red", "pepper"])
    >>> for rank in rankings[:5]:
            print(f"{rank.score:.4f}: {rank.fdc.description}")

    0.0320: Peppers, red, cooked
    0.1057: Peppers, bell, red, raw
    0.1172: Peppers, sweet, red, sauteed
    0.1326: Peppers, green, cooked
    0.1673: Peppers and onions, cooked, no added fat


4. Score using BM25 matcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The technique is called Best Matching 25 [#Robertson]_.
This technique calculates a similarity score between a query and a document and uses the term frequency and inverse document frequency to estimate the relative importance of each token.

This approach is generally very effective, however it relies on the same words used in the ingredient name and :abbr:`FDC (Food Data Central)` description.
Since this is not always the case, we combine it with the :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` matcher to handle cases where different words are used to refer to the same ingredient.

.. code:: python

    >>> from ingredient_parser.en.foundationfoods._bm25 import get_bm25_matcher
    >>> BM25 = get_bm25_matcher()
    >>> rankings = BM25.score_matches(["red", "pepper"])
    >>> for rank in rankings[:5]:
            print(f"{rank.score:.4f}: {rank.fdc.description}")

    12.9365: Peppers, red, cooked
    11.8650: Peppers, sweet, red, sauteed
    11.8650: Peppers, sweet, red, raw
    11.8650: Spices, pepper, red or cayenne
    11.8650: Peppers, bell, red, raw


5. Check :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` and BM25 alignment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Fuzzy technique described below is another semantic ranking technique, but it has the downside of being computationally expensive and therefore slow.

To avoid always having this slow down, the decision of when to use this is based on how well aligned the results from the :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` and BM25 matchers are.
If :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` and BM25 produce well aligned results (that is, a similar set of :abbr:`FDC (Food Data Central)` entries ranked in a similar order), then we do not need to use the Fuzzy matcher.
If the :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` and BM25 results are not well aligned, then we will use the Fuzzy matcher on the union of the top results from each matcher to provide another source of rankings for the results fusion later.

The alignment of the :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` and BM25 results is quantified using rank-biased overlap ([#Webber]_).
This calculates a score between 1 (identical rankings) and 0 (disjoint rankings).
A score below the set threshold triggers the use of the Fuzzy matcher.

6. Score using Fuzzy matcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The fuzzy document distance metric is described in [#Morales]_.
Each sentence is considered as a set of tokens, and the distance is calculated from the Euclidean distance between tokens in two sentences being compared.
By considering the embedding vector for each token individually, this metric yields different results to :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)` but is quote effective nonetheless.

The results using this approach are more explainable than the result from :abbr:`uSIF (Unsupervised Smooth Inverse Frequency)`, however the implementation of this metric has the downside of being significantly slower.

.. code:: python

    >>> from ingredient_parser.en.foundationfoods._fuzzy import get_fuzzy_matcher
    >>> fuzzy = get_fuzzy_matcher()
    >>> rankings = fuzzy.score_matches(["red", "pepper"])
    >>> for rank in rankings[:5]:
            print(f"{rank.score:.4f}: {rank.fdc.description}")

    0.1411: Peppers, red, cooked
    0.1994: Spices, pepper, red or cayenne
    0.2026: Peppers, sweet, red, sauteed
    0.2082: Peppers, bell, red, raw
    0.2085: Peppers, sweet, red, raw



7. Fuse results
~~~~~~~~~~~~~~~


8. Check if the best result is significant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Limitations
^^^^^^^^^^^

The current implementation has a some limitations.

#. The fuzzy distance scoring will sometimes result in returning an :abbr:`FDC (Food Data Central)` entry that has a good score but is not a good match.
   Work is ongoing to improve this, and suggestions and contributions are welcome.

#. Enabling this functionality is much slower than when not enabled.
   When enabled, parsing a sentence is roughly 75x slower than if disabled .

References
^^^^^^^^^^

.. [#Robertson] S.\ E. Robertson, S. Walker, S. Jones, M. Hancock-Beaulieu, and M. Gatford, ‘Okapi at TREC-3’, in Text Retrieval Conference, 1994.

.. [#Ethayarajh] Kawin Ethayarajh. 2018. Unsupervised Random Walk Sentence Embeddings: A Strong but Simple Baseline. In Proceedings of the Third Workshop on Representation Learning for NLP, pages 91–100, Melbourne, Australia. Association for Computational Linguistics. https://aclanthology.org/W18-3012/

.. [#Webber] W.\ Webber, A. Moffat, and J. Zobel, ‘A similarity measure for indefinite rankings’, ACM Trans. Inf. Syst., vol. 28, no. 4, pp. 1–38, Nov. 2010, doi: 10.1145/1852102.1852106.

.. [#Morales] Morales-Garzón, A., Gómez-Romero, J., Martin-Bautista, M.J. (2020). A Word Embedding Model for Mapping Food Composition Databases Using Fuzzy Logic. In: Lesot, MJ., et al. Information Processing and Management of Uncertainty in Knowledge-Based Systems. IPMU 2020. Communications in Computer and Information Science, vol 1238. Springer, Cham. https://doi.org/10.1007/978-3-030-50143-3_50

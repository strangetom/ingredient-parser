The Data
========

Data sources
^^^^^^^^^^^^

There are two sources of data which are used to train the model, each with their own advantages and disadvantages.

StrangerFoods
~~~~~~~~~~~~~

The recipes from my website: https://strangerfoods.org. 

* The dataset is extremely clean and well labelled. (Having very clean data is not necessarily useful since it won't reflect the kinds of sentences that we might come across in the wild.)
* The dataset primarily uses metric units
* The dataset is small, roughly 7100 entries

New York Times
~~~~~~~~~~~~~~

The New York Times released a dataset of labelled ingredients in their `Ingredient Phrase Tagger <https://github.com/NYTimes/ingredient-phrase-tagger>`_ repository, which had the same goal as this.

* The dataset isn't very clean and the labelling is suspect in places.
* The dataset primarily uses imperial/US customary units
* The dataset is large, roughly 178,000 entries

The two datasets have different advantages and disadvantages, therefore combining the two should yield an improvement over using either on their own.

Cleaning the New York Times dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The New York Times dataset has gone through, and continues to go through, the very manual process of cleaning the data. This process is there to ensure that the labels assigned to each token in each ingredient sentence are correct and consistent across the dataset. In general, the idea is to avoid modifying the input sentence and only correct the labels for each, although entries have been removed where there is too much missing information or the entry is not actually an ingredient sentence (a few recipe instructions have been found mixed into the data).

The model is currently trained using the first 30,000 entries, so the cleaning is primarily focussed on that subset.

.. note::

    The impact of the cleaning can be seen by training the model using the full NYTimes dataset, where the majority of the data has not been properly cleaned. The model performance drops significantly: ~5% hit to both word and sentence metrics.

    Perhaps in time, a larger amount of the data can be used, once properly cleaned up.

The following operations were done to clean up the data (note that this is not exhaustive, the git history for the dataset will give the full details).

* Convert all numbers in the labels to decimal
    This includes numbers represented by fractions in the input e.g. 1 1/2 becomes 1.5
* Convert all ranges to a standard format of X-Y
    This includes ranges represented textually, e.g. 1 to 2, 3 or 4 become 1-2, 3-4 respectively
* Entries where the quantities and units were originally consolidated should be unconsolidated
    There were many examples where the input would say 

        1/2 cup, plus 1 tablespoon ...

    with the quantity set as "9" and the unit "tablespoon".
    The model will not do maths for us, nor will it understand have to convert between units. In this example, the correct labelling is a quantity of "0.5", a unit of "cup", and a comment of "plus 1 tablespoon".
* Adjectives that are a fundamental part of the ingredient identity should be part of the name
    This was mostly an inconsistency across the data, for example if the entry contained "red onion", sometimes this was labelled with a name of "red onion" and sometimes with a name of "onion" and a comment of "red".

    A general rule was applied: if the adjective changes the ingredient in a way that the cook cannot, it should be part of the name. It is recognised that this can be subjective. Universal correctness is not the main goal of this, only consistency.

    Examples of this:

    * red/white/yellow/green/Spanish onion
    * granulated/brown/confectioners' sugar
    * soy/coconut/skim/whole milk
    * ground spices
    * extra-virgin olive oil
    * ...
* All units should be made singular
    This is to reduce the amount the model needs to learn. "teaspoon" and "teaspoons" are fundamentally the same unit, but because they are different words, the model could learn different associations.

:doc:`Data Cleaning Todo List <clean>` contains a list of possible further data cleaning steps.

Processing the data
^^^^^^^^^^^^^^^^^^^

Before any data can be used to either train or test the model, or the model used to label the data, the data needs to be pre-processed in a consistent manner. This pre-process step is there to remove as much of the variation in the data that can be reasonably foreseen, so that the model is presented with tidy and consistent data and therefore has an easier time of learning or labelling.

The pre-processing steps has three main steps:

1. Clean the input sentence to standardise specific constructs
2. Tokenize the cleaned input sentence 
3. Determine the features for each token.

The :class:`PreProcessor` class handles all three steps for us. 
.. code:: python

    >>> from Preprocess import PreProcessor
    >>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
    >>> p.sentence
    '0.5 cup orange juice, freshly squeezed'
    >>> p.tokenized_sentence
    ['0.5', 'cup', 'orange', 'juice', ',', 'freshly', 'squeezed']

Steps 1 and 2 are discussed below. Step 3 is discussed on the :doc:`Feature Selection <features>` page.

1. Clean the input sentence
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The cleaning of the input sentence is done immediately when the :class:`PreProcessor` class is instantiated. The ``_clean`` method of the :class:`PreProcessor` class is called, which executes a number of steps to clean up the input sentence.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._clean
    :dedent: 4

Each of the functions are detailed below.

``_replace_string_numbers``
+++++++++++++++++++++++++++

Numbers represented in textual form e.g. "one", "two" are replaced with numeric forms.
The replacements are predefined in a dictionary.
For performance reasons, the regular expressions used to substitute the text with the number are precomiled and provided in the ``STRING_NUMBERS_REGEXES`` constant, which is a dictionary where the value is a tuple of (precompiled regex, substitute value).

.. literalinclude:: ../../../ingredient_parser/_constants.py
    :lines: 85-104
    

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_string_numbers
    :dedent: 4

``_replace_html_fractions``
+++++++++++++++++++++++++++

Fractions represented by html entities (e.g. 0.5 as ``&frac12;``) are replaced with Unicode equivalents (e.g. ½). This is done using the standard library ``html.unescape`` function.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_html_fractions
    :dedent: 4


``_replace_unicode_fractions``
++++++++++++++++++++++++++++++

Fractions represented by Unicode fractions are replace a textual format (.e.g ½ as 1/2), as defined by the dictionary in this function. Note that because the previous function replaced html fractions with Unicode fractions, the order of these functions is important.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_unicode_fractions
    :dedent: 4


``_replace_fake_fractions``
+++++++++++++++++++++++++++

Fractions represented in a textual format (e.g. 1/2, 3/4) are replaced with decimals.

A regular expression is used to find these in the sentence. The regular expression also matches fractions greater than 1 (e.g. 1 1/2 is 1.5).

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :lines: 13-16

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_fake_fractions
    :dedent: 4


``_split_quantity_and_units``
+++++++++++++++++++++++++++++

A space is enforced between quantities and units to make sure they are tokenized to separate tokens.
The regular expression that does this is quite simple.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :lines: 21-23

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._split_quantity_and_units
    :dedent: 4

``_replace_string_range``
+++++++++++++++++++++++++

Ranges are replaced with a standardised form of X-Y. The regular expression that searches for ranges in the sentence matches anything in the following forms:

* 1 to 2
* 1- to 2-
* 1 or 2
* 1- to 2-

where the numbers 1 and 2 represent any decimal value.

The purpose of this is to ensure the range is kept as a single token.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :lines: 28-33

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_string_range
    :dedent: 4


``_singlarise_unit``
++++++++++++++++++++

Units are made singular. This is done using a predefined list of plural units and their singular form.

.. literalinclude:: ../../../ingredient_parser/_constants.py
    :lines: 5-83

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._singlarise_unit
    :dedent: 4

2. Tokenize the cleaned sentence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the input has been cleaned, it can be split into tokens. Each token represents a single unit of the sentence. These are not necessarily the same as a word because we might want to handle punctuation and compound words in particular ways.

The tokenizer in created using NLTK's Regular Expression tokenizer. The splits an string input according the a regular expression.

The defined tokenizer splits the sentence according the following rules.

* Word characters, full stops, hyphens and apostrophes that are adjacent are kept together as a token.
    This effectively converts word to tokens, with some special cases like keeping ranges as a single token.
* Open and closing parentheses become tokens on their own.
    Parentheses are difficult to handle because they can appear directly adjacent to word, so we separate them into tokens on their own.
* Commas become a token.
    Same argument as for parentheses.
* Double quotes/speech marks become a token.
    Double quotes can be a unit (inch), which we would to identify.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :lines: 35-38

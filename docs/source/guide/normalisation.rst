Normalisation
=============

Normalisation is the process of transforming the sentences to ensure that particular features of the sentence have a standard form. This pre-process step is there to remove as much of the variation in the data that can be reasonably foreseen, so that the model is presented with tidy and consistent data and therefore has an easier time of learning or labelling.

The :class:`PreProcessor` class handles the sentence normalisation for us. 

.. code:: python

    >>> from Preprocess import PreProcessor
    >>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
    >>> p.sentence
    '0.5 cup orange juice, freshly squeezed'

The normalisation of the input sentence is done immediately when the :class:`PreProcessor` class is instantiated. The :func:`_normalise` method of the :class:`PreProcessor` class is called, which executes a number of steps to clean up the input sentence.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._normalise
    :dedent: 4

.. tip::

    By setting ``show_debug_output=True`` when instantiating the :class:`PreProcessor` class, the sentence will be printed out at each step of the normalisation process.

Each of the normalisation functions are detailed below.


``_replace_en_em_dash``
^^^^^^^^^^^^^^^^^^^^^^^

En-dashes and em-dashes are replaced with hyphens.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_en_em_dash
    :dedent: 4


``_replace_string_numbers``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Numbers represented in textual form e.g. "one", "two" are replaced with numeric forms.
The replacements are predefined in a dictionary.
For performance reasons, the regular expressions used to substitute the text with the number are precomiled and provided in the ``STRING_NUMBERS_REGEXES`` constant, which is a dictionary where the value is a tuple of (precompiled regex, substitute value).

.. literalinclude:: ../../../ingredient_parser/_constants.py
    :lines: 140-167
    

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_string_numbers
    :dedent: 4

``_replace_html_fractions``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Fractions represented by html entities (e.g. 0.5 as ``&frac12;``) are replaced with Unicode equivalents (e.g. ½). This is done using the standard library ``html.unescape`` function.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_html_fractions
    :dedent: 4


``_replace_unicode_fractions``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Fractions represented by Unicode fractions are replaced a textual format (.e.g ½ as 1/2), as defined by the dictionary in this function. The next step (``_replace_fake_fractions``) will turn these into decimal numbers.

We have to handle two cases: where the character before the unicode fraction is a hyphen and where it is not. In the latter case, we want to insert a space before the replacement so we don't accidently merge with the character before. However, if the character before is a hyphen, we don't want to do this because we could end up splitting a range up.

.. literalinclude:: ../../../ingredient_parser/_constants.py
    :lines: 169-205

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_unicode_fractions
    :dedent: 4

``_combine_quantities_split_by_and``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Fractional quantities split by 'and' e.g. 1 and 1/2 are replaced by the decimal equivalent.

A regular expression is used to find these in the sentence.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :lines: 41-43

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._combine_quantities_split_by_and
    :dedent: 4


``_replace_fake_fractions``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Fractions represented in a textual format (e.g. 1/2, 3/4) are replaced with decimals.

A regular expression is used to find these in the sentence. The regular expression also matches fractions greater than 1 (e.g. 1 1/2 is 1.5).

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :lines: 18-21

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_fake_fractions
    :dedent: 4


``_split_quantity_and_units``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A space is enforced between quantities and units to make sure they are tokenized to separate tokens. If an quantity and unit are joined by a hyphen, this is also replaced by a space.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :lines: 26-30

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._split_quantity_and_units
    :dedent: 4


``_remove_unit_trailing_period``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Units with a trailing period have the period removed. This is only done for a subset of units where this has been observed.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._remove_unit_trailing_period
    :dedent: 4


``_replace_string_range``
^^^^^^^^^^^^^^^^^^^^^^^^^

Ranges are replaced with a standardised form of X-Y. The regular expression that searches for ranges in the sentence matches anything in the following forms:

* 1 to 2
* 1- to 2-
* 1 or 2
* 1- to 2-

where the numbers 1 and 2 represent any decimal value.

The purpose of this is to ensure the range is kept as a single token.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :lines: 35-39

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._replace_string_range
    :dedent: 4


``_singlarise_unit``
^^^^^^^^^^^^^^^^^^^^

Units are made singular using a predefined list of plural units and their singular form.

This step is actually performed after tokenisation (see :doc:`Extracting the features <features>`) and we keep track of the index of each token that has been singularised. This is so we can automatically re-pluralise only the tokens that were singularised after the labeling by the model.

.. literalinclude:: ../../../ingredient_parser/_constants.py
    :lines: 5-102

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._singlarise_units
    :dedent: 4

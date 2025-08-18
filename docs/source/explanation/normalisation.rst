.. currentmodule:: ingredient_parser.en.preprocess
.. _reference-explanation-normalisation:

Sentence Normalisation
======================

Normalisation is the process of transforming the sentences to ensure that particular features of the sentence have a standardised form.
This pre-processing step is there to remove as much of the variation in the data that can be reasonably foreseen, so that the model is presented with tidy and consistent data and therefore has an easier time assigning the correct labels.

The :class:`PreProcessor` class handles the sentence normalisation.

.. code:: python

    >>> from Preprocess import PreProcessor
    >>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
    >>> p.sentence
    '#1$2 cup orange juice, freshly squeezed'

The normalisation of the input sentence is done on initialisation of a :class:`PreProcessor` object. The :func:`_normalise` method of the :class:`PreProcessor` class is called, which executes a number of steps to clean up the input sentence.

.. literalinclude:: ../../../ingredient_parser/en/preprocess.py
    :pyobject: PreProcessor._normalise
    :dedent: 4

.. tip::

    By setting ``show_debug_output=True`` when instantiating a :class:`PreProcessor` object, the sentence will be printed out at each step of the normalisation process.

Each of the normalisation steps is described below.

#. ``_replace_en_em_dash``

   En-dashes (`–`) and em-dashes (`—`) are replaced with hyphens (`-`). This makes identification of ranges of quantities easier.

#. ``_replace_html_fractions``

   Fractions written as html entities (e.g. ``&frac12;`` for 0.5) are replaced with Unicode equivalents (e.g. ½).
   This is done using the standard library's :func:`html.unescape` function.

#. ``_replace_unicode_fractions``

   Fractions represented by Unicode fractions are replaced a textual format (.e.g ½ as 1/2), as defined by the dictionary in this function.
   Because we replaced the html fractions in the previous step, these are also converted here too.

   There are two cases to consider: where the character before the unicode fraction is a hyphen and where it is not.

   In the second case, we insert a space before the replacement so we don't accidentally merge with the character before.
   For example we want **1½** to become **1 1/2** and not **11/2**.

   However, if the character before is a hyphen, we don't want to do this because we could end up splitting a range up.
   For example, we want **½-¾** to become **1/2-3/4** and not **1/2- 3/4** (note the space before the 3).

#. ``combine_quantities_split_by_and``

   Fractional quantities split by 'and' e.g. 1 and 1/2 are converted to the format described in the next step.
   We do this now instead of later to avoid treating the 1/2 on it's own.

#. ``_identify_fractions``

   All remaining fractions are modified so that they survive tokenisation as a single token.
   This is necessary so that we can convert them to :class:`fractions.Fraction` objects later.

   For fractions less than 1, the forward slash is replaced by ``$`` and a ``#`` is prepended e.g. **1/2** becomes **#1$2**.

   For fractions greater than 1, the forward slash is replaced by ``$`` and a ``#`` is inserted between the integer and the fraction e.g. **2 3/4** becomes **2#3$4**.

#. ``_split_quantity_and_units``

   A space is enforced between quantities and units to make sure they are tokenized to separate tokens.
   If a quantity and unit are joined by a hyphen, this is also replaced by a space.
   This takes into account certain strings that aren't technically units, but we want to treat in the same way here, for example **x** in the context **1x** or **2x**.

#. ``_remove_unit_trailing_period``

   Units with a trailing period have the period removed.
   This is only done for a subset of units where this has been observed in the model training data.

#. ``replace_string_range``

   Ranges are replaced with a standardised form of **X-Y**.
   A regular expression searches for ranges in the sentence that match anything in the following forms:

   * 1 to 2
   * 1- to 2-
   * 1 or 2
   * 1- or 2-

   where the numbers 1 and 2 represent any decimal value or fraction as modified above.

   The purpose of this is to ensure the range is kept as a single token.

#. ``_replace_dupe_units_ranges``

   Ranges where the unit is given for both quantities are replaced with the standardised range format, e.g. **5 oz - 8 oz** is replaced by **5-8 oz**.
   Cases where the same unit is used but in different forms (e.g. 5 oz - 8 ounce) are also considered for the unit synonyms defined in the ``UNIT_SYNONYMS`` constant.


#. ``_merge_quantity_x``

   Quantities followed by an "x" are merged together so they form a single token, for example:

   * 1 x -> 1x
   * 0.5 x -> 0.5x

#. ``_collapse_ranges``

   Remove any white space surrounding the hyphen in a range


Singularising units
^^^^^^^^^^^^^^^^^^^

Units are converted to their singular form, using a predefined list of plural units and their singular form.
This step is actually performed after tokenisation so that we can keep track of the index of each token that has been modified.
This is so we can automatically re-pluralise only the tokens that were singularised after the labelling by the model.

.. currentmodule:: ingredient_parser.dataclasses

Post-processing
===============

The output from the model is a list of labels and a list of scores, one of each for every token in the input sentence.
This needs to be turned into a more useful data structure so that the output can be used by the users of this library.

The :class:`ParsedIngredient` class defines the structure of the returned information from the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function:

.. literalinclude:: ../../../ingredient_parser/dataclasses.py
    :pyobject: ParsedIngredient
    :end-before: def

Each of the fields in the dataclass has to be determined from the output of the model. The :class:`PostProcessor <ingredient_parser.en.postprocess.PostProcessor>` class handles this for us.

Size, Preparation, Purpose, Comment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For each of the labels SIZE, PREP, PURPOSE and COMMENT, the associated tokens are combined into an :class:`IngredientText` object.

.. literalinclude:: ../../../ingredient_parser/dataclasses.py
    :pyobject: IngredientText

The post-processing steps are as follows:

#. Find the indices for the label under consideration, plus the PUNC label.
#. Group these indices into lists of consecutive indices.
#. Join the tokens corresponding to each group of consecutive indices with a space.
#. If ``discard_isolated_stop_words`` is True, discard any groups that just comprise a word from the list of stop words.
#. Average the confidence scores for each the tokens in each group consecutive indices.
#. Remove any isolated or invalid punctuation and any consecutive tokens that are identical.
#. Join all the groups together with a comma and fix any weird punctuation this causes.
#. Average the confidence scores across all groups.

The output of this processing is an :class:`IngredientText` object for each label, which contains the text string, the confidence score, and the starting index of the string in the ingredient sentence.

Name
^^^^

The post-processing to obtain the ingredient names is similar to above, but with a couple of extra steps before the steps listed above used to identify the different ingredient names.

#. Find the indices for all B_NAME_TOK, I_NAME_TOK, NAME_VAR, NAME_MOD, NAME_SEP and PUNC labels
#. Group indices with the same label together.
   When grouping, B_NAME_TOK and I_NAME_TOK are also grouped together, with each B_NAME_TOK starting a new group.
#. Iterate through the groups in reverse, applying the following rules:

   #. Each NAME_VAR group is prepended to the beginning of the previous B_NAME_TOK group.
   #. Each NAME_MOD group is prepended to all previous B_NAME_TOK or NAME_VAR+B_NAME_TOK groups.

#. Post-process these groups of indices as above, noting that the first two steps are already completed.

The output of this function is a list of :class:`IngredientText` objects, one for each ingredient names.

If ``separate_names`` is set to False, then all the NAME_* label types are treated as a single NAME label and the post-processing is the same for the SIZE, PREP, PURPOSE and COMMENT labels.
This will return a single :class:`IngredientText` object.

Amount
^^^^^^

The QTY and UNIT labels are combined into an :class:`IngredientAmount` object.

.. literalinclude:: ../../../ingredient_parser/dataclasses.py
    :pyobject: IngredientAmount
    :end-before: def

For most cases, the amounts are determined by combining a QTY label with the following UNIT labels, up to the next QTY which becomes a new amount.
For example:

.. code:: python

    >>> p = PreProcessor("3/4 cup (170g) heavy cream")
    >>> p.tokenized_sentence
    ['0.75', 'cup', '(', '170', 'g', ')', 'heavy', 'cream']
    ...
    >>> parsed = PostProcessor(sentence, tokens, labels, scores).parsed()
    >>> amounts = parsed.amount
    [
        IngredientAmount(quantity=Fraction(3, 4),
                  quantity_max=Fraction(3, 4),
                  unit=<Unit('cup')>,
                  text='0.75 cups',
                  confidence=0.999881,
                  APPROXIMATE=False,
                  SINGULAR=False,
                  RANGE=False,
                  MULTIPLIER=False,
                  PREPARED_INGREDIENT=False),
        IngredientAmount(quantity=Fraction(170, 1),
                  quantity_max=Fraction(170, 1),
                  unit=<Unit('gram')>,
                  text='170 g',
                  confidence=0.995941,
                  APPROXIMATE=False,
                  SINGULAR=False,
                  RANGE=False,
                  MULTIPLIER=False,
                  PREPARED_INGREDIENT=False)
    ]

Quantities
++++++++++

Quantities are returned as :class:`fractions.Fraction` objects, or ``str`` for non-numeric quantities (e.g. dozen).

.. code:: python

    >>> parsed = parse_ingredient("1/3 cup oil", quantity_fractions=True)
    >>> parsed.amount.quantity
    Fraction(1, 3)


.. note::

    Conversion of quantities to float or int is left to the end users of this library.

Tokens with the QTY label that are numbers represented in textual form e.g. "one", "two" are replaced with numeric forms.
The replacements are predefined in the ``STRING_NUMBERS`` constant.
For performance reasons, the regular expressions used to substitute the text with the number are pre-compiled and provided in the ``STRING_NUMBERS_REGEXES`` constant, which is a dictionary where the value is a tuple of (pre-compiled regular expression, substitute value).

.. literalinclude:: ../../../ingredient_parser/en/_constants.py
    :lines: 166-198

Units
+++++

.. note::

    The use of :class:`pint.Unit` objects can be disabled by setting ``string_units=True`` in the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function. When this is True, units will be returned as strings, correctly pluralised for the quantity.

The `Pint <https://pint.readthedocs.io/en/stable/>`_ library is used to standardise the units where possible.
If the unit in a parsed :class:`IngredientAmount` can be matched to a unit in the Pint Unit Registry, then a :class:`pint.Unit` object is used in place of the unit string.

This has the benefit of standardising units that can be represented in different formats, for example a `gram` could be represented in the sentence as `g`, `gram`, `grams`.
These will all be represented using the same ``<Unit('gram')>`` object in the parsed information.

By default, US customary units are used where a unit has more than one definition. This can be changed to use the Imperial unit by setting ``imperial_units=True`` in the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function call.

.. code:: python

    >>> parse_ingredient("3/4 cup heavy cream", imperial_units=False)  # Default
    ParsedIngredient(
        name=IngredientText(text='heavy cream', confidence=0.997513),
        size=None,
        amount=[IngredientAmount(quantity=Fraction(3, 4),
                                 quantity_max=Fraction(3, 4),
                                 unit=<Unit('cup')>,
                                 text='0.75 cups',
                                 confidence=0.999926,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False,
                                 PREPARED_INGREDIENT=False)],
        preparation=None,
        comment=None,
        sentence='3/4 cup heavy cream'
    )

    >>> parse_ingredient("3/4 cup heavy cream", imperial_units=True)
    ParsedIngredient(
        name=IngredientText(text='heavy cream', confidence=0.997513),
        size=None,
        amount=[IngredientAmount(quantity=Fraction(3, 4),
                                 quantity_max=Fraction(3, 4),
                                 unit=<Unit('imperial_cup')>,
                                 text='0.75 cups',
                                 confidence=0.999926,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False,
                                 PREPARED_INGREDIENT=False)],
        preparation=None,
        comment=None,
        sentence='3/4 cup heavy cream'
    )

.. tip::

    The use of :class:`pint.Unit` objects means that the ingredient amounts can easily be converted to different units.
    See the :doc:`Convert between units </how-to/convert-units>` how-to guide.

IngredientAmount flags
++++++++++++++++++++++

:class:`IngredientAmount` objects have a number of flags that are set to provide additional information about the amount.

+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| Flag                    | Description                                                                                                                                         |
+=========================+=====================================================================================================================================================+
| **APPROXIMATE**         | This is set to True when the QTY is preceded by a word such as `about`, `approximately` and indicates if the amount is approximate.                 |
+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| **SINGULAR**            | This is set to True when the amount is followed by a word such as `each` and indicates that the amount refers to a singular item of the ingredient. |
|                         |                                                                                                                                                     |
|                         | There is also a special case (below), where an inner amount that inside a QTY-UNIT pair will be marked as SINGULAR.                                 |
+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| **RANGE**               | This is set to True with the amount if a range of values, e.g. 1-2, 300-400.                                                                        |
|                         | In these cases, the ``quantity`` field of the :class:`IngredientAmount` object is set to the lower value in the range                               |
|                         | and ``quantity_max`` is the upper end of the range.                                                                                                 |
+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| **MULTUPLIER**          | This is set to True when the amount is represented as a multiple such as 1x.                                                                        |
|                         | The ``quantity`` field in set to the value of the multiplier (e.g. for ``1x`` the quantity is  ``1``).                                              |
+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| **PREPARED_INGREDIENT** | This is set to True when the amount refers to the ingredient after any preparation instructions in the ingredient sentence have been followed.      |
|                         |                                                                                                                                                     |
|                         | For example in the sentence **1 tbsp chopped nuts**, we would want 1 tablespoon of nuts, measured after they have been chopped.                     |
|                         | If the sentence was **1 tbsp nuts, chopped**, we would want to chop the nuts after we have measured 1 tablespoon.                                   |
+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+


Special cases for amounts
+++++++++++++++++++++++++

There are some particular cases where the combination of QTY and UNIT labels that make up an amount are not straightforward.
For example, consider the sentence **2 14 ounce cans coconut milk**.
In this case there are two amounts: **2 cans** and **14 ounce**, where the latter is marked as **SINGULAR** because it applies to each of the 2 cans.

.. code:: python

    >>> parsed = parse_ingredient("2 14 ounce cans coconut milk")
    >>> parsed.amount
    [IngredientAmount(quantity=Fraction(2, 1),
                      quantity_max=Fraction(2, 1),
                      unit='cans',
                      text='2 cans',
                      confidence=0.999897,
                      APPROXIMATE=False,
                      SINGULAR=False,
                      RANGE=False,
                      MULTIPLIER=False,
                      PREPARED_INGREDIENT=False),
     IngredientAmount(quantity=Fraction(14, 1),
                      quantity_max=Fraction(14, 1),
                      unit=<Unit('ounce')>,
                      text='14 ounces',
                      confidence=0.998793,
                      APPROXIMATE=False,
                      SINGULAR=True,
                      RANGE=False,
                      MULTIPLIER=False,
                      PREPARED_INGREDIENT=False)]


Identifying and handling this pattern of QTY and UNIT labels is done by the :func:`PostProcessor._sizable_unit_pattern` function.

A second case is where the full amount is made up of more than one adjacent quantity-unit pair.
This is particularly common with US customary units such as pounds and ounces, or pints and fluid ounces.
In these cases, a :class:`CompositeIngredientAmount <ingredient_parser.dataclasses.CompositeIngredientAmount>` is returned.
For example

.. code:: python

    >>> parsed = parse_ingredient("1lb 2oz pecorino romano cheese")
    >>> parsed.amount
    [CompositeIngredientAmount(
        amounts=[
            IngredientAmount(quantity=Fraction(1, 1),
                             quantity_max=Fraction(1, 1),
                             unit=<Unit('pound')>,
                             text='1 lb',
                             confidence=0.999923,
                             starting_index=0,
                             APPROXIMATE=False,
                             SINGULAR=False,
                             RANGE=False,
                             MULTIPLIER=False,
                             PREPARED_INGREDIENT=False),
            IngredientAmount(quantity=Fraction(1, 1),
                             quantity_max=Fraction(1, 1),
                             unit=<Unit('ounce')>,
                             text='2 oz',
                             confidence=0.998968,
                             starting_index=2,
                             APPROXIMATE=False,
                             SINGULAR=False,
                             RANGE=False,
                             MULTIPLIER=False,
                             PREPARED_INGREDIENT=False)],
        join='',
        subtractive=False,
        text='1 lb 2 oz',
        confidence=0.9994455,
        starting_index=0
    )]

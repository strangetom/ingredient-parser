.. currentmodule:: ingredient_parser.dataclasses

Post-processing the model output
================================

The output from the model is a list of labels and scores, one for each token in the input sentence. This needs to be turned into a more useful data structure so that the output can be used by the users of this library.

The following dataclass is defined which will be output from the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function:

.. literalinclude:: ../../../ingredient_parser/dataclasses.py
    :pyobject: ParsedIngredient

Each of the fields in the dataclass has to be determined from the output of the model. The :class:`PostProcessor` class handles this for us.

Name, Size, Preparation, Purpose, Comment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For each of the labels NAME, SIZE, PREP, PURPOSE and COMMENT, the process of combining the tokens for each labels is the same.

The general steps are as follows:

1. Find the indices of the labels under consideration.
2. Group these indices into lists of consecutive indices.
3. Join the tokens corresponding to each group of consecutive indices with a space.
4. If ``discard_isolated_stop_words`` is True, discard any groups that just comprise a word from the list of stop words.
5. Average the confidence scores for each the tokens in each group consecutive indices.
6. Remove any isolated punctuation or any consecutive tokens that are identical.
7. Join all the groups together with a comma and fix any weird punctuation this causes.
8. Average the confidence scores across all groups.

.. literalinclude:: ../../../ingredient_parser/en/postprocess.py
    :pyobject: PostProcessor._postprocess

The output of this function is an :class:`IngredientText` object:

.. literalinclude:: ../../../ingredient_parser/dataclasses.py
    :pyobject: IngredientText

Amount
^^^^^^

The QTY and UNIT labels are combined into an :class:`IngredientAmount` object

.. literalinclude:: ../../../ingredient_parser/dataclasses.py
    :pyobject: IngredientAmount

For most cases, the amounts are determined by combining a QTY label with the following UNIT labels, up to the next QTY which becomes a new amount. For example:

.. code:: python

    >>> p = PreProcessor("3/4 cup (170g) heavy cream")
    >>> p.tokenized_sentence
    ['0.75', 'cup', '(', '170', 'g', ')', 'heavy', 'cream']
    ...
    >>> parsed = PostProcessor(sentence, tokens, labels, scores).parsed()
    >>> amounts = parsed.amount
    [
        IngredientAmount(quantity=0.75,
                  quantity_max=0.75,
                  unit=<Unit('cup')>,
                  text='0.75 cups',
                  confidence=0.999881,
                  APPROXIMATE=False,
                  SINGULAR=False,
                  RANGE=False,
                  MULTIPLIER=False),
        IngredientAmount(quantity=170.0,
                  quantity_max=170.0,
                  unit=<Unit('gram')>,
                  text='170 g',
                  confidence=0.995941,
                  APPROXIMATE=False,
                  SINGULAR=False,
                  RANGE=False,
                  MULTIPLIER=False)
    ]

Tokens with the QTY label that are numbers represented in textual form e.g. "one", "two" are replaced with numeric forms.
The replacements are predefined in a dictionary.
For performance reasons, the regular expressions used to substitute the text with the number are pre-compiled and provided in the ``STRING_NUMBERS_REGEXES`` constant, which is a dictionary where the value is a tuple of (pre-compiled regular expression, substitute value).

.. literalinclude:: ../../../ingredient_parser/en/_constants.py
    :lines: 155-187

.. literalinclude:: ../../../ingredient_parser/en/postprocess.py
    :pyobject: PostProcessor._replace_string_numbers
    :dedent: 4


There are two amounts identified: **0.75 cups** and **170 g**.

Units
+++++

.. note::

    The use of :class:`pint.Unit` objects can be disabled by setting ``string_units=True`` in the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function. When this is True, units will be returned as strings, correctly pluralised for the quantity.

The `pint <https://pint.readthedocs.io/en/stable/>`_ library is used to standardise the units where possible. If the unit in a parsed :class:`IngredientAmount` can be matched to a unit in the pint Unit Registry, then a :class:`pint.Unit` object is used in place of the unit string.

This has the benefit of standardising units that can be represented in different formats, for example a `gram` could be represented in the sentence as `g`, `gram`, `grams`. These will all be represented using the same ``<Unit('gram')>`` object in the parsed information.

This has benefits if you wish to use the parsed information to convert between different units. For example:

.. code:: python

    >>> p = parse_ingredient("3/4 cup heavy cream")
    >>> q = p.amount[0].quantity * p.amount[0].unit
    >>> q
    0.75 <Unit('cup')>
    >>> q.to("ml")
    177.44117737499994 <Unit('milliliter')>

By default, US customary version of units are used where a unit has more than one definition. This can be changed to use the Imperial definition by setting ``imperial_units=True`` in the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function call.

.. code:: python

    >>> parse_ingredient("3/4 cup heavy cream", imperial_units=False)  # Default
    ParsedIngredient(
        name=IngredientText(text='heavy cream', confidence=0.997513),
        size=None,
        amount=[IngredientAmount(quantity=0.75,
                                 quantity_max=0.75,
                                 unit=<Unit('cup')>,
                                 text='0.75 cups',
                                 confidence=0.999926,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False)],
        preparation=None,
        comment=None,
        sentence='3/4 cup heavy cream'
    )

    >>> parse_ingredient("3/4 cup heavy cream", imperial_units=True)
    ParsedIngredient(
        name=IngredientText(text='heavy cream', confidence=0.997513),
        size=None,
        amount=[IngredientAmount(quantity=0.75,
                                 quantity_max=0.75,
                                 unit=<Unit('imperial_cup')>,
                                 text='0.75 cups',
                                 confidence=0.999926,
                                 APPROXIMATE=False,
                                 SINGULAR=False,
                                 RANGE=False,
                                 MULTIPLIER=False)],
        preparation=None,
        comment=None,
        sentence='3/4 cup heavy cream'
    )

.. tip::

    The use of :class:`pint.Unit` objects means that the ingredient amounts can easily be converted to different units.

    .. code:: python

       >>> parsed = parse_ingredient("3 pounds beef brisket")
       >>> # Create a pint.Quantity object from the quantity and unit
       >>> q = parsed.amount[0].quantity * parsed.amount[0].unit
       >>> q
       3.0 <Unit('pound')>

       >>> # Convert to kg
       >>> q.to("kg")
       1.3607771100000003 <Unit('kilogram')>

IngredientAmount flags
++++++++++++++++++++++

:class:`IngredientAmount` objects have a number of flags that can be set.

**APPROXIMATE**

This is set to True when the QTY is preceded by a word such as `about`, `approximately` and indicates if the amount is approximate.

**SINGULAR**

This is set to True when the amount is followed by a word such as `each` and indicates that the amount refers to a singular item of the ingredient.

There is also a special case (below), where an inner amount that inside a QTY-UNIT pair will be marked as SINGULAR.

**RANGE**

This is set to True with the amount if a range of values, e.g. 1-2, 300-400. In these cases, the ``quantity`` field of the :class:`IngredientAmount` object is set to the lower value in the range and ``quantity_max`` is the upper end of the range.

**MULTIPLIER**

This is set to True when the amount is represented as a multiple such as 1x. The ``quantity`` field in set to the value of the multiplier (e.g. for ``1x`` the quantity is  ``1``).

Special cases for amounts
+++++++++++++++++++++++++

There are some particular cases where the combination of QTY and UNIT labels that make up an amount are not straightforward. For example, consider the sentence **2 14 ounce cans coconut milk**. In this case there are two amounts: **2 cans** and **14 ounce**, where the latter is marked as **SINGULAR** because it applies to each of the 2 cans.

.. code:: python

    >>> parsed = parse_ingredient("2 14 ounce cans coconut milk")
    >>> parsed.amount
    [IngredientAmount(quantity=2.0,
                      quantity_max=2.0,
                      unit='cans',
                      text='2 cans',
                      confidence=0.999897,
                      APPROXIMATE=False,
                      SINGULAR=False,
                      RANGE=False,
                      MULTIPLIER=False),
     IngredientAmount(quantity=14.0,
                      quantity_max=14.0,
                      unit=<Unit('ounce')>,
                      text='14 ounces',
                      confidence=0.998793,
                      APPROXIMATE=False,
                      SINGULAR=True,
                      RANGE=False,
                      MULTIPLIER=False)]


Identifying and handling this pattern of QTY and UNIT labels is done by the :func:`PostProcessor._sizable_unit_pattern()` function.

A second case is where the full amount is made up of more than one quantity-unit pair. This is particularly common with US customary units such as pounds and ounces, or pints and fluid ounces. In these cases, a :class:`CompositeIngredientAmount <ingredient_parser.dataclasses.CompositeIngredientAmount>` is returned. For example

.. code:: python

    >>> parsed = parse_ingredient("1lb 2oz pecorino romano cheese")
    >>> parsed.amount
    [CompositeIngredientAmount(
        amounts=[
            IngredientAmount(quantity=1.0,
                             quantity_max=1.0,
                             unit=<Unit('pound')>,
                             text='1 lb',
                             confidence=0.999923,
                             starting_index=0,
                             APPROXIMATE=False,
                             SINGULAR=False,
                             RANGE=False,
                             MULTIPLIER=False),
            IngredientAmount(quantity=2.0,
                             quantity_max=2.0,
                             unit=<Unit('ounce')>,
                             text='2 oz',
                             confidence=0.998968,
                             starting_index=2,
                             APPROXIMATE=False,
                             SINGULAR=False,
                             RANGE=False,
                             MULTIPLIER=False)],
        join='',
        subtractive=False,
        text='1 lb 2 oz',
        confidence=0.9994455,
        starting_index=0
    )]


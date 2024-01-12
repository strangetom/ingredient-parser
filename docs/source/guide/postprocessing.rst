Post-processing the model output
================================

The output from the model is a list of labels and scores, one for each token in the input sentence. This needs to be turned into a more useful data structure so that the output can be used by the users of this library.

The following dataclass is defined which will be output from the ``parse_ingredient`` function:

.. literalinclude:: ../../../ingredient_parser/postprocess.py
    :pyobject: ParsedIngredient

Each of the fields in the dataclass has to be determined from the output of the model. The :class:`PostProcessor` class handles this for us. 

Name, Preparation, Comment
^^^^^^^^^^^^^^^^^^^^^^^^^^

For each of the labels NAME, PREP, and COMMENT, the process of combining the tokens for each labels is the same.

The general steps are as follows:

1. Find the indices of the labels under consideration.
2. Group these indices into lists of consecutive indices.
3. Join the tokens corresponding to each group of consecutive indices with a space.
4. If ``discard_isolated_stop_words`` is True, discard any groups that just comprise a word from the list of stop words. 
5. Average the confidence scores for each the tokens in each group consecutive indices.
6. Remove any isolated punctuation or any consecutive tokens that are identical.
7. Join all the groups together with a comma and fix any weird punctuation this causes.
8. Average the confidence scores across all groups.

.. literalinclude:: ../../../ingredient_parser/postprocess.py
    :pyobject: PostProcessor._postprocess

The output of this function is an :class:`IngredientText` object:

.. literalinclude:: ../../../ingredient_parser/postprocess.py
    :pyobject: IngredientText

Amount
^^^^^^

The QTY and UNIT labels are combined into an :class:`IngredientAmount` object

.. literalinclude:: ../../../ingredient_parser/postprocess.py
    :pyobject: IngredientAmount

For most cases, the amounts are determined by combining a QTY label with the following UNIT labels, up to the next QTY which becomes a new amount. For example:

.. code:: python

    >>> p = PreProcessor("3/4 cup (170g) heavy cream")
    >>> p.tokenized_sentence
    ['0.75', 'cup', '(', '170', 'g', ')', 'heavy', 'cream']
    ...
    >>> parsed = PostProcessor(sentence, tokens, labels, scores).parsed()
    >>> amounts = parsed.amount
    [IngredientAmount(quantity='0.75', unit='cups', text='0.75 cups', confidence=0.999426, APPROXIMATE=False, SINGULAR=False),
    IngredientAmount(quantity='170', unit='g', text='170 g', confidence=0.909345, APPROXIMATE=False, SINGULAR=False)]

There are two amounts identified: **0.75 cups** and **170 g**.

IngredientAmount flags
++++++++++++++++++++++

:class:`IngredientAmount` objects have a number of flags that can be set.

**APPROXIMATE**

This is set to True when the QTY is preceded by a word such as `about`, `approximately` and indicates if the amount is approximate.

**SINGULAR**

This is set to True when the amount is followed by a word such as `each` and indicates that the amount refers to a singular item of the ingredient.

There is also a special case (below), where an inner amount that inside a QTY-UNIT pair will be marked as SINGULAR.

Special cases for amounts
+++++++++++++++++++++++++

There are some particular cases where the combination of QTY and UNIT labels that make up an amount are not straightforward. For example, consider the sentence **2 14 ounce cans coconut milk**. In this case there are two amounts: **2 cans** and **14 ounce**, where the latter is also singular.

.. code:: python

    >>> p = PreProcessor("2 14 ounce cans coconut milk")
    >>> p.tokenized_sentence
    ['2', '14', 'ounce', 'can', 'coconut', 'milk']
    ...
    >>> parsed = PostProcessor(sentence, tokens, labels, scores).parsed()
    >>> amounts = parsed.amount
    [IngredientAmount(quantity='2', unit='cans', text='2 cans', confidence=0.9901127131948666, APPROXIMATE=False, SINGULAR=False),
    IngredientAmount(quantity='14', unit='ounces', text='14 ounces', confidence=0.979053978856428, APPROXIMATE=False, SINGULAR=True)]

Identifying and handling this pattern of QTY and UNIT labels is done by the :func:`PostProcessor._sizable_unit_pattern()` function.
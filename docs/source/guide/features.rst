.. currentmodule:: ingredient_parser.en.preprocess

Feature selection
=================

Feature calculation is done for each token in the sentence, so first the normalised sentence must be tokenised.

Tokenization
^^^^^^^^^^^^

Once the input sentence has been normalised, it can be split into tokens. Each token represents a single unit of the sentence. These are not necessarily the same as the words because we might want to handle punctuation and compound words in a particular way.

The tokenizer splits the sentence according the following rules:

.. literalinclude:: ../../../ingredient_parser/en/_utils.py
    :lines: 29-68

This splits the sentence apart into wherever there is white space or a punctuation mark in ``PUNCTUATION_TOKENISER``.

.. code:: python

    >>> from Preprocess import PreProcessor
    >>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
    >>> p.tokenised_sentence
    ['0.5', 'cup', 'orange', 'juice', ',', 'freshly', 'squeezed']

At this stage, any numeric tokens are replaced with ``!num``. This is so that the model doesn't need to learn lots of different values that are numeric, which helps improve performance and reduce model size.

Feature Calculation
^^^^^^^^^^^^^^^^^^^

The features for each of each token in each sentence need to be selected and extracted.

There are quite a wide range of features that can be extracted for each token and it can be difficult to tell if a particular feature is useful or not.

The `Ingredient Phrase Tagger <https://github.com/NYTimes/ingredient-phrase-tagger>`_ approach to features was to use the following:

* The token itself
* The position of the token in the sentence, as an index
* The number of tokens in the sentence, but rounded down to the nearest group in [4, 8, 12, 16, 20]
* Whether the token starts with a capital letter
* Whether the token is inside parentheses in the sentence

The features used for this model are a little different

* The stem of the token
* The part of speech (:abbr:`POS (Part of Speech)`) tag
* Whether the token is capitalised
* Whether the token is numeric
* Whether the token is a unit (determined from the list of units)
* Whether the token is a punctuation mark
* Whether the token is an ambiguous unit
* Whether the token is inside parentheses
* Whether the token is after a comma
* Whether the token follows a + symbol
* Whether the sentence is a short sentence (having less than 3 tokens)

If possible, based on the position of the token in the sentence, the following features are also added

* The stem of the previous token
* The :abbr:`POS (Part of Speech)` tag for the previous token combined with the :abbr:`POS (Part of Speech)` tag for the current token
* The stem of the token before the previous token
* The :abbr:`POS (Part of Speech)` tag for the token before the previous token combined with the :abbr:`POS (Part of Speech)` tags for the previous and current tokens
* The stem of the next token
* The :abbr:`POS (Part of Speech)` tag for the next token combined with the :abbr:`POS (Part of Speech)` tag for the current token
* The stem of the token after the next token
* The :abbr:`POS (Part of Speech)` tag for the token after the next token combined with the :abbr:`POS (Part of Speech)` tags for the current and next tokens

The :func:`_token_features` function of :class:`PreProcessor` returns all these features as a dictionary.

.. literalinclude:: ../../../ingredient_parser/en/preprocess.py
    :pyobject: PreProcessor._token_features
    :dedent: 4

The :func:`sentence_features` function of :class:`PreProcessor` return the features for all tokens in the sentence in a list.

.. attention::

    It is likely that some of these features aren't necessary. There is a chunk of work for the future to determine the most useful features.

Feature Selection
=================

The features for each of each token in each sentence need to be selected and extracted.

There are quite a wide range of features that can be extracted for each token and it can be difficult to tell if a particular feature is useful or not.

The `Ingredient Phrase Tagger <https://github.com/NYTimes/ingredient-phrase-tagger>`_ approach to features was to use the following:

* The token itself
* The position of the token in the sentence, as an index
* The number of tokens in the sentence, but rounded down to the nearest group in [4, 8, 12, 16, 20]
* Whether the token starts with a capital letter
* Whether the token is inside parentheses in the sentence

The features used for this model are a little different

* The token
* The part of speech (POS) tag
* The combined POS tags for the previous and current token
* The combined POS tags for the current and next token
* The previous token (or an empty string if the first token)
* The token 2 tokens previous (or an empty string if the second or first token)
* The next token (or an empty string if the last token)
* The token 2 tokens after (or an empty string if the last or second last token)
* Whether the token is capitalised
* Whether the token is numeric
* Whether the token is a unit (determined from the list of units)

The ``_token_features`` function of :class:`PreProcessor` returns all these features as a dictionary.

.. literalinclude:: ../../../ingredient_parser/preprocess.py
    :pyobject: PreProcessor._token_features
    :dedent: 4

The ``sentence_features`` function of :class:`PreProcessor` return the features for all tokens in the sentence in a list.

.. attention::
    
    It is likely that some of these features aren't necessary. There is a big chunk for the future to determine the most useful features.
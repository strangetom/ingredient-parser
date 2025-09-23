.. _reference-explanation-features:

Feature Generation
==================

To be able to identify the different parts of the ingredient sentence, like the ingredient name, quantity, unit etc., the sentence is split into individual tokens.
From each token, a set of features are generated and it is these features that are used by the sequence tagging model to assign a label to each token.

Tokenization
^^^^^^^^^^^^

Tokenization is the process of splitting the ingredient sentence into individual tokens.
For the most part, a token is just an individual word from the sentence.
The one exception to this is **and/or**, which is kept as a single token.
In addition, punctuation is also split from any words to make a separate token.

The steps of the tokenizer are as follows:


#. Split the sentence at each white space character.

   Consecutive white space characters are handled so they only create a single split.

#. Split punctuation from each token, with the following exceptions: ``.``, ``$``, ``#``.

   Full stops are not split here because we do not want to split decimal numbers apart.
   ``$`` and ``#`` are used to identify fractions, so we do not want to split them apart either.

#. Recombine **and/or** into a single token.

   The previous steps will split **and/or** into separate tokens, so we recombine them here.

#. Split full stops from the end of tokens.

   If a token ends with a full stop, split this into a separate token.

#. Return the list of tokens, removing any empty strings.

.. code:: python

    >>> from Preprocess import PreProcessor
    >>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
    >>> p.tokenised_sentence
    ['#1$2', 'cup', 'orange', 'juice', ',', 'freshly', 'squeezed']


Features
^^^^^^^^

Features are properties of a token that can be deterministically calculated without the parser model.
When the model is trained, it will learn a weight for each of the features depending of how much that feature contributes to the token having a particular label or not having a label.
The features are always primitive data types: ``str``, ``bool`` (``int`` or ``float`` are converted to ``str``).

In addition to calculating features for the given token, they are also calculated for up to three surrounding tokens depending on where the token is in the sentence.
This helps provide context for the current token and improves the model accuracy.
To distinguish the features of the current token from the features of the surrounding tokens, the names features for the surrounding tokens are given a prefix based on how far from the current token they are.

Therefore, the features for any token are made up of properties of that token plus properties of the surrounding tokens.

.. attention::

    It can be quite difficult to work out whether all the features are useful to the model. The set of features and how they are used will continue to be refined as this library develops.

Lexical features
~~~~~~~~~~~~~~~~

Lexical features are determined from the properties of individual tokens in the sentence and include things like: the token, the suffix of the token, the prefix of the token, whether the token is inside parentheses etc.

The full list of lexical features are as follows:

+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| Feature         | Description                                                                                                                                          |
+=================+======================================================================================================================================================+
| bias            | This is an empty string for each token and let's the model learn the likelihood of any token having a particular label, independent of the features. |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| sentence length | The number of tokens in the sentence, rounded down to the nearest of 2, 4, 8, 12, 16, 20, 32, 64. This will be the same for all tokens in a sentence.|
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| part of speech  | The part of speech of the token.                                                                                                                     |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| stem            | The `stem <https://www.nltk.org/api/nltk.stem.porter.html#nltk.stem.porter.PorterStemmer>`_ of the token.                                            |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| token           | If the stem is different to the token, the token is also included as a feature.                                                                      |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| capitalised     | Whether the token starts with a capital letter or not.                                                                                               |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| unit            | Whether the token is found in a predefined list of units.                                                                                            |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| punc            | Whether the token is a punctuation mark.                                                                                                             |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| ambiguous       | Whether the token is a word that *could* be a unit but not in all cases, for example **clove** (clove of garlic or cloves the spice).                |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| in parentheses  | Whether the token is inside parentheses in the sentence.                                                                                             |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| after comma     | Whether the token appears after a comma in the sentence.                                                                                             |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| after plus      | Whether the token appears after the word **plus**.                                                                                                   |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| word shape      | The shape of the word encoded using X, x, d; for example the shape of Apple is Xxxxx.                                                                |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| n-grams         | Character n-grams at the start and end of the token, where n = 3, 4, 5. These are only included if the length of the token is at least n + 1.        |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+

To simplify the number features that the model has to learn, all tokens that are numbers are replace with ``!num``.


Structual features
~~~~~~~~~~~~~~~~~~

Structural features are determined from the structure of the sentence.
These are based on identifying particular phrase patterns that are common in recipe ingredient sentence.

+-------------------------+----------------------------------------------------------------------------------------------------------------------------+
| Structure               | Description                                                                                                                |
+=========================+============================================================================================================================+
| Multi-ingredient phrase | Multi-ingredient phrases are where a number of types of an ingredient are listed, such as **olive or vegetable oil**.      |
|                         |                                                                                                                            |
|                         | The generated features are booleans indicating the start and end of a multi-ingredient phrase.                             |
+-------------------------+----------------------------------------------------------------------------------------------------------------------------+
| Example phrase          | Example phrases are where specific example of an ingredient is given, e.g. **such as parsley**.                            |
|                         |                                                                                                                            |
|                         | The generated feature is a boolean indicating if the token is part of an example phrase.                                   |
+-------------------------+----------------------------------------------------------------------------------------------------------------------------+
| Compound sentence split | Some ingredient sentence are compound sentences, listing different (often alternative) ingredients with different amounts. |
|                         | For example, **1 tablespoon chopped fresh basil or 1 teaspoon dried**, where *or* separates the clauses.                   |
|                         |                                                                                                                            |
|                         | The generated feature is a boolean indicating if the token occurs after split.                                             |
+-------------------------+----------------------------------------------------------------------------------------------------------------------------+


Semantic features
~~~~~~~~~~~~~~~~~

Semantic features are determined from the meaning of the token
In practice this means making use of word embeddings, which are a method to encode a word as a numeric vector in such a way that the vectors for words with similar meanings are clustered close together.

.. note::

   Currently semantic features are not used as features for the parser model, but this is being investigated.

Example
^^^^^^^

Below is an example of the features generated for one of the tokens in an ingredient sentence.

.. code:: python

    >>> from ingredient_parser.en import PreProcessor
    >>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
    >>> p.sentence_features()[1]  # for the token: "cup"
    {
      'bias': '',
      'sentence_length': '4',
      'pos': 'NN',
      'stem': 'cup',
      'is_capitalised': False,
      'is_unit': True,
      'is_punc': False,
      'is_ambiguous': False,
      'is_in_parens': False,
      'is_after_comma': False,
      'is_after_plus': False,
      'word_shape': 'xxx',
      'mip_start': False,
      'mip_end': False,
      'after_sentence_split': False,
      'example_phrase': False,
      'prev_stem': '!num',
      'prev_pos_ngram': 'CD+NN',
      'prev_pos': 'CD',
      'prev_is_capitalised': False,
      'prev_is_unit': False,
      'prev_is_punc': False,
      'prev_is_ambiguous': False,
      'prev_is_in_parens': False,
      'prev_is_after_comma': False,
      'prev_is_after_plus': False,
      'prev_word_shape': '!xxx',
      'prev_mip_start': False,
      'prev_mip_end': False,
      'prev_after_sentence_split': False,
      'prev_example_phrase': False,
      'next_stem': 'orang',
      'next_pos_ngram': 'NN+NN',
      'next_pos': 'NN',
      'next_is_capitalised': False,
      'next_is_unit': False,
      'next_is_punc': False,
      'next_is_ambiguous': False,
      'next_is_in_parens': False,
      'next_is_after_comma': False,
      'next_is_after_plus': False,
      'next_word_shape': 'xxxxxx',
      'next_mip_start': False,
      'next_mip_end': False,
      'next_after_sentence_split': False,
      'next_example_phrase': False,
      'next2_stem': 'juic',
      'next2_pos_ngram': 'NN+NN+NN',
      'next2_pos': 'NN',
      'next2_is_capitalised': False,
      'next2_is_unit': False,
      'next2_is_punc': False,
      'next2_is_ambiguous': False,
      'next2_is_in_parens': False,
      'next2_is_after_comma': False,
      'next2_is_after_plus': False,
      'next2_word_shape': 'xxxxx',
      'next2_mip_start': False,
      'next2_mip_end': False,
      'next2_after_sentence_split': False,
      'next2_example_phrase': False,
      'next3_stem': ',',
      'next3_pos_ngram': 'NN+NN+NN+,',
      'next3_pos': ',',
      'next3_is_capitalised': False,
      'next3_is_unit': False,
      'next3_is_punc': True,
      'next3_is_ambiguous': False,
      'next3_is_in_parens': False,
      'next3_is_after_comma': False,
      'next3_is_after_plus': False,
      'next3_word_shape': ',',
      'next3_mip_start': False,
      'next3_mip_end': False,
      'next3_after_sentence_split': False,
      'next3_example_phrase': False
   }

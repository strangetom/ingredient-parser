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

Features are properties of a token that can be deterministically calculated.
When the sequence tagging model is trained, it will learn a weight for each of the features depending of how much that feature contributes to the token having a particular label.
The features are always primitive data types: ``str``, ``bool``, ``int``, ``float``.

In addition to calculating features for the given token, they are also calculated for the three surrounding tokens depending on where the token is in the sentence.
This helps provide context for the current token and improves the model accuracy.
To distinguish the features of the current token from the features of the surrounding tokens, the names features for the surrounding tokens are given a prefix based on how far from the current token they are.

Therefore, the features for any token are made up of properties of that token plus properties of the surrounding tokens.

.. attention::

    It can be quite difficult to work out whether all the features are useful to the model. The set of features and how they are used will continue to be refined as this library develops.

Syntactic features
~~~~~~~~~~~~~~~~~~

Syntactic features are determined from the syntax of the token in the sentence and include things like: the token, the suffix of the token, the prefix of the token, whether the token is inside parentheses etc.

The full list of syntactic features are as follows:

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


Semantic features
~~~~~~~~~~~~~~~~~

Semantic features are determined from the meaning of the token
In practice this means making use of word embeddings, which are a method to encode a word as a numeric vector in such a way that the vectors for words with similar meanings are clustered close together.

An embeddings model has been trained using `floret <https://github.com/explosion/floret>`_ from the same data used to train the sequence tagging model.
This model encodes words as 10-dimensional vectors (chosen to reduce the size of the model).
For each token, the corresponding 10-dimensional vector can be calculated and used as a feature.

Due to limitations of the `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_, which cannot make use of features that are lists, each dimension of the vector is turned into a separate feature.

Example
^^^^^^^

Below is an example of the features generated for one of the tokens in an ingredient sentence.

.. code:: python

    >>> from Preprocess import PreProcessor
    >>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
    >>> p.sentence_features()[1]  # for the token: "cup"
    {
      'bias': '',
      'sentence_length': 4,
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
      'v0': -0.139836490154,
      'v1': 0.335813522339,
      'v2': 0.772642672062,
      'v3': -0.165960505605,
      'v4': 0.16534408927,
      'v5': -0.356404691935,
      'v6': 0.335878640413,
      'v7': -0.614531040192,
      'v8': 0.474092006683,
      'v9': -0.137665584683,
      'prev_stem': '!num',
      'prev_pos': 'CD+NN',
      'prev_is_capitalised': False,
      'prev_is_unit': False,
      'prev_is_punc': False,
      'prev_is_ambiguous': False,
      'prev_is_in_parens': False,
      'prev_is_after_comma': False,
      'prev_is_after_plus': False,
      'prev_word_shape': '!xxx',
      'prev_v0': -0.228524670005,
      'prev_v1': 0.118124544621,
      'prev_v2': 0.474654018879,
      'prev_v3': 0.006919545121,
      'prev_v4': 0.293126374483,
      'prev_v5': -0.280303806067,
      'prev_v6': 0.479749411345,
      'prev_v7': -0.370705068111,
      'prev_v8': -0.055196929723,
      'prev_v9': -0.28187289834,
      'next_stem': 'orang',
      'next_pos': 'NN+NN',
      'next_is_capitalised': False,
      'next_is_unit': False,
      'next_is_punc': False,
      'next_is_ambiguous': False,
      'next_is_in_parens': False,
      'next_is_after_comma': False,
      'next_is_after_plus': False,
      'next_word_shape': 'xxxxxx',
      'next_v0': -0.988151550293,
      'next_v1': 1.244541049004,
      'next_v2': -0.004523974378,
      'next_v3': 0.618911862373,
      'next_v4': 0.682275772095,
      'next_v5': 0.035868640989,
      'next_v6': -0.350227534771,
      'next_v7': -1.441177010536,
      'next_v8': -1.112710833549,
      'next_v9': 0.280764371157,
      'next2_stem': 'juic',
      'next2_pos': 'NN+NN+NN',
      'next2_is_capitalised': False,
      'next2_is_unit': False,
      'next2_is_punc': False,
      'next2_is_ambiguous': False,
      'next2_is_in_parens': False,
      'next2_is_after_comma': False,
      'next2_is_after_plus': False,
      'next2_word_shape': 'xxxxx',
      'next3_stem': ',',
      'next3_pos': 'NN+NN+NN+,',
      'next3_is_capitalised': False,
      'next3_is_unit': False,
      'next3_is_punc': True,
      'next3_is_ambiguous': False,
      'next3_is_in_parens': False,
      'next3_is_after_comma': False,
      'next3_is_after_plus': False,
      'next3_word_shape': ','
    }


.. _reference-explanation-appendix-pos-tags:

Improving part of speech tags
=============================

Part of speech tags are used during feature generation.
A number of the :ref:`lexical features <lexical-features>` make use of the part of speech tags directly, and they are used in the identification :ref:`structural features <structural-features>`.

`NLTK <https://www.nltk.org/>`_ provides an English language part of speech tagger, which we make use of in this library.
However its accuracy when it comes to ingredient sentences seems to be worse then other types of text.

For example, consider the sentence: **1 pear cored, peeled and chopped**.
The parts of speech are unambiguous, however **pear** is incorrectly tagged **JJ** (adjective) instead of **NN** (noun, singular).

.. code:: python

    >>> pos_tag(tokenize("1 pear cored, peeled and chopped"))
    [('1', 'CD'), ('pear', 'JJ'), ('cored', 'VBN'), (',', ','), ('peeled', 'VBN'), ('and', 'CC'), ('chopped', 'VBD')]

NLTK's part of speech tagger has two stages that we could improve:

#. A lookup table for words with unambiguous tags (referred to as a ``tagdict``).
#. A Averaged Perceptron model, which determines the tag from features of the word, it's context and the previous tag in the sequence (quite similar to how this library works).

The simplest option is to augment the ``tagdict`` with additional words commonly found in ingredient sentences.
From the example sentence above, we could add the word **pear** because that will always be a noun in the context of ingredient sentences.

We will use Spacy's `English transformer model <https://spacy.io/models/en#en_core_web_trf>`_, which claims 98% accuracy for part of speech tagging, to provide the true tags.
Any tokens that occur at least 20 times in the training data that has the same tag at least 90% of the time are included in the new ``tagdict``.
When loading NLTK's part of speech tagger, we update the built in ``tagdict`` with this new one.
This new ``tagdict`` contains over 1000 new words compared to NLTK's built-in tagdict.

.. code:: python

    def pos_tag(tokens: list[str]) -> list[tuple[str, str]]:
        tagger = _get_tagger("eng")
        ingredient_tagdict = load_ingredient_tagdict()
        tagger.tagdict.update(ingredient_tagdict)
        return _pos_tag(tokens=tokens, tagset=None, tagger=tagger, lang="eng")

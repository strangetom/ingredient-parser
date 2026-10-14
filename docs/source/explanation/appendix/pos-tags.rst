.. _reference-explanation-appendix-pos-tags:

Improving part of speech tagging
================================

Improving accuracy
^^^^^^^^^^^^^^^^^^

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
#. A Averaged Perceptron model, which determines the tag from features of the word, it's context and the previous tags in the sequence (similar to how the :abbr:`CRF (Conditional Random Fields)` model in this library works).

The simplest option is to augment the ``tagdict`` with additional words commonly found in ingredient sentences.
From the example sentence above, we could add the word **pear** because that will always be a noun in the context of ingredient sentences.

Spacy's `English transformer model <https://spacy.io/models/en#en_core_web_trf>`_, which claims 98% accuracy for part of speech tagging, was used to generate candidates to add to the ``tagdict``.
Any tokens that occurred at least 20 times in the training data that had the same tag at least 90% of the time were included in the new ``tagdict``.
When loading NLTK's part of speech tagger, the built in ``tagdict`` is updated with this new one.
This new ``tagdict`` contains over 1000 new words compared to NLTK's built-in tagdict.

.. code:: python

    def pos_tag(tokens: list[str]) -> list[tuple[str, str]]:
        tagger = _get_pos_tagger()
        ingredient_tagdict = load_ingredient_tagdict()
        tagger.tagdict.update(ingredient_tagdict)
        return tagger.tag(tokens)

.. note::

    After initially generating the new ``tagdict``, we will manually insert additional entries for unambiguous words encountered in the wild that the tagger gets wrong, resulting in incorrect parsing of a sentence.

    This means that the ``tagdict`` distributed with this library is not entirely reproducible using the approach described here.

Improving execution performance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

NLTK's :func:`nltk.tag.pos_tag` function is written in pure Python, using only standard library features.
Since this library already depends on NumPy, NLTK's :class:`nltk.tag.perceptron.PerceptronTagger` can be reimplemented to use NumPy such that identical results are returned using the same model weights whilst improving execution performance.
Reusing the same weights also allows for some simplifications to be made in the NumPy implementation, for example, there will be no need implement any functionality related training the model.

The major change between NLTK's implementation and this NumPy implementation is the data structures used to store the weights.
Rather than a ``dict`` of ``dicts``, the NumPy implementation stores the weights a 2D array with dimensions ``(n_features, n_tags)``.
To use the 2D array, the features for token need to be mapped to the row indices.

The following code shows how the weights are loaded from JSON and converted to a 2D array of weights a ``feature_vocab`` dict that maps features to row indices.

.. code:: python

    rows, cols, vals = [], [], []
    feature_vocab = {}
    for feat_idx, (feature, tag_weights) in enumerate(weights_dict.items()):
        feature_vocab[feature] = feat_idx
        for tag, weight in tag_weights.items():
            rows.append(feat_idx)
            cols.append(tag_to_idx[tag])
            vals.append(weight)

    weights_matrix = np.zeros((len(feature_vocab), len(tags)), dtype=np.float64)
    weights_matrix[rows, cols] = vals

The ``predict()`` function follows takes the features for a token, finds the row indices for those features, sums the weights for the selected rows, then selected the column with the largest score.

.. code:: python

    def predict(features: list[str]) -> str:
        """Predict the tag for a token described by features list."""

        # Convert from feature strings to index in feature vocabulary.
        feature_indices = [
            idx for f in features if (idx := self.feature_vocab.get(f)) is not None
        ]

        # Sum weights for active features across all tags at once.
        # Shape: (n_tags,) i.e. the summed score for each tag.
        if len(feature_indices) > 0:
            scores = self.weights.take(feature_indices, axis=0).sum(axis=0)
        else:
            scores = np.zeros(self.n_tags)

        # Return the best label
        return self.tags[scores.argmax()]

Note that the features in the NumPy implementation are a list of strings.
The NLTK's implementation uses a dict that maps feature name to a weight.
The nature of the features means that these local feature weights are always 1, therefore the NumPy implementation just keeps the feature names.

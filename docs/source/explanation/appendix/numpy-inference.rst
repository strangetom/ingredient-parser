.. _reference-explanation-appendix-numpy-inference:

NumPy based CRF inference
=========================

This page describes the implementation of a NumPy-based approach to inference using the :abbr:`CRF (Conditional Random Fields)`.
This library relies on `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_ to provide the functionality to train the :abbr:`CRF (Conditional Random Fields)` model.
Until v2.7.0, `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_ was also used for provide the inference functionality to use the trained model when parsing ingredient sentences, but this has now been replaced with an alternative implementation written using NumPy.

There are a few reasons for doing this:

#. Reduce the number of runtime dependencies
#. Make the model weights more accessible by using a more generic format (JSON)
#. Enable post-training adjustment of the weights.

.. note::

   `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_ remains a development dependency as it is still required for training the model.


Weights export
^^^^^^^^^^^^^^

`python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_ uses a binary format for saving model weights.
This format can be read by `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_ but is not very convenient if not using `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_.

Conveniently, the ``pycrfsuite.Tagger`` object has an ``.info()`` method that returns the model parameters in dicts.

.. code:: python

    >>> tagger = pycrfsuite.Tagger()
    >>> tagger.open("/path/to/model.crfsuite")
    >>> parameters = tagger.info()
    >>> parameters.attributes  # dict of features and their index
    {
        'bias:': '0',
        'sentence_length:12': '1',
        ...
    }
    >>> parameters.labels  # dict of labels and their index
    {
        'QTY': '0',
        'UNIT': '1',
        ...
    }
    >>> parameters.state_features  # dict of (feature name, label) tuples and their weight
    {
        ('bias:', 'QTY'): 0.653217,
        ('bias:', 'UNIT'): -0.690819,
        ('bias:', 'PUNC'): 0.313675,
        ...
    }
    >>> parameters.transitions # dict of (previous label, current label) tuples and their weight
    {
        ('QTY', 'QTY'): 0.71467,
        ('QTY', 'UNIT'): 3.821193,
        ('QTY', 'PUNC'): -0.275862,
        ...
    }

The dicts above are trivially written to a JSON file which can be easily read and converted to NumPy arrays for inference.


NumPy implementation
^^^^^^^^^^^^^^^^^^^^

Data structures
~~~~~~~~~~~~~~~

The model weights are stored as NumPy arrays.
Assume that the number of features is ``n_features`` and the number of labels is ``n_labels``.
It is convenient to store the transition and state weights as separate NumPy arrays.

.. code:: python

    state_weights = np.zeros((self.n_features, self.n_labels))

    for (feature, label), weight in feature_weights.items():
        feature_idx = features_to_idx[feature]
        label_idx = label_to_idx[label]
        emission_weights[feature_idx, label_idx] = weight


    transition_weights = np.zeros((self.n_labels, self.n_labels))

    for (prev_label, current_label), weight in transition_weights.items():
        prev_label_idx = label_to_idx[prev_label]
        current_label_idx = label_to_idx[current_label]
        transition_weights[prev_label_idx, current_label_idx] = weight

``feature_to_idx`` and ``labels_to_idx`` are the ``attributes`` and ``labels`` dicts exported from the ``pycrfsuite.Tagger()`` object.
These map the feature name and label name to the relevant column and row indices in the NumPy arrays.

Viterbi
~~~~~~~

The Viterbi algorithm is used to determine the optimal sequence of labels for the sequence of tokens described by their features.
The algorithm works by calculating the maximum scores for each possible label for each token considering all the transitions from the possible labels for the previous token.
Once all the scores for each possible label for each token are calculated, the algorithm works backwards through the sequence to select the label that maximised the global score for the whole sequence.

First we compute the scores based on the emission weights for each element of the sequence.
These are independent of the label transitions, so we can compute them all in one go.
For each element of the sequence, we select only the indices of the relevant features.

.. code:: python

    state_scores = np.zeros((seq_len, self.n_labels), dtype=np.float64)
    for t, features in enumerate(features_seq):
        indices = self._features_to_idx_array(features)
        if len(indices) > 0:
            # Sum the weights for the selected features by column (label) and assign
            # to the correct row of the emission_scores matrix.
            state_scores[t] = self.emission_weights[indices].sum(axis=0)

Next we define a pair of NumPy arrays: one to hold the maximum score for each label for each token, and one to hold a pointers to the previous label that resulted in that maximum score.
We only need to keep track of which previous label resulted in the maximum score for the current label because any other previous label would not maximise the score for the whole sequence.

.. code:: python

    # Initialize the Viterbi lattice as NumPy arrays.
    # One array for the scores, initialized to -inf. This is the best score for each
    # label given the previous label specified by the backpointers array.
    # One array for the backpointers, which hold the index of the previous label
    # that resulted in the score in the lattice_scores array.
    lattice_scores = np.full((seq_len, self.n_labels), -np.inf)
    backpointers = np.zeros((seq_len, self.n_labels), dtype=np.int8)

Now we can start considering the label transitions.
For the first element of the sequence, there is no label transition.

.. code:: python

    lattice_scores[0] = state_scores[0]

For the remaining elements of the sequence, we calculate the score for each possible transition from previous label to current label.
However we only keep track the maximum score for each current label and the previous label that resulted in that score.

The score for each current label given a previous label is the sum of: the score of the previous label, the score for the transition from the previous label to the current label (given by the transition matrix) and the state score for the current label.

.. code:: python

    # Forward pass, starting at t=1 because we've already initialised t=0
    for t in range(1, seq_len):
        # Get the scores for each label from the previous lattice row.
        # [:, np.newaxis] rotates this into a column vector because this is the
        # previous label to the current label, so we need to broadcast across the
        # rows of the transition matrix.
        prev_el_scores = lattice_scores[t - 1][:, np.newaxis]

        # Candidates is a (n_label, n_label) shaped matrix containing the total
        # scores for transition from each previous label to the current label.
        # We broadcast the prev_el_scores across all rows in the transition
        # matrix and broadcast the emission_scores across all columns to end up
        # with the sum of relevant weights for each label -> label transition.
        candidates = prev_el_scores + self.transition_weights + state_scores[t]

        # Find the best score in each column and the index of the best score in each
        # column and save to the lattice_scores and backpointers matrices
        # respectively.
        lattice_scores[t] = np.max(candidates, axis=0)
        backpointers[t] = np.argmax(candidates, axis=0)

Once we've iterated over every sequence element and filled the ``lattice_scores`` and ``backpointer`` matrices, we can iterate backwards through them to determine the optimal sequence of labels.
The best label for the last element of the sequence is given by the label with the highest score.
The ``backpointers`` matrix tell us the previous label that resulted in that score, which gives us the label for the second to last element, and so on.

.. code:: python

        # Back tracking through the lattice to find the best scoring sequence.
        label_indices = [0] * seq_len
        # Find the best label for the last element of the lattice, since there isn't a
        # backpointer for this.
        label_indices[-1] = int(np.argmax(lattice_scores[-1]))
        # Iterate backwards through the lattice.
        # At each step, append the backpointer that yielded the best score to the label
        # sequence.
        for t in range(seq_len - 2, -1, -1):
            label_indices[t] = int(backpointers[t + 1, label_indices[t + 1]])

        predicted_labels = [self.idx_to_label[idx] for idx in label_indices]

Marginal probabilities
~~~~~~~~~~~~~~~~~~~~~~

.. hint::

    Coming later...

Performance comparison
~~~~~~~~~~~~~~~~~~~~~~

NumPy is a very efficient method of performing lots of mathematical computations in Python, so we should not expect there to be a significant performance different between using this NumPy implementation and `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_.
However because `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_ is a wrapper around the crfsuite library which is written in C, we can expect it to be slightly faster.

The following benchmarks show the difference in performance.

.. note::

    These benchmarks are measuring the time to parse a sentence, which includes the pre-processing and post-processing, not just the difference in labelling a sequence of tokens.


**python-crfsuite**

.. code::

    $ python benchmark.py -i 3 -n 5000
    Elapsed time: 113.64 s.
    75084 total iterations.
    1513.55 us/sentence.
    660.70 sentences/second.


**NumPy**

.. code::

    $ python benchmark.py -i 3 -n 5000
    Elapsed time: 121.10 s.
    75084 total iterations.
    1612.85 us/sentence.
    620.02 sentences/second.

The NumPy implementation is about 6% slower.

Post-training adjustments
^^^^^^^^^^^^^^^^^^^^^^^^^

Post-training quantization
~~~~~~~~~~~~~~~~~~~~~~~~~~

Quantization is a technique to reduce the computational and memory cost of running inference using a model by representing the weights with lower precision data types.

The quantization technique described here is post training symmetric linear quantization. The weights are scaled linearly relative to the largest absolute weight value, which is mapped to the largest value representable by the chosen lower precision data type i.e.

.. math::

    [-w_{max}, w_{max}] \rightarrow [-q_{max}, q_{max}]

The quantization is done such that an original weight of zero is mapped a quantized weight of zero.

Quantization can be performed to an arbitrary level of precision.

The function for quantizing the weights is quite straight forward:

.. code:: python

    def quantize(params: CRFModelParameters, nbits: int) -> CRFModelParameters:

        # Determine the maximum absolute weight value
        max_weight = 0
        for w in params.state_features.values():
            max_weight = max(max_weight, abs(w))
        for w in params.transitions.values():
            max_weight = max(max_weight, abs(w))

        # Calculate the scale factor for the quantization to an integer
        # with the selected number of bits
        scale = (2 ** (nbits - 1) - 1) / max_weight

        # Quantize the weights by scaling them.
        # If a weight quantizes to zero, we can discard it.
        quantized_state_features = {}
        for feature, weight in params.state_features.items():
            quantized_weight = round(weight * scale)
            if quantized_weight != 0:
                quantized_state_features[feature] = quantized_weight

        quantized_transitions = {}
        for feature, weight in params.transitions.items():
            quantized_weight = round(weight * scale)
            if quantized_weight != 0:
                quantized_transitions[feature] = quantized_weight

        params.state_features = quantized_state_features
        params.transitions = quantized_transitions
        params.quantization_scale = scale
        return params

Training the model at different levels of quantization shows the differences in model accuracy and size.

+--------------+-------------------+----------------+------------+
| Data type    | Sentence accuracy | Token accuracy | Size (MB)  |
+==============+===================+================+============+
| 32 bit float | 98.22%            | 95.42%         | 0.34       |
+--------------+-------------------+----------------+------------+
| 16 bit int   | 98.22%            | 95.42%         | 0.28       |
+--------------+-------------------+----------------+------------+
| 12 bit int   | 98.20%            | 95.38%         | 0.26       |
+--------------+-------------------+----------------+------------+
| 8 bit int    | 98.18%            | 95.33%         | 0.21       |
+--------------+-------------------+----------------+------------+

The table shows that quantizing to smaller data types reduces model accuracy and size.
The int16 case shows a reduction in model size of 17% with no loss in accuracy.

Weight pruning
~~~~~~~~~~~~~~

Weight pruning is the process of removing weights where the absolute value is below a set threshold.
The idea behind this is that smaller weights are more likely to represent over-fitting of the model to the training data and therefore by removing them, the model size is reduced and the model is made more general.
The objective of the pruning process is to find the balance between reduction in model size and the decrease in model accuracy that eventually results from too much pruning.

.. code:: python

    def prune_weights(params: CRFModelParameters, min_abs_weight: float) -> CRFModelParameters:

        params.state_features = {
            feature: weight
            for feature, weight in params.state_features.items()
            if abs(weight) >= min_abs_weight
        }
        params.transitions = {
            feature: weight
            for feature, weight in params.transitions.items()
            if abs(weight) >= min_abs_weight
        }
        return params

The table below shows the effect of pruning weights below the listed threshold.

+------------------------+-------------------+----------------+------------+
| Minimum absolute value | Sentence accuracy | Token accuracy | Size (MB)  |
+========================+===================+================+============+
| 0                      | 98.22%            | 95.42%         | 0.34       |
+------------------------+-------------------+----------------+------------+
| 0.01                   | 98.22%            | 95.42%         | 0.32       |
+------------------------+-------------------+----------------+------------+
| 0.1                    | 98.15%            | 95.24%         | 0.25       |
+------------------------+-------------------+----------------+------------+
| 0.5                    | 95.48%            | 89.27%         | 0.12       |
+------------------------+-------------------+----------------+------------+

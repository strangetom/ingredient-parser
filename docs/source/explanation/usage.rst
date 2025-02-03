Model Usage
===========

With the model trained, it can be used to label the tokens of an ingredient sentence with one of the following labels:

* QTY
* UNIT
* NAME
* SIZE
* PREP
* PURPOSE
* COMMENT
* PUNC

The general process is like so

.. code:: python

    p = PreProcessor(input_sentence)

    tagger = pycrfsuite.Tagger()
    tagger.open(model_file)

    labels_pred = tagger.tag(p.sentence_features())

The ``tagger`` returns a list of labels the same length as the list of sentence tokens. For example, consider the sentence **3/4 cup (170g) heavy cream**:

.. code:: python

    >>> p = PreProcessor("3/4 cup (170g) heavy cream")
    >>> p.tokenized_sentence
    ['0.75', 'cup', '(', '170', 'g', ')', 'heavy', 'cream']

    >>> tagger.tag(p.sentence_features())
    ['QTY', 'UNIT', 'COMMENT', 'QTY', 'UNIT', 'COMMENT', 'NAME', 'NAME']

A confidence score can be calculated for each label too

.. code:: python

    >>>[tagger.marginal(label, i) for i, label in enumerate(labels)]
    [0.99969..., 0.9991524..., 0.997019..., 0.907705..., 0.910985..., 0.962122..., 0.998440...,
 0.996780...]

The confidence score is a value between 0 and 1 which represents the model's belief that a given label is correct. The sum of the scores for all labels for a given token is equal to 1.

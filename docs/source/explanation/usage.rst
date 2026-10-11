.. _reference-explanation-usage:

Model Usage
===========

With a model trained, it can be used to label the tokens of an ingredient sentence.
The process is shown in the figure below, taking the lower **Parsing** branch of the diagram.

.. figure:: /_static/diagrams/pipelines.png
  :class: dark-light
  :alt: Training and parsing pipelines.

  Training and parsing pipelines.

The (simplified) code looks like

.. code:: python

    >>> from ingredient_parser.en import PreProcessor
    >>> import ingredient_parser.inference import NumpyCRFInference
    # Pre-process sentence
    >>> p = PreProcessor("100 g green beans")
    # Create tagger object and load model
    >>> tagger = NumpyCRFInference("./en/data/model.json.gz")
    # Predict labels using token features
    >>> labels_pred = tagger.tag_from_features(p.sentence_features())

``tagger.tag_from_features(...)`` returns a list of (label, score) tuples the same length as the list of sentence features.
For example, consider the sentence **3/4 cup (170g) heavy cream**:

.. code:: python

    >>> p = PreProcessor("3/4 cup (170g) heavy cream")
    >>> [t.text for t in p.tokenized_sentence]
    ['#3$4', 'cup', '(', '170', 'g', ')', 'heavy', 'cream']
    >>> tagger.tag(p.sentence_features())
    [('QTY', 0.9999848752237287),
     ('UNIT', 0.9997945950855104),
     ('PUNC', 0.9999996958461318),
     ('QTY', 0.9994314164369485),
     ('UNIT', 0.998971391274032),
     ('PUNC', 0.9999965724377852),
     ('B_NAME_TOK', 0.9996519613978546),
     ('I_NAME_TOK', 0.9995347960335114)]


The confidence score can be calculated for any label at any position in the sequence too.

.. code:: python

    >>> labels = ['B_NAME_TOK', 'COMMENT', 'I_NAME_TOK', 'NAME_MOD', 'NAME_SEP', 'NAME_VAR', 'PREP', 'PUNC', 'PURPOSE', 'QTY', 'SIZE', 'UNIT']
    >>> [tagger.marginal(label, 0) for label in labels]
    [5.613672029050713e-06,      # B_NAME_TOK
     3.529313863183855e-06,      # COMMENT
     3.1521162725425907e-07,     # I_NAME_TOK
     1.0810971413220757e-08,     # NAME_MOD
     2.00873697025265e-08,       # NAME_SEP
     1.6948483205700586e-07,     # NAME_VAR
     1.4864862737236024e-06,     # PREP
     6.161970166490801e-07,      # PUNC
     3.945590993646312e-07,      # PURPOSE
     0.9999848752237287,         # QTY
     4.994455642600358e-07,      # SIZE
     3.482501584144013e-06]      # UNIT


The confidence score is a value between 0 and 1 which represents the model's belief that a given label is correct.
The sum of the scores for all possible labels for a given token is equal to 1.

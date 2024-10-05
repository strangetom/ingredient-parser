Model Guide
===========

This user guide provided more in depth information about the pipelines of training the model and for parsing a sentence.

Training Pipeline
^^^^^^^^^^^^^^^^^
The training pipeline is shown below.

.. image:: /_static/training-pipline.svg
  :width: 600
  :alt: Training pipeline


Load data
~~~~~~~~~

The data is loaded from an sqlite3 database of labelled sentences.

See :doc:`Training data <data>` for more information.

Normalise
~~~~~~~~~

The input sentences are normalised to clean up particular sentence features into a standard format. The sentence is then tokenised.

See :doc:`Normalisation <normalisation>` for more information.

Extract features
~~~~~~~~~~~~~~~~

The features for each token are extracted. These features are used to train the model or, once the model has been trained, label each token.

See :doc:`Extracting features <features>` for more information.

Train
~~~~~

The Conditional Random Fields model is trained on 80% of the training data.

Evaluate
~~~~~~~~

The remaining 20% of the training data is used to evaluate the performance of the model on data the model has not encountered before.

See :doc:`Training the model <training>` for more information.


Parsing Pipeline
^^^^^^^^^^^^^^^^

The parsing pipeline is shown below.

.. image:: /_static/parsing-pipline.svg
  :width: 300
  :alt: Parsing pipeline

The `Normalise`_ and `Extract features`_ steps are the same as above.

Label
~~~~~

The features for each token in the sentence are fed into the CRF model which returns a label and the confidence for the label for each token in the sentence.

See :doc:`Using the model <usage>` for more information.

Post-process
~~~~~~~~~~~~

The token labels go through a post-processing step to build the object that is output from the `parse_ingredient` function.

See :doc:`Post-processing <postprocessing>` for more information.

.. toctree::
   :maxdepth: 1
   :hidden:

   Training data <data>
   Normalisation <normalisation>
   Features selection <features>
   Training the model <training>
   Using the model <usage>
   Post-processing the model output <postprocessing>
   Foundation foods <foundation>
   Extending to other languages <extending>

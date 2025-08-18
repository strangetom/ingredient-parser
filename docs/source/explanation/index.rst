.. _reference-explanation-index:

Model Guide
===========

The core functionality of this library is provided by a sequence tagging natural language model.
The model takes a sequence of features calculated from the input sentence and assigns a label to each element of the sequence.
Post-processing of the sequence of labels and tokens is then used to populate the :class:`ParsedIngredient <ingredient_parser.dataclasses.ParsedIngredient>` object.

The figure below shows the processing pipelines used for training the model and parsing a sentence.

.. figure:: /_static/pipelines.svg
  :alt: Training and parsing pipelines.

  Training and parsing pipelines.

The **first** step is normalising the input sentence.
The goal of normalisation is to transform certain aspects of the sentence into a standardised form to make it easier for the model to learn the correct labels, and make subsequent post-processing easier too.
The :doc:`Sentence Normalisation <normalisation>` page provides more details on this process.

The **second** step is feature generation.
This is the process of splitting the sentence into tokens.
For each token, a set of features are generated which can be based on the token itself or the surrounding tokens.
The :doc:`Feature Generation <features>` page provides more details on this process.

Training
^^^^^^^^

If we are training the model the **third** step is training.
Here we take a large number of example sentences for which we know the correct label sequence and use them to train the model.
Once a model has been trained, the **fourth** step is to evaluate it using example sentences we did not train the model on and that we also know the correct label sequence for.

The :doc:`Data <data>` page provides details on the training data.

The :doc:`Training <training>` page provides details on the model architecture, and training and evaluation steps.

Parsing
^^^^^^^
If we are parsing a sentence, the **third** step is to use the model to label the tokens in the sentence.
The :doc:`Model Usage <usage>` page provides more details on this process.

Once the sentence tokens have been labelled, the **fourth** step is to post-process the tokens and labels.
The goal of the post-processing is to interpret the sequence of tokens and sequence of labels to determine the different parts of the sentence.
In some cases, this is quite straightforward: just group token with the same label.
In other cases, we look for particular patterns of tokens and labels to determine the output.
The :doc:`Post-processing <postprocessing>` page provides more details on this process.

.. toctree::
   :maxdepth: 1
   :hidden:

   Sentence Normalisation <normalisation>
   Feature Generation <features>
   Training Data <data>
   Model Training <training>
   Model Usage <usage>
   Post-processing <postprocessing>
   Foundation foods <foundation>

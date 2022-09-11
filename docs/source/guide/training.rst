Training the model
==================

The model chosen is a condition random fields model. This was selected because the New York Times work on this used the same model quite successfully. However, rather than re-using the same tools and process the New York Times did, this model is implemented using `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_.

To train the model, the two datasets are combined and split into training and testing sets. The NYTimes data is limited to the first 30,000 entries to prevent it overwhelming the StrangerFoods data. 

A split of 75% training, 25% testing is used be default and data in the training and testing sets are randomised using ``sklearn``'s ``model_selection.train_test_split`` function.

The training and testing data is transformed to get it's features and correct labelling

.. literalinclude:: ../../../train/train.py
    :pyobject: transform_to_dataset

.. code:: python

    X_train, y_train = transform_to_dataset(ingredients_train, labels_train)
    X_test, y_test = transform_to_dataset(ingredients_test, labels_test)

Getting the labels for each input is a bit weird. The datasets are organised in a way that means we have a string the represents the input, a string for the quantity, a string for the unit, a string for the name, and a string for the comment. 

For example, the input string

    1 cup canned plum tomatoes with juice

Has the following associated labelling:

.. list-table::

    * - Quantity
      - Unit
      - Name
      - Comment
    * - 1
      - cup
      - plum tomatoes
      - canned, with juice

We have reverse engineer this data to match each token in the input to the correct label. This is not possible to get 100% correct, especially if a word appears multiple times in a sentence with different contexts and therefore different labels. Even more difficulty is added because a token sometimes does not appear in any of the labels! Cleaning up the data should eventually resolve this however.

The ``match_label`` function attempts to do this.

.. literalinclude:: ../../../train/train.py
    :pyobject: match_labels

.. literalinclude:: ../../../train/train.py
    :pyobject: invert_labels_dict

Note that two new labels are introduced in this step, that do not appear in the labelled data.

The ``OTHER`` labels is used for any tokens that cannot be matched to a label.

The ``COMMA`` label is used to label commas, specifically. This is done because commas are particular difficult for the model to learn the correct label for, since they can legitimately appear almost anywhere in a sentence. Post-processing of the model output if used to return the commas to the most likely position, but this is not necessary for training.

Training the model
^^^^^^^^^^^^^^^^^^

With the data ready, we can now train the model using `python-crfuite <https://github.com/scrapinghub/python-crfsuite>`_.

.. code:: python
    
    import pycrfsuite

    trainer = pycrfsuite.Trainer(verbose=False)
    for X, y in zip(X_train, y_train):
        trainer.append(X, y)
    trainer.train("model.crfsuite")

This trains the model and saves the model to the file specified.
This is relatively quick the train, it takes ~30 seconds on a laptop with an Intel Core 15-10300H and 16 GB of RAM. No GPU is required.

All of the above steps are implemented in the ``train/train.py`` script. The following command will execute the script and train the model on both datasets.

.. code:: bash

    python train/train.py --nyt train/data/nytimes/nyt-ingredients-snapshot-2015.csv --sf train/data/strangerfoods/sf_labelled_data.csv

Evaluating the model
^^^^^^^^^^^^^^^^^^^^

Two metrics are used to evaluate the model:

1. Word-level accuracy
    This is a measure of the percentage of tokens in the test data that the model predicted the correct label for.
2. Sentence-level accuracy
    This is a measure of the percentage of sentences in the test data where the model predicted the correct label for all tokens 

.. code:: python

    tagger = pycrfsuite.Tagger()
    tagger.open("model.crfsuite")
    y_pred = [tagger.tag(X) for X in X_test]
    stats = evaluate(X_test, y_pred, y_test)

The current performance of the model is

.. code::

    Sentence-level results:
        Total: 9277
        Correct: 7880
        -> 84.94%

    Word-level results:
        Total: 53162
        Correct: 50655
        -> 95.28%

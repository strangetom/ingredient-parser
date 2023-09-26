Training the model
==================

The model chosen is a Condition Random Fields (CRF) model. This was selected largely because the New York Times work on this used the same model quite successfully, and CRF models are commonly used in sequence labelling machine learning applications.

However, rather than re-using the same tools and process the New York Times did, this model is trained and evaluated using `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_.

To train the model, the datasets are combined and transformed so that we have the input sentence and the true labels for each token in the input sentnece.

.. literalinclude:: ../../../train/training_utils.py
    :pyobject: transform_to_dataset

.. code:: python

        transformed_sents, transformed_labels = transform_to_dataset(
            dataset_sents, dataset_labels
        )

Getting the labels for each input is a bit unusual. The datasets are stored in csv files which means we have a string the represents the input and a string for each label. 

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

We have match each token in the input sentence to the correct label. This is not possible to get 100% correct, especially if a word appears multiple times in a sentence with different contexts and therefore different labels. 

The :func:`match_label` function attempts to do this.

.. literalinclude:: ../../../train/training_utils.py
    :pyobject: match_labels

.. literalinclude:: ../../../train/training_utils.py
    :pyobject: invert_labels_dict

Note that two new labels are introduced in this step, that do not appear in the labelled data.

The ``OTHER`` labels is used for any tokens that cannot be matched to a label. Occassionally a token cannot be matched to a label, which is usually due to one of two causes:

1. The token is simply missing from the label fields in the csv file. This is easy enough to rectify.
2. The normalisation and tokensiation processes have not resulted in the tokens assumed when the dataset was labelled. There are some known cases that result in this situation that hopefully be rectified in the future.

The ``COMMA`` label is used to label commas, specifically. This is done because commas are particular difficult for the model to learn the correct label for, since they can legitimately appear almost anywhere in a sentence. Post-processing of the model output if used to return the commas to the most likely position, but this is not necessary for training.

The data is then split into training and testing sets. A split of 75% training, 25% testing is used be default and data in the training and testing sets are randomised using ``sklearn``'s :func:`model_selection.train_test_split` function.

Training the model
^^^^^^^^^^^^^^^^^^

With the data ready, we can now train the model using `python-crfuite <https://github.com/scrapinghub/python-crfsuite>`_.

.. note::

    To train the model, you will need the additional dependencies listed in ``requirements-dev.txt``. These can be installed by running the command:

    .. code::

        >>> python -m pip install -r requirements-dev.txt

.. code:: python
    
    import pycrfsuite

    trainer = pycrfsuite.Trainer(verbose=False)
    trainer.set_params(
        {
            "feature.possible_states": True,
            "feature.possible_transitions": True,
            "c1": 0.2,
            "c2": 1,
        }
    )
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)

    trainer.train(args.save_model)

This trains the model and saves the model to the file specified.

This is relatively quick the train, it takes about 2-3 minutes on a laptop with an Intel Core 15-10300H and 16 GB of RAM. No GPU is required.

All of the above steps are implemented in the ``train.py`` script. The following command will execute the script and train the model on both datasets.

.. code:: bash

    >>> python train.py train --datasets train/data/nytimes/nyt-ingredients-snapshot-2015.csv train/data/strangerfoods/sf-labelled-data.csv train/data/cookstr/cookstr-ingredients-snapshot-2017-clean.csv

Evaluating the model
^^^^^^^^^^^^^^^^^^^^

Two metrics are used to evaluate the model:

1. Word-level accuracy
    This is a measure of the percentage of tokens in the test data that the model predicted the correct label for.
2. Sentence-level accuracy
    This is a measure of the percentage of sentences in the test data where the model predicted the correct label for all tokens 

.. code:: python

    tagger = pycrfsuite.Tagger()
    tagger.open(args.save_model)
    labels_pred = [tagger.tag(X) for X in features_test]
    stats = evaluate(labels_pred, truth_test)

The current performance of the model is

.. code::

    Sentence-level results:
        Total: 12044
        Correct: 10834
        Incorrect: 1210
        -> 89.95% correct

    Word-level results:
        Total: 76299
        Correct: 73430
        Incorrect: 2869
        -> 96.24% correct

There will always be some variation in model performance each time the model is trained, because the training data is partitioned randomly each time. If the model is representing the training data well, then the variation in performance metrics should be small (i.e. << 1%).

The model training process can be executed multiple times to obtain the average performance and the uncertainty in the performance, by running the following command:

.. code:: bash

    >>> python train.py multiple --datasets train/data/nytimes/nyt-ingredients-snapshot-2015.csv train/data/strangerfoods/sf-labelled-data.csv train/data/cookstr/cookstr-ingredients-snapshot-2017-clean.csv --runs 10

where the ``--runs`` argument sets the number of training cycles to run.
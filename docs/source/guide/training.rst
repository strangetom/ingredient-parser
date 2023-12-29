Training the model
==================

The model chosen is a Condition Random Fields (CRF) model. This was selected largely because the New York Times work on this used the same model quite successfully, and CRF models are commonly used in sequence labelling machine learning applications.

However, rather than re-using the same tools and process the New York Times did, this model is trained and evaluated using `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_.

The training data is stored in an sqlite3 database. The ``training`` table contains the following fields:

* source - the source dataset for the sentence
* sentence - the original sentence
* tokens - the tokenised sentence, stored as a list
* labels - the labels for each token, stored as a list

This method of storing the training data means that we can load the data straight from the database in the format required for training the model. The utility function :func:`load_datasets` in ``train/training_utils.py`` loads the data from the specified datasets, with an option to discard any sentence that contain an OTHER label.

The data is then split into training and testing sets. A split of 75% training, 25% testing is used be default and data in the training and testing sets are randomised using ``sklearn``'s :func:`model_selection.train_test_split` function.

Training the model
^^^^^^^^^^^^^^^^^^

With the data ready, we can now train the model using `python-crfuite <https://github.com/scrapinghub/python-crfsuite>`_.

.. note::

    To train the model, you will need the additional dependencies listed in ``requirements-dev.txt``. These can be installed by running the command:

    .. code:: bash

        $ python -m pip install -r requirements-dev.txt

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

All of the above steps are implemented in the ``train.py`` script. The following command will execute the script and train the model on all datasets.

.. code:: bash

    $ python train.py train --database train/data/training.sqlite3

You can run ``python train.py --help`` to view all the available options for tweaking the training process.

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
        Total: 14982
        Correct: 13943
        Incorrect: 1039
        -> 93.07% correct

    Word-level results:
        Total: 105831
        Correct: 103106
        Incorrect: 2725
        -> 97.43% correct



There will always be some variation in model performance each time the model is trained because the training data is partitioned randomly each time. If the model is representing the training data well, then the variation in performance metrics should be small (i.e. << 1%).

The model training process can be executed multiple times to obtain the average performance and the uncertainty in the performance, by running the following command:

.. code:: bash

    $ python train.py multiple --database train/data/training.sqlite3 --runs 10

where the ``--runs`` argument sets the number of training cycles to run.
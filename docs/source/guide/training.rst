Training the model
==================

The model chosen is a Condition Random Fields (:abbr:`CRF (Conditional Random Fields)`) model. This was selected largely because the New York Times work on this used the same model quite successfully, and :abbr:`CRF (Conditional Random Fields)` models are commonly used in sequence labelling machine learning applications.

However, rather than re-using the same tools and process the New York Times did, this model is trained and evaluated using `python-crfsuite <https://github.com/scrapinghub/python-crfsuite>`_.

The training data is stored in an sqlite3 database. The ``training`` table contains the following fields:

* source - the source dataset for the sentence
* sentence - the original sentence
* tokens - the tokenised sentence, stored as a list
* labels - the labels for each token, stored as a list

This method of storing the training data means that we can load the data straight from the database in the format required for training the model. The utility function :func:`load_datasets` in ``train/training_utils.py`` loads the data from the specified datasets, with an option (default true) to discard any sentence that contain an OTHER label.

The data is then split into training and evaluation sets. A split of 80% training, 20% evaluation is used be default and data in the training and evaluation sets are randomised using :func:`sklearn.model_selection.train_test_split`.

Training
^^^^^^^^

With the data ready, we can now train the model using `python-crfuite <https://github.com/scrapinghub/python-crfsuite>`_.

.. note::

    To train the model, you will need the additional dependencies listed in ``requirements-dev.txt``. These can be installed by running the command:

    .. code::

        $ python -m pip install -r requirements-dev.txt


A outline of the code for training the model is shown below, which trains the model and saves the model to the file specified.

.. code:: python

    import pycrfsuite

    trainer = pycrfsuite.Trainer(verbose=False)
    trainer.set_params(
        {
            "feature.possible_states": True,
            "feature.possible_transitions": True,
            "c1": 0.2,
            "c2": 1,
            ...
        }
    )
    for X, y in zip(features_train, truth_train):
        trainer.append(X, y)

    trainer.train("model.crfsuite")

All of the above steps are implemented in the ``train.py`` script. The following command will execute the script and train the model on all datasets.

.. code::

    $ python train.py train --database train/data/training.sqlite3

You can run ``python train.py --help`` to view all the available options for tweaking the training process.

.. note::

    It takes about 12 minutes to train the on a laptop with an Intel Core 15-10300H and 16 GB of RAM. No GPU is required.

Evaluation
^^^^^^^^^^

Two metrics are used to evaluate the model:

1. Word-level accuracy
    This is a measure of the percentage of tokens in the evaluation data that the model predicted the correct label for.
2. Sentence-level accuracy
    This is a measure of the percentage of sentences in the evaluation data where the model predicted the correct label for all tokens.

An outline of the code for testing the model is shown below, which opens the trained model and uses it to label the tokens for each sentence in the evaluation set.

.. code:: python

    tagger = pycrfsuite.Tagger()
    tagger.open("model.crfsuite")
    labels_pred = [tagger.tag(X) for X in features_evaluate]
    stats = evaluate(labels_pred, truth_evaluate)

See the `Model Card <https://github.com/strangetom/ingredient-parser/blob/master/ingredient_parser/ModelCard.md>`_ for the current model performance.

Each time the model is trained, the training data is partitioned randomly between the training and evaluation sets. This means there will be some variation in model performance each time the model is trained. However, ff the model is representing the training data well, then the variation in performance metrics should be small (i.e. << 1%).

The model training process can be executed multiple times to obtain the average performance and the uncertainty in the performance, by running the following command:

.. code::

    $ python train.py multiple --database train/data/training.sqlite3 --runs 10

where the ``--runs`` argument sets the number of training cycles to run.

Tuning
^^^^^^

pycrfsuite offers a few different algorithms for training the model, each of which has a number of hyper-parameters that can be used to tune its performance. The selection of the best algorithm and optimal hyper-parameters involves iterating over the algorithms and their hyper-parameters and evaluating the trade-offs between model size, model accuracy and training time.

To run a grid search over a number of different algorithms and hyper-parameters for each one, the ``gridsearch`` sub-command of ``train.py`` can be used.

.. code::

    # Show all the options
    $ python train.py gridsearch --help

    # Train models using the LBFGS and AP algorithms, using default hyper-parameters
    $ python train.py gridseach --database train/data/training.sqlite3 --algos lbfgs ap

    # Train models using the LBFGS algorithm, using all combinations of the specified
    # hyper-parameters and the default values for any not specified
    $ python train.py gridseach --database train/data/training.sqlite3 --algos lbfgs --lbfgs-params '{"c1": [0.05, 0.1, 0.5, 1], "c2":[0.1, 0.5, 1, 2]}'

    # Train models using the LBFGS and AP algorithms, only varying the global hyper-parameters
    # which apply to all models
    $ python train.py gridseach --database train/data/training.sqlite3 --algos lbfgs  ap --global-params '{"feature.minfreq":[0, 1, 5],"feature.possible_transitions":[true, false],"feature.possible_states":[true, false]}'

When a grid search is performed, the same train/evaluation split of the data is used for every model, so the performances can be directly compared. Each model trained is given a random unique name. By default, the models are deleted after their performance has been evaluated. To keep the models, the ``--keep-models`` option can be used.

For example, to train models using each of the possible algorithms with their default hyper-parameters:

.. code::

    $ python train.py gridsearch --database train/data/training.sqlite3 --algos lbfgs l2sgd ap pa arow
    [INFO] Loading and transforming training data.
    [INFO] 59,928 usable vectors
    [INFO] 72 discarded due to OTHER labels
    [INFO] Grid search over 5 hyperparameters combinations.
    [INFO] 727897090 is the random seed used for the train/test split.
    100%|█████████████████████████████████████████████████████████| 5/5 [02:51<00:00, 34.32s/it]
    ┌─────────────┬──────────────┬──────────────────┬─────────────────────┬─────────┬─────────────┐
    │ Algorithm   │ Parameters   │ Token accuracy   │ Sentence accuracy   │ Time    │   Size (MB) │
    ├─────────────┼──────────────┼──────────────────┼─────────────────────┼─────────┼─────────────┤
    │ lbfgs       │ {...}        │ 97.32%           │ 93.07%              │ 0:02:48 │        3.31 │
    │ l2sgd       │ {...}        │ 97.30%           │ 93.04%              │ 0:00:57 │        3.31 │
    │ ap          │ {...}        │ 97.06%           │ 92.18%              │ 0:00:34 │        2.25 │
    │ pa          │ {...}        │ 97.05%           │ 92.11%              │ 0:00:48 │        2.21 │
    │ arow        │ {...}        │ 95.46%           │ 87.61%              │ 0:00:44 │        1.82 │
    └─────────────┴──────────────┴──────────────────┴─────────────────────┴─────────┴─────────────┘

See the `CRFSuite documentation <https://www.chokkan.org/software/crfsuite/manual.html>`_ for details on the hyper-parameters for each algorithm.

Model reproducibility
^^^^^^^^^^^^^^^^^^^^^

The model file output from the training process can be reliably reproduced as long as the training database is the same, and the same split between the training and evaluation data is used.

By default when training a model, a random integer is used as the seed for :func:`sklearn.model_selection.train_test_split`. This is printed to the command line. A seed value can be set using the ``--seed`` argument, which will result in the same split between training and evaluation data every time the same seed value is used. With this, the model can be reproduced.

.. code::

    $ python train.py train --database train/data/training.sqlite3 --seed 354876538
    [INFO] Loading and transforming training data.
    [INFO] 59,928 usable vectors.
    [INFO] 72 discarded due to OTHER labels.
    [INFO] 354876538 is the random seed used for the train/test split.
    ...

Historical performance
^^^^^^^^^^^^^^^^^^^^^^

The model performance has improved over time as a result of improvements to the labeling consistency of the training data, the sentence normalization steps and the feature selection. The figure below shows the sentence- and word-level performance for the last few releases.

.. image:: /_static/performance-history.svg
  :class: .dark-light
  :alt: Bar graph showing the model performance improving which each new release

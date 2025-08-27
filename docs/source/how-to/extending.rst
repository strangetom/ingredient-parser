.. _reference-how-to-extending:

Extend to other languages
=========================

.. note::

    At the moment, there aren't any plans to support languages other than English.

The ``ingredient_parser`` package has been designed so that it can be extended to multiple languages.
This page describes how to train a model for another language and how to integrate it into the ``ingredient_parser`` package.

The ideas in this page is largely theoretical and may need to be adjusted if additional languages are ever supported.

Package structure
^^^^^^^^^^^^^^^^^

The package structure is shown below

.. code:: bash

    ingredient_parser/
    ├── _common.py
    ├── dataclasses.py
    ├── __init__.py
    ├── parsers.py
    ├── en/
    │   ├── _constants.py
    │   ├── __init__.py
    │   ├── ModelCard.en.md
    │   ├── model.en.crfsuite
    │   ├── parser.py
    │   ├── postprocess.py
    │   ├── preprocess.py
    │   ├── _regex.py
    │   └── _utils.py


The ``en`` sub-package contains all the files specifically related to the English-language parser.
The ``en`` sub-package exposes 4 functions and classes via the ``__init__.py`` file:

#. :func:`parse_ingredient_en`, the English specific implementation of :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>`.
#. :func:`inspect_parser_en`, the English language specific implementation of :func:`inspect_parser <ingredient_parser.parsers.inspect_parser>`.
#. :class:`PreProcessor <ingredient_parser.en.preprocess.PreProcessor>`, the pre-processor for English sentences.
#. :class:`PostProcessor <ingredient_parser.en.postprocess.PostProcessor>`, the post-processor for English sentences.

The first two functions are called by :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` and :func:`inspect_parser <ingredient_parser.parsers.inspect_parser>` respectively when English is the specified language.
The :class:`PreProcessor <ingredient_parser.en.preprocess.PreProcessor>` and :class:`PostProcessor <ingredient_parser.en.postprocess.PostProcessor>` classes are exposed for model training and convenience.

Equivalents of these functions and classes should be implemented for any new languages and exposed in the same way.

Example: Spanish
~~~~~~~~~~~~~~~~

To extend the package to include support for parsing Spanish sentences, we will need to add an ``es`` sub-package:

.. code:: bash

    ingredient_parser/
    ├── es/
    │   ├── __init__.py
    │   ├── ModelCard.es.md
    │   ├── model.es.crfsuite
    │   ├── parser.py
    │   ├── postprocess.py
    │   ├── preprocess.py

We will then need to implement Spanish versions for :func:`parse_ingredient_es` and :func:`inspect_parser_es`, as well as the Spanish equivalents of :class:`PreProcessor <ingredient_parser.en.preprocess.PreProcessor>` and :class:`PostProcessor <ingredient_parser.en.postprocess.PostProcessor>`.

.. tip::

    Use the code in the ``en`` sub-package as an example and modify as needed.

    It is quite likely that much of the pre- and post-processing is similar between languages that use the Latin alphabet, so modifying the English implementation should be a good starting point.

    The :ref:`training <training-a-new-model>` section below gives some further suggestions on specific changes that might be needed.


The top level :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` and :func:`inspect_parser <ingredient_parser.parsers.inspect_parser>` functions in ``ingredient_parser/parsers.py`` will need updating along the lines of

.. code:: python

    from ingredient_parser.es import inspect_parser_es, parse_ingredient_es

    def parse_ingredient(...):

        match lang:
            case "en":
                return parse_ingredient_en(...)
            case "es":
                return parse_ingredient_es(...)


.. attention::

    The language specific implementations of the functions and classes exposed in the language specific sub-package must have the same arguments as the English implementations.

.. _training-a-new-model:

Training a new model
^^^^^^^^^^^^^^^^^^^^

To support other languages, we will need a :abbr:`CRF (Conditional Random Fields)` model for that language.
There will be a separate model for each language.

The training pipeline (shown below) is agnostic of the target language, so we will take each step in turn and list the likely modifications that would be needed.

.. image:: /_static/pipelines.svg
  :alt: Training and parsing pipelines.

0. Prepare data
~~~~~~~~~~~~~~~

.. warning::

    This is a very time consuming process.

This is where the majority of the effort is required.
A dataset of ingredient sentences in the target language needs to be created and labelled.
This is a time consuming and manual process.

The minimum number of training sentences needed for a proof of concept demonstration is probably 1000-2000.
The more different sentences available for training, the more robust the model will be.

To make best use of the existing infrastructure for training models, the sentences should be stored in an sqlite3 database using the same schema as the English training data (see :ref:`Data Storage <data-storage>`).
A separate database is recommended over a separate table in the current database to make it easier to make changes to one langugage's training independently.

For each ingredient sentence in the training data, you will need to create a list of tokens and a list of labels.
Depending on the language, you may need a language specific :func:`tokenize <ingredient_parser.en._utils.tokenize>` function.

.. tip::

    A web app has been developed to aid in the adding and labelling of training sentences. If intending to add another language, you will need to adjust some of the web app code. Regardless, you can run these commands under the webtools directory to install the packages and run the web app.

    .. code:: bash

        $ npm install
        $ npm run dev

    Then navigate to http://localhost:5000 in your browser.

1. Normalise
~~~~~~~~~~~~

The goal of the normalisation step is to try to convert common variations in how sentences are written into standardised forms, so the model learns on more consistent data.

The majority of the normalisation steps fall into one of two categories:

1. Singularising units
2. Normalising numbers

The singularising of units is done using a predefined dict of singular and plural forms of units, which will need to be updated for the target language.
The English list is in ``ingredient_parser/en/_constants.py``.

The normalising of numbers may be common across many languages.
One key difference will be whether the target language uses decimal commas or decimal points.
English uses decimal points, so the functions in :func:`PreProcessor.normalise <ingredient_parser.en.PreProcessor.normalise>` may need modifying (including the regular expressions they rely on) to correctly work with decimal commas.

2. Generate features
~~~~~~~~~~~~~~~~~~~~

There are a couple of things to consider here:

* Changing the Stemmer to one specific to the target language.
* Changing the Part of Speech tagger to one specific to the target language.
* Updates to the other feature generation function relevant to the target language.
  Features may be specific to the target language.
* If using semantic feature from embeddings, an embeddings model will need to be created.

The current feature set using for English should be a good starting point for other languages using the Latin alphabet.

3. and 4. Train and Evaluate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With all the previous updates made, the only further change needed will be to update the :func:`select_preprocessor` function in ``train/training_utils.py`` to load the correct :class:`PreProcessor` class.

The command to train a model has an option to set the database and the database table. For example, to select the database table named "es":

.. code:: bash

    $ python train.py train --database train/data/training.es.sqlite3 --database-table es

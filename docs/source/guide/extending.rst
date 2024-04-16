Extending to other languages
============================

.. note::

    At the moment, there aren't any plans to support languages other than English.

This page gives some thoughts on how to modify the library to support different languages. Everything on this page is just an opinion, based on the process to develop this package for the English language, and has not been implemented.

For simplicity, only languages that use the Latin alphabet are considered.

There are two parts:

1. How to retool this package for a different language
2. How to modify the package to support multiple languages

How to support other languages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Training
++++++++

The training pipeline (shown below) is agnostic of the target language, so I will take each step in turn and list the likely modifications that would be needed.

.. image:: /_static/training-pipline.svg
  :width: 600
  :alt: Training pipeline

1. Load data
~~~~~~~~~~~~

.. warning::

    This is a very time consuming process.

This is where the majority of the effort is required. A dataset of ingredient sentences in the target language needs to be created and labelled. This is a time consuming and manual process.

The minimum number of training sentences needed for a proof of concept demonstration is probably 1000-2000. The more sentences available for training, the more robust the model will be.

To make best use of the existing infrastructure for training models, the sentences should be stored in an sqlite3 database using the same schema as the English training data (see :ref:`Data Storage <data-storage>`).

For each ingredient sentence in the training data, you will need to create a list of tokens and a list of labels. Depending on the language, you may need to modify how the :func:`tokenize <ingredient_parser.en._utils.tokenize>` function works.

.. tip::

    A webapp has been developed to aid in the adding and labelling of training sentences. Run the command

    .. code:: bash

        $ flask --app labeller run

    Then navigate to http://localhost:5000 in your browser.

    You may need to tweak this to work with the correct database.

2. Normalise
~~~~~~~~~~~~

The goal of the normalisation step is to try to convert common variations in how sentences are written into standardised forms, so the model learns on more consistent data.

The majority of the normalisation steps fall into one of two categories:

1. Singularising units
2. Normalising numbers

The singularising of units is done using a predefined dict of singualr and plural forms of units, which will need to be updated for the target language. This list is in ``ingredient_parser._constants.py``.

The normalising of numbers may be common across many languages. One key difference will be whether the target language uses decimal commas or decimal points. English uses decimal points, so the functions in :func:`PreProcessor.normalise <ingredient_parser.en.PreProcessor.normalise>` may need modifying (including the regular expressions they rely on) to correctly work with decimal commas.

3. Extract features
~~~~~~~~~~~~~~~~~~~

There are a couple of things to consider here:

* Changing the Stemmer to one specific to the target language
* Does the Part of Speech tagger to one specific to the target language
* Updates to the other feature generation function relevant to the target language

4 and 5. Train and Evaluate
~~~~~~~~~~~~~~~~~~~~~~~~~~~

With all the previous updates made, the training and evaluation steps shouldn't need any modification, other than to make sure they use to right data and :class:`PreProcessor <ingredient_parser.en.preprocess.PreProcessor>` implementation.

The command to train a model has an option to set the database table. For example, to select the database table named "en":

.. code:: bash

    $ python train.py train --database train/data/training.sqlite3 --database-table en


Parsing
+++++++

The parsing pipeline (shown below) is similarly agnostic of the language used, and luckily it benefits from many of the changes needed for the training pipeline.

.. image:: /_static/parsing-pipline.svg
  :width: 300
  :alt: Parsing pipeline

1. Normalise
~~~~~~~~~~~~

This uses the same :class:`PreProcessor <ingredient_parser.en.preprocess.PreProcessor>` as the training pipeline, so no further modifications will be needed.

2. Extract features
~~~~~~~~~~~~~~~~~~~

This uses the same :class:`PreProcessor <ingredient_parser.en.preprocess.PreProcessor>` as the training pipeline, so no further modifications will be needed.

3. Label
~~~~~~~~

This also does not require any updates because the labelling of tokens is independent of the language used, as long as the tokensiation and feature extraction have been appropriately updated.

4. Postprocess
~~~~~~~~~~~~~~

The goal of the postprocessing step is to combine the labelled tokens into a useful :class:`ParsedIngredient <ingredient_parser.en.postprocess.ParsedIngredient>` object.

For the most part, this is just a case of combining adjacent tokens with the same label into strings and should be language agnostic.

The case to consider in more details is amounts. There are some special cases handled by the :func:`PostProcessor._postprocess_amounts <ingredient_parser.postprocess.PostProcess._postprocess_amounts>` function that are probably specific to English and would need modifying or removing.

A good starting point would be to remove those special cases and rely on the fallback pattern processing to start with. For example:

.. code:: python

    def _postprocess_amounts(self) -> list[IngredientAmount]:
        """ ...
        """
        funcs = [
            #self._sizable_unit_pattern,  # Comment out or remove this
            #self._composite_amounts_pattern,  # Comment out or remove this
            self._fallback_pattern,
        ]

        amounts = []
        for func in funcs:
            idx = self._unconsumed(list(range(len(self.tokens))))
            tokens = self._unconsumed(self.tokens)
            labels = self._unconsumed(self.labels)
            scores = self._unconsumed(self.scores)

            parsed_amounts = func(idx, tokens, labels, scores)
            amounts.extend(parsed_amounts)

        return sorted(amounts, key=lambda x: x._starting_index)

How to support multiple languages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This section is dump of ideas that could eventually allow multiple languages to be supported by this package.

**Assumptions**:

.. list-table::

    * - Separate models
      - There will a separate model for each supported language.
    * - No language detection
      - Automatic detection of the language of a sentence to be parsed is out of scope of this package. It is assumed the language is known prior to attempting to parse the sentence.

Changes to training
+++++++++++++++++++

* The database of training data can trivially be updated to include a table of training data for each language. There may be benefit to separate databases, purely from the perspective of managing the database with git.

* The ``train.py`` commands can be updated to have a ``--language`` option which will set the language model being trained. This will select the correct training data and ensure the correct tokeniser and PreProcessor implementations are used.

* The output model file should be named with the language e.g. **model.en.crfsuite** for English.

* There will need to be a separate and specific model card for model.

Changes to parsing
++++++++++++++++++

* The :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function can be updated to add a ``language`` keyword argument. There are then a couple of options:

  * Use the ``language`` argument to select the correct model, ``PreProcessor`` and ``PostProcessor``. The :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function would look similar to how it is now except there would be an extra bit of code to select the correct classes.

  * Change the :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function so it just passes the sentence and keyword arguments to the correct language specific version of the function e.g.

    .. code:: python

        def parse_ingredient(sentence, language="en", ...):

            if language == "en":
                return parse_ingredient_en(sentence, **kwargs)
            elif language == "es":
                return parse_ingredient_es(sentence, **kwargs)
            # etc ...

    This second approach might have advantages in terms of only importing the required functionality, and not everything.

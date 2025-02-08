Training Data
=============

To train the sequence tagging model that provides the core functionality of this library, we need a set of example sentences for which we have the correct labels.
The training data needs to be adequately representative of the types of sentences we expect to encounter when using the library.
Given the wide variation in how ingredient sentences are phrase and structured, this means a lot training data.

Training data has been sourced from the following places:

+------------+-----------+-----------------------------------------------------------------------------------+
| Dataset    | Sentences | Source                                                                            |
+============+===========+===================================================================================+
| allrecipes | 15,000    | https://archive.org/details/recipes-en-201706                                     |
+------------+-----------+-----------------------------------------------------------------------------------+
| bbc        | 15,000    | https://archive.org/details/recipes-en-201706                                     |
+------------+-----------+-----------------------------------------------------------------------------------+
| cookstr    | 15,000    | https://archive.org/details/recipes-en-201706                                     |
+------------+-----------+-----------------------------------------------------------------------------------+
| nyt        | 30,000    | https://github.com/NYTimes/ingredient-phrase-tagger                               |
+------------+-----------+-----------------------------------------------------------------------------------+
| tc         | 6,318     | https://github.com/strangetom/ingredient-parser/issues/21#issuecomment-2361461401 |
+------------+-----------+-----------------------------------------------------------------------------------+

.. note::

    With the exception of the TC dataset, each dataset contains more than the listed number of sentences. The number refers to the number of sentences that have been labelled for training the model.

The sentences in the different datasets have different characteristics, which should help the model generalise to be able to handle the majority of ingredient sentences.
Some of the different characteristics that are worth highlighting are

* Units system, e.g. metric (bbc) or imperial/US customary
* Sentence complexity, e.g. sentences from cookstr tend to be long and include multiple ingredients and quantities
* Use of brand names (allrecipes) or generic names

Labelling the data
^^^^^^^^^^^^^^^^^^

Preparing the training sentences is a very manual task that involves labelling each token in each sentence with the correct label.
One of the biggest challenges is doing this consistently due to the size of the training data and the variation in the sentences.

The model uses the following labels:

+------------+-----------------------------------------------------------------------------------------------+
| Label      | Description                                                                                   |
+============+===============================================================================================+
| QTY        | Quantity of the ingredient.                                                                   |
+------------+-----------------------------------------------------------------------------------------------+
| UNIT       | Unit of the quantity for the ingredient.                                                      |
+------------+-----------------------------------------------------------------------------------------------+
| SIZE       | Physical size of the ingredient (e.g. large, small).                                          |
|            |                                                                                               |
|            | This is not used to label the size of the unit.                                               |
+------------+-----------------------------------------------------------------------------------------------+
| PREP       | Preparation instructions for the ingredient (e.g. finely chopped).                            |
+------------+-----------------------------------------------------------------------------------------------+
| PURPOSE    | Purpose of the ingredient (e.g. for garnish)                                                  |
+------------+-----------------------------------------------------------------------------------------------+
| PUNC       | Any punctuation tokens.                                                                       |
+------------+-----------------------------------------------------------------------------------------------+
| B_NAME_TOK | The first token of an ingredient name.                                                        |
+------------+-----------------------------------------------------------------------------------------------+
| I_NAME_TOK | A token within an ingredient name that is not the first token.                                |
+------------+-----------------------------------------------------------------------------------------------+
| NAME_VAR   | A token that indicates a variation of the ingredient name.                                    |
|            |                                                                                               |
|            | This is used in cases such as **beef or chicken stock**. **beef** and **chicken** are labelled|
|            | with NAME_VAR as they indicate variations of the ingredient name **stock**.                   |
+------------+-----------------------------------------------------------------------------------------------+
| NAME_MOD   | A token that modifies multiple ingredient names in the sentence.                              |
|            |                                                                                               |
|            | For example in **dried apples and pears**, **dried** is labelled as NAME_MOD because it       |
|            | modifies the two ingredient names, **apples** and **pears**.                                  |
+------------+-----------------------------------------------------------------------------------------------+
| NAME_SEP   | A token that separates different ingredient names and isn't PUNC, typically **or**.           |
+------------+-----------------------------------------------------------------------------------------------+
| COMMENT    | Additional information in the sentence that does not fall in one of the other labels.         |
+------------+-----------------------------------------------------------------------------------------------+

The descriptions in the table above for most of the labels should be sufficient to understand, however the different labels used to label tokens in ingredient names requires further explanation.





.. _data-storage:

Data storage
^^^^^^^^^^^^

The labelled training data is stored in an sqlite3 database at ``train/data/training.sqlite3``. The database contains a single table, ``en``, with the following fields:

+------------------+------------------------------------------------------+
| Field            | Description                                          |
+==================+======================================================+
| id               | Unique ID for the sentence.                          |
+------------------+------------------------------------------------------+
| source           | The source dataset the sentence is from.             |
+------------------+------------------------------------------------------+
| sentence         | The ingredient sentence, not normalised.             |
+------------------+------------------------------------------------------+
| tokens           | List of tokens for the sentence.                     |
+------------------+------------------------------------------------------+
| labels           | List of token labels.                                |
+------------------+------------------------------------------------------+
| foundation_foods | List of indices of tokens that are foundation foods. |
+------------------+------------------------------------------------------+


:abbr:`CSV (Comma Separated Values)` files of the full datasets are in the ``train/data/<dataset>`` directories. These :abbr:`CSV (Comma Separated Values)` files contain the full set of ingredient sentences, including those not properly labelled. The :abbr:`CSV (Comma Separated Values)` files are kept aligned with the database using the following command.

.. code::

    $ python train/data/db_to_csv.py

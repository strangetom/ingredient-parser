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

    With the exception of the TC dataset, each complete dataset contains more than the listed number of sentences. The number refers to the number of sentences that have been labelled for training the model.

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
| UNIT       | Unit of a quantity for the ingredient.                                                        |
+------------+-----------------------------------------------------------------------------------------------+
| SIZE       | Physical size of the ingredient (e.g. large, small).                                          |
|            |                                                                                               |
|            | This is not used to label the size of the unit, these are given the UNIT label.               |
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
| NAME_VAR   | A token that creates a variant of the ingredient name.                                        |
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
| OTHER      | This label is used in sentences where the sentence normalisation and tokenization steps result|
|            | in the incorrect tokens.                                                                      |
|            |                                                                                               |
|            | This is rare in the training data (currently only 45 sentences) and sentences including this  |
|            | label are excluded when training and evaluating the model.                                    |
|            |                                                                                               |
|            | The sentences are kept because the pre-processing steps should eventually handle them         |
|            | correctly.                                                                                    |
+------------+-----------------------------------------------------------------------------------------------+

The descriptions in the table above for most of the labels should be sufficient to understand, however the different labels used to label tokens in ingredient names requires further explanation.

The library has the goal of being able to identify separate ingredient names where they are given.
This is not straight forward as different ingredients are not always easily separable by a single word.

.. admonition:: Examples

    Here are some examples of ingredient sentences containing multiple ingredient names.

    #. 1 tsp butter or olive oil

       Names: **butter**, **olive oil**

       *This is the simplest case, where the word "or" separates the two names.*

    #. 500 ml olive, sunflower or vegetable oil

       Names: **olive oil**, **sunflower oil**, **vegetable oil**

       *This is a very common case, but separating using "or" and the comma will give names that do not make sense.*

    #. 2 cups hot beef or chicken stock

       Names: **hot beef stock**, **hot chicken stock**

       *One of the more complex cases, where the base name is "stock"; "beef" and "chicken" create variations of stock; and "hot" modifies those variations.*

To be able to reconstruct ingredient names that make sense from the tokens in the ingredient sentence we to label the different parts that make up the name.

B_NAME_TOK and I_NAME_TOK are used to the label the base names.
B_NAME_TOK is used for the first token of the name, I_NAME_TOK for all other token in a name.
The reason for labelling the first token differently is so that we can identify where a name starts if there aren't any other token separating it from the previous name.

NAME_VAR is used to label tokens that create variants of the following base names.
In the second example above, "olive", "sunflower" and "vegetable" are all labelled with NAME_VAR because the create variants of the base name "oil".

NAME_MOD is used to label tokens that modify all following base names.
In the third example above, "hot" is labelled with NAME_MOD because it applies to "beef stock" and "chicken stock".
(Note that in this example, "beef" and "chicken" will have the NAME_VAR label, and "stock" the B_NAME_TOK label.)


.. _data-storage:

Data storage
^^^^^^^^^^^^

The labelled training data is stored in an sqlite3 database at ``train/data/training.sqlite3``.
The database contains a single table, ``en``, with the following fields:

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

The consistency of the database can be checked using the following command.

.. code:: bash

    $ python train/data/validate_db.py

This will check the following:

* That the tokens stored in the database match the tokens obtained from calling ``PreProcessor`` on the ingredient sentence.
* That the number of tokens and labels stored in the database are the same for each ingredient sentence.
* That duplicate sentences have the same labels.
* That all I_NAME_TOK labels are preceded by B_NAME_TOK or I_NAME_TOK.

CSV Exports
~~~~~~~~~~~

:abbr:`CSV (Comma Separated Values)` files of the full datasets are in the ``train/data/<dataset>`` directories.
These :abbr:`CSV (Comma Separated Values)` files contain the full set of ingredient sentences for each dataset.

The format of these :abbr:`CSV (Comma Separated Values)` files is aligned with the original format originally used by https://github.com/NYTimes/ingredient-phrase-tagger.
This means that, for sentences that are in the database and labelled, the :abbr:`CSV (Comma Separated Values)` includes a representation of the labels, but it should be noted that the database cannot be automatically recreated from the :abbr:`CSV (Comma Separated Values)` files.

The :abbr:`CSV (Comma Separated Values)` are kept synchronised (for the sentences that are also in the database) using the following command.

.. code::

    $ python train/data/db_to_csv.py

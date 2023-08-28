Loading the data
================

Data sources
^^^^^^^^^^^^

There are three sources of data which are used to train the model, each with their own advantages and disadvantages.

StrangerFoods
~~~~~~~~~~~~~

The recipes from my website: https://strangerfoods.org. 

* The dataset is extremely clean and well labelled. (Having very clean data is not necessarily useful since it won't reflect the kinds of sentences that we might come across in the wild.)
* The dataset primarily uses metric units
* The dataset is small, roughly 7100 entries

New York Times
~~~~~~~~~~~~~~

The New York Times released a dataset of labelled ingredients in their `Ingredient Phrase Tagger <https://github.com/NYTimes/ingredient-phrase-tagger>`_ repository, which had the same goal as this.

* The dataset is has each sentence labelled, but the labelling is inconsistent.
* The dataset primarily uses imperial/US customary units
* The dataset is large, roughly 178,000 entries

Cookstr
~~~~~~~

The Cookstr dataset is derived from 7918 recipes scraped from `<cookstr.com>`_ (no longer available) between 2017-06 and 2017-07. The scraped data can be found at https://archive.org/details/recipes-en-201706.

* The dataset is unlabelled and will need labelling manually.
* The dataset primarily uses imperial/US customary units, although many ingredients give the quantity in multiple units
* The dataset is medium sized, roughly 40,000 entries

The three datasets have different advantages and disadvantages, therefore combining the two should yield an improvement over using any on their own.

Labelling the data
^^^^^^^^^^^^^^^^^^

.. note::
    
    The details described in this section also apply to how the labelling was performed for the Cookstr dataset.

    It does not apply to the Stranger Foods dataset which is automatically generated.

The New York Times dataset has gone through, and continues to go through, the very manual process of labelling the training data. This process is there to ensure that the labels assigned to each token in each ingredient sentence are correct and consistent across the dataset. In general, the idea is to avoid modifying the input sentence and only correct the labels for each, although entries have been removed where there is too much missing information or the entry is not actually an ingredient sentence (a few recipe instructions have been found mixed into the data).

The model is currently trained using the first 30,000 entries of the New York Times dataset, so the labelling efforts have primarily been focussed on that subset.

.. tip::

    The impact of the consistent labelling can be seen by training the model using the full New York Times dataset, where the majority of the data has not been consistently labelled. The model performance drops significantly: ~5% reduction to both word and sentence metrics.

The following operations were done to clean up the labelling (note that this is not exhaustive, the git history for the dataset will give the full details).

* Convert all numbers in the labels to decimal
    This includes numbers represented by fractions in the input e.g. 1 1/2 becomes 1.5
* Convert all ranges to a standard format of X-Y
    This includes ranges represented textually, e.g. 1 to 2, 3 or 4 become 1-2, 3-4 respectively
* Entries where the quantities and units were originally consolidated should be unconsolidated
    There were many examples where the input would say 

        1/2 cup, plus 1 tablespoon ...

    with the quantity set as "9" and the unit "tablespoon".
    The model will not do maths for us, nor will it understand have to convert between units. In this example, the correct labelling is a quantity of "0.5", a unit of "cup", and a comment of "plus 1 tablespoon".
* Adjectives that are a fundamental part of the ingredient identity should be part of the name
    This was mostly an inconsistency across the data, for example if the entry contained "red onion", sometimes this was labelled with a name of "red onion" and sometimes with a name of "onion" and a comment of "red".

    Three general rules were applied:  

    1. **If the adjective changes the ingredient in a way that the chef cannot, it should be part of the name.**   
    2. **If the adjective changes the item you would purchase in a shop, it should be part of the name.**
    3. **If the adjectve changes the item in a way that the chef would not expect to do as part of the recipe, it should be part of the name.**
    
    It is recognised that this can be subjective. Universal correctness is not the main goal of this, only consistency.

    Examples of this:

    * red/white/yellow/green/Spanish onion
    * granulated/brown/confectioners' sugar
    * soy/coconut/skim/whole milk
    * ground spices
    * extra-virgin olive oil
    * fresh x/y/z
    * ice water
    * cooked chicken

* All units should be made singular
    This is to reduce the amount the model needs to learn. "teaspoon" and "teaspoons" are fundamentally the same unit, but because they are different words, the model could learn different associations.

* Where alternative ingredients are given in the sentence, these should be part of the name if the alternative is in the same quantity, or the comment if it is a different quantity.
    For example:

    * ``3 tablespoons butter or olive oil, or a mixture`` should have the name as ``butter or olive oil``

    however

    * ``4 shoots spring shallots or 4 shallots, minced`` should have the name as ``spring shallots`` and the comment as ``or 4 shallots, minced`` because there are different quantities of spring shallots to shallots.

.. warning::

    The labelling processing is very manual and as such has not been completed on all of the available data. The labelling has been completed for the following subsets of the datasets:

    * The first 30,000 sentences of the New York Times dataset
    * The first 10,000 sentences of the Cookstr dataset

    If the model is trained on more of the available data, then the performance will likely worsen.
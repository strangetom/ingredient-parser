User Guide
==========

Data Sources
^^^^^^^^^^^^

There are two sources of data which will be used to train the model, each with their own advantages and disadvantages.

StrangerFoods
~~~~~~~~~~~~~

The recipes from my website: https://strangerfoods.org. 

* The dataset is extremely clean and well labelled. This isn't a particularly useful feature.
* The dataset primarily uses metric units
* The dataset is small, roughly 7100 entries

New York Times
~~~~~~~~~~~~~~

The New York Times released a dataset of labelled ingredients in their `Ingredient Phrase Tagger <https://github.com/NYTimes/ingredient-phrase-tagger>`_ repository, which had the same goal as this.

* The dataset isn't very clean and the labelling is suspect in places.
* The dataset primarily uses imperial/US customary units
* The dataset is large, roughly 178,000 entries

The two datasets have different advantages and disadvantages, therefore combining the two should yield an improvement.

Processing the Data
^^^^^^^^^^^^^^^^^^^

The model chosen is a condition random fields model. This was selected because the NYTimes work on this used the same model. Rather than re-using the same tools and process the NYTimes did, this will implemented purely in ``python`` using my own ideas (although they are obviously influenced by the NYTimes work).

Step 1 is pre-processing the data. We need to do the following things to it:

1. Replace fractions with a uniform representation
2. Tokenize each ingredient sentence

The ```PreProcessor``` class handles this for us. All fractions are replaced with decimals and a custom tokenizer is used to split the sentence up so that words, commas, parantheses and quotes counted as tokens.

.. code:: python

    >>> from Preprocess import PreProcessor
    >>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
    >>> p.sentence
    '0.5 cup orange juice, freshly squeezed'
    >>> p.tokenized_sentence
    ['0.5', 'cup', 'orange', 'juice', ',', 'freshly', 'squeezed']

Extracting Features
^^^^^^^^^^^^^^^^^^^

Step 2 is to extract the features for each token in the sentence. The selected features are as follows:

* The token
* The previous token (or an empty string if the first token)
* The token 2 tokens previous (or an empty string if the second or first token)
* The next token (or an empty string if the last token)
* The token 2 tokens after (or an empty string if the last or second last token)
* Whether the token is inside parentheses
* If the token is capitalised
* If the token is numeric

.. code:: python

    def token_features(self, index: int) -> Dict[str, Any]:
        """Return the features for each token in the sentence

            Parameters
            ----------
            index : int
                Index of token to get features for.

            Returns
            -------
            Dict[str, Any]
                Dictionary of features for token at index
            """
        token = self.tokenized_sentence[index]
        return {
            "word": token,
            "prev_word": "" if index == 0 else self.tokenized_sentence[index - 1],
            "prev_word2": "" if index < 2 else self.tokenized_sentence[index - 2],
            "next_word": ""
            if index == len(self.tokenized_sentence) - 1
            else self.tokenized_sentence[index + 1],
            "next_word2": ""
            if index >= len(self.tokenized_sentence) - 2
            else self.tokenized_sentence[index + 2],
            "is_capitalised": self.is_capitalised(token),
            "is_numeric": self.is_numeric(token),
        }


It's likely that some of these features aren't necessary, but I haven't done the analysis to look at the impact of removing each one.

Step 3 is to train the model. The two datasets are combined and split into training and testing sets. The NYTimes data is limited to the first 30,000 entries to prevent it overwhelming the StrangerFoods data.

The training and testing data is transformed to get it's features and correct labelling

.. code:: python
    
    def transform_to_dataset(sentences: List[str], labels: List[Dict[str, str]]) -> tuple[List[Dict[str, str]], List[str]]:
        """Transform dataset into feature lists for each sentence

        Parameters
        ----------
        sentences : List[str]
            Sentences to transform
        labels : List[Dict[str, str]]
            Labels for tokens in each sentence

        Returns
        -------
        List[Dict[str, str]]
            List of transformed sentences
         List[str]
            List of transformed labels
        """
        X, y = [], []

        for sentence, labels in zip(sentences, labels):
            p = PreProcessor(sentence)
            X.append(p.sentence_features())
            y.append(
                [
                    match_label(p.tokenized_sentence[index], labels)
                    for index in range(len(p.tokenized_sentence))
                ]
            )

        return X, y

    X_train, y_train = transform_to_dataset(ingredients_train, labels_train)
    X_test, y_test = transform_to_dataset(ingredients_test, labels_test)

The tokens have to be matched to the label because not all words in each entry are labelled. The ``match_label`` function does this, although imperfectly since it does not handle a word appearing multiple times in a sentence

.. code:: python
    
    def match_label(token: str, labels: Dict[str, str]) -> str:
        """Match a token to it's label
        This is naive in that it assumes a token can only have one label with the sentence

        Parameters
        ----------
        token : str
            Token to match

        Returns
        -------
        str
            Label for token, or None
        """

        # Make lower case first, beccause all labels are lower case
        token = token.lower()
        token = singlarise_unit(token)

        if token in labels["quantity"]:
            return "QTY"
        elif token in labels["unit"]:
            return "UNIT"
        elif token in labels["name"]:
            return "NAME"
        elif token in labels["comment"]:
            return "COMMENT"
        else:
            return "OTHER"

Training the Model
^^^^^^^^^^^^^^^^^^

With the data ready, we can now train the model using `python-crfuite <https://github.com/scrapinghub/python-crfsuite>`_.

.. code:: python
    
    import pycrfsuite

    trainer = pycrfsuite.Trainer(verbose=False)
    for X, y in zip(X_train, y_train):
        trainer.append(X, y)
    trainer.train("model.crfsuite")

Then we can evaluate the model using the test data. For each entry in the test data, we use the model to predict the labels then calculate the accuracy score.

.. code:: python

    from sklearn import metrics

    tagger = pycrfsuite.Tagger()
    tagger.open("model.crfsuite")
    y_pred = [tagger.tag(X) for X in X_test]
    print(metrics.accuracy_score(y_test, y_pred))
    # 0.9169...

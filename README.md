# ingredient-parser

This is an attempt to create a model that can be passed an ingredient string from a recipe and extract structured data from it, for example

```
1 large onion, finely chopped
```

becomes

```python
{
    "quantity": 1,
    "unit": "large",
    "name": "onion",
    "comment": "finely chopped"
}
```
## Data sources

There are two sources of data which will be used to train the model, each with their own advantages and disadvantages.

### StrangerFoods

The recipes from my website: https://strangerfoods.org. This data is found in the ```data/strangerfoods``` folder of this repository.

* The dataset is extremely clean and well labelled. This isn't a particularly useful feature.
* The dataset primarily uses metric units
* The dataset is small, roughly 6500 entries

### New York Times

The New York Times released a dataset of labelled ingredients in their [Ingredient Phrase Tagger](https://github.com/NYTimes/ingredient-phrase-tagger) repository, which had the same goal as this.

* The dataset isn't very clean and the labelling is suspect in places.
* The dataset primarily uses imperial/US customary units
* The dataset is large, roughly 180,000 entries

The two datasets have different advantages and disadvantages, therefore combining the two should yield an improvement.

## Training the model

The model chosen is a condition random fields model. This was selected because the NYTimes work on this used the same model. Rather than re-using the same tools and process the NYTimes did, this will implemented purely in ```python``` using my own ideas (although they are obviously influenced by the NYTimes work).

Step 1 is pre-processing the data. We need to do the following things to it:

1. Replace fractions with a uniform representation
2. Tokenize each ingredient sentence

The ```PreProcessor``` class handles this for us. All fractions are replaced with decimals and a custom tokenizer is used to split the sentence up so that words, commas, parantheses and quotes counted as tokens.

```python
from Preprocess import PreProcessor
>>> p = PreProcessor("1/2 cup orange juice, freshly squeezed")
>>> p.sentence
'0.5 cup orange juice, freshly squeezed'
>>> p.tokenized_sentence
['0.5', 'cup', 'orange', 'juice', ',', 'freshly', 'squeezed']
```

Step 2 is to extract the features for each token in the sentence. The selected features are as follows:

* The token
* The previous token (or an empty string if the first token)
* The token 2 tokens previous (or an empty string if the second or first token)
* The next token (or an empty string if the last token)
* The token 2 tokens after (or an empty string if the last or second last token)
* Whether the token is inside parentheses
* If the token is capitalised
* If the token is numeric

```python
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
```



It's likely that some of these features aren't necessary, but I haven't done the analysis to look at the impact of removing each one.

Step 3 is to train the model. The two datasets are combined and split into training and testing sets. The NYTimes data is limited to the first 30,000 entries to prevent it overwhelming the StrangerFoods data.

The training and testing data is transformed to get it's features and correct labelling

```python
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
```

The tokens have to be matched to the label because not all words in each entry are labelled. The ```match_label``` function does this, although imperfectly since it does not handle a word appearing multiple times in a sentence

```python
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

    # TODO:
    # 1. Handle ingredients that have both US and metric units (or remove them from training data...)
    # 2. Singularise all units so they match the label

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
```

With the data ready, we can now train the model using [```sklearn_crfsuite```](https://github.com/TeamHG-Memex/sklearn-crfsuite).

```python
from sklearn_crfsuite import CRF

model = CRF()
model.fit(X_train, y_train)
```

Then we can evaluate the model using the test data. For each entry in the test data, we use the model to predict the labels then calculate the accuracy score.

```python
from sklearn_crfsuite import metrics

y_pred = model.predict(X_test)
print(metrics.flat_accuracy_score(y_test, y_pred))
# 0.9039365676383135
```

All of the above steps are implemented in the ```tools/train.py``` script.

## Using the model

If you don't want the train the model yourself, then a pre-trained model is provided in the ```ingredient_parser``` package

```python
>>> from ingredient_parser import parse_ingredient

>>> parse_ingredient("3 pounds pork shoulder, cut into 2-inch chunks")
{'sentence': '3 pounds pork shoulder, cut into 2-inch chunks',
 'quantity': '3',
 'unit': 'pound',
 'name': 'pork shoulder',
 'comment': 'cut into 2-inch chunks'}

# Output confidence for each label
>>> parse_ingredient("3 pounds pork shoulder, cut into 2-inch chunks", confidence=True)
{'sentence': '3 pounds pork shoulder, cut into 2-inch chunks',
 'quantity': '3',
 'unit': 'pound',
 'name': 'pork shoulder',
 'comment': 'cut into 2-inch chunks',
 'confidence': {'quantity': 0.9976,
  'unit': 0.9913,
  'name': 0.9291,
  'comment': 0.9801}}
```

This requires ```sklearn_crfsuite``` to run.

## Model accuracy

The model provided in ```ingredient-parser/``` directory has the following accuracy on a test dataset of 9227 sentences:

```
Sentence-level results:
	Total: 9227
	Correct: 6924
	-> 75.04%

Word-level results:
	Total: 53740
	Correct: 49276
	-> 91.69%
```

My interpretation of these results is the the high word-level accuracy compared to the lower sentence-level accuracy means that if the model is getting a label wrong, it's usually only one label in the sentence.

## To do list

- [ ] Clean up the NYTimes data.
- [x] Change library from ```sklearn_crfsuite``` to [```python_crfsuite```](https://github.com/scrapinghub/python-crfsuite) because the ```sklearn_crfsuite``` appears to be unmaintained and breaking in newer versions of python. 
- [ ] Investigate which features are most relevant and which can be removed
  - [ ] The model ```state_features_``` property can help here
- [ ] Investigate whether it's reasonable to use the first 20,000 entries in the NYTimes dataset.
  - [ ] Should it be more?
  - [ ] Should it be randomly selected?
- [x] Output confidence scores using ```model.predict_marginals()```
- [x] Write a tool that uses the model and return a dict like the one at the top of this README.
- [ ] Compare the model results to my regular expression based parser.

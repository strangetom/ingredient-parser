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
    "item": "onion",
    "comment": "finely chopped"
}
```
## Data sources

There are two sources of data which will be used to train the model.

1. The recipes from my website: https://strangerfoods.org. This data is found in the ```data/strangerfoods``` folder of this repository.

2. [nyt-ingredients-snapshot-2015.csv](https://github.com/nytimes/ingredient-phrase-tagger/blob/master/nyt-ingredients-snapshot-2015.csv), from the NY Times [Ingredient Phrase Tagger](https://github.com/NYTimes/ingredient-phrase-tagger) repository.

The two sources are formatted differently, but I'll deal with that later.

## Thinking

We're going to use scikit-learn and probably a decision tree classifier but TBD.

The pipeline is going to be along the lines

1. Pre-process the training data
2. Generate features from the data
3. Train model

To pre-process the training data, we're going to want to:

* Replace all fractions (including unicode) with decimals
* Attempt to singularise all units (although since we want to the classifier to identify the units this is a bit of a chicken-egg problem)

Suggested features to for each word in the sentence are:

* The word
* The preceding word(s) (if not first)
* The following word(s) (if not last)
* Whether the word is inside parentheses
* Whether the word follows a comma
* If the word is first
* If the word is capitalised
* It the word is numeric
* The Part Of Speech tag for the word

The suggestion of a decision tree classifier is based of [this](https://nlpforhackers.io/training-pos-tagger/) tutorial for Part Of Speech tagging, but it doesn't look like a unreasonable starting place.

### Other things I might do

The training data from NYTimes isn't very tidy and it's a bit difficult to match the label to the token in the sentence, so there might be a way to reformat the data to make that better.




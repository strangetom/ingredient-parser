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
The model will be created using Conditional Random Fields, using an approach borrowed from NY Times [Ingredient Phrase Tagger][https://github.com/NYTimes/ingredient-phrase-tagger].

## Data sources

There are two sources of data which will be used to train the model.

1. The recipes from my website: https://strangerfoods.org. This data is found in  ```training_data.csv``` in the ```data/``` folder of this repository.

2. [nyt-ingredients-snapshot-2015.csv](https://github.com/nytimes/ingredient-phrase-tagger/blob/master/nyt-ingredients-snapshot-2015.csv), from the NY Times [Ingredient Phrase Tagger](https://github.com/NYTimes/ingredient-phrase-tagger) repository.

The two sources are formatted differently, but I'll deal with that later.

## Training the model

Instructions of training the model once I've created a model.

## Using the model

The pre-trained model will be provided in the ```model/``` folder of this repository.

Instructions on usage once I've actually created a model.

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
The model will be created using Conditional Random Fields, using an approach borrowed from NY Times [Ingredient Phrase Tagger](https://github.com/NYTimes/ingredient-phrase-tagger).

## Data sources

There are two sources of data which will be used to train the model.

1. The recipes from my website: https://strangerfoods.org. This data is found in  ```training_data.csv``` and ```testing_data.csv``` in the ```data/``` folder of this repository.

2. [nyt-ingredients-snapshot-2015.csv](https://github.com/nytimes/ingredient-phrase-tagger/blob/master/nyt-ingredients-snapshot-2015.csv), from the NY Times [Ingredient Phrase Tagger](https://github.com/NYTimes/ingredient-phrase-tagger) repository.

The two sources are formatted differently, but I'll deal with that later.

## Training the model

This requires a working installation of [CRF++](https://taku910.github.io/crfpp/). There's a bug in the latest release (and it seems to be unmaintained) so either look at [PR#15](https://github.com/taku910/crfpp/pull/15) or [this fork](https://github.com/mtlynch/crfpp) by mylynch.

### Generating data files

Generate training and testing data csv files.

1. ```generate_labelled_data.py``` generates a ```labelled_data.csv``` from the recipes found on https://strangerfoods.org.

2. ```generate_training_testing_data_from_csv.py``` takes the csv file, splits the data into training and testing datasets and generates .crf files in the format required by CRF++ using the following command:

   ```bash
   >>> python generate_training_testing_data_from_csv.py -i labelled_data.csv -o training_data.crf -t testing_data.crf 
   ```


### Train model using CRF++

With the ```.crf``` files created as above, training is straightforward with the ```crf_learn``` command.

```bash
>>> crf_learn models/template_file data/training_data.crf models/model.crfmodel
```

### Evaluate model

The model is written to ```models/models.crfmodel```.

We can use the ```crf_test``` command to run the ```testing_data.crf``` through the model to generate some results.

```bash
>>> crf_test -m models/model.crfmodel data/testing_data.crf > test/testing_results.crf      
```

The ```evaluate_model.py``` script will parse the ```testing_results.crf``` file and output a summary of the results:

```bash
Sentence-level results:
	Total: 1481
	Correct: 1390
	-> 93.86%

Word-level results:
	Total: 8280
	Correct: 8060
	-> 97.34%

```

## Using the model

The pre-trained model will be provided in the ```models/``` folder of this repository.

Instructions coming later.

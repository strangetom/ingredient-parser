# Model Card

## Model Details

### Person or Organisation

<https://github.com/strangetom>

### Model Date and Version

Date: August 2023

Version: The model version is the same has the `ingredient_parser_nlp` package version.

### Model Type

Natural language model for parsing structured information from recipe ingredient sentences.

The model is a Conditional Random Fields (CRF) model, implemented using [pycrfsuite](https://github.com/scrapinghub/python-crfsuite). A pre-processing step is required before a sentence can be presented to the model, which performs a number of text normalisation operations. See [preprocess.py](https://github.com/strangetom/ingredient-parser/blob/master/ingredient_parser/preprocess.py). 

### License

The model, including the training data and training scripts and python package, are released under an [MIT License](https://github.com/strangetom/ingredient-parser/blob/master/LICENSE).

### Questions or Comments

Questions or comments can be raised by opening an issue on GitHub: https://github.com/strangetom/ingredient-parser/issues.

## Intended Use

The ingredient parser model parses structured information from English language ingredient sentences.

### Primary Intended Uses

- Parse the following information from English language recipe ingredient sentences:
  - Quantity of ingredient
  - Unit of ingredient
  - Name of ingredient
  - Comment
  - Other, for text that cannot be classified into one of the above labels

### Primary Intended Users

- Developers and users of recipe management software or services

### Out-of-Scope Uses

- The model only support English language sentences.
- The model only supports the Latin alphabet and standard special characters.
- The model only supports parsing one ingredient sentence at a time. Attempting to pass a string containing multiple sentences is not supported and has not been tested.

## Limitations

The model has been trained on datasets that have limitations.

- The New York Times dataset contains sentences that largely follow a consistent style, use US customary units, and often refer to ingredients or brands found only in the USA.
- The Cookstr dataset contains sentences that use US customary units as the primary unit, and often refer to ingredients or brands found only in the USA.
- The StrangerFoods dataset is based on information collated from a large number of sources. Due to the way in which the data extracted from the source database, the sentences are automatically labelled, which introduces inconsistencies.

Certain sentence formats, such as consecutive numbers that should not be combined (e.g. 1 2-ounce steak) are not well managed in the preprocessing step and can result in unexpected parsing results.

## Metrics

Word level accuracy measures the percentage of words in the evaluation data that were correctly labelled.

Sentence level accuracy measures the percentage of ingredient sentences where all words were correctly labelled.

## Training and Evaluation Data

There are 3 datasets used to train and evaluate model performance.

1. New York Times, originally found at https://github.com/nytimes/ingredient-phrase-tagger.

   The first 30,000 sentences are used in the training and evaluation of the model.

2. Cookstr, originally found as part of https://archive.org/details/recipes-en-201706.

   The first 10,000 sentences are used in the training and evaluation of the model.

3. StrangerFoods, found at https://strangerfoods.org

   All sentences are used in the training and evaluation of the model.

The New York Times and Cookstr datasets have been through extensive cleaning to make the data consistent. The cleaned versions of the data are found in the repository for the ingredient_parser_nlp package: https://github.com/strangetom/ingredient-parser

The model is trained on a randomised set of 75% of the total data, and evaluated on the remaining 25%.

## Quantitative Analysis

The model has the following performance metrics:

| Word level accuracy | Sentence level accuracy |
| ------------------- | ----------------------- |
| 96.25%              | 89.58%                  |

Due to the randomisation of the selection of training and evaluation data, the word level accuracy metric can vary by ±0.3 pp and the sentence level accuracy can vary by ±0.8 pp between model training runs.

## Ethical Considerations

There are no known ethical considerations related to this model.

## Caveats and Recommendations

The model is under active development and the stated performance is likely to change between releases. Best efforts will be made to keep this model card up to date.
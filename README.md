# Ingredient Parser

The Ingredient Parser package is a Python package for parsing structured information out of recipe ingredient sentences.

![](docs/source/_static/logo.png)

## Documentation

Documentation on using the package and training the model can be found at https://ingredient-parser.readthedocs.io/.

## Quick Start

Install the package using pip

```bash
$ python -m pip install ingredient-parser-nlp
```

Import the ```parse_ingredient``` function and pass it an ingredient sentence.

```python
>>> from ingredient_parser import parse_ingredient
>>> parse_ingredient("3 pounds pork shoulder, cut into 2-inch chunks")
ParsedIngredient(
    name=IngredientText(text='pork shoulder', confidence=0.999193),
    size=None,
    amount=[IngredientAmount(quantity='3',
                             unit=<Unit('pound')>,
                             text='3 pounds',
                             confidence=0.999906,,
                             APPROXIMATE=False,
                             SINGULAR=False)],
    preparation=IngredientText(text='cut into 2 inch chunks', confidence=0.999193),
    comment=None,
    purpose=None,
    sentence='3 pounds pork shoulder, cut into 2-inch chunks'
)
```

Refer to the documentation [here](https://ingredient-parser.readthedocs.io/en/latest/start/index.html#optional-parameters) for the optional parameters that can be used with `parse_ingredient` .

## Model

The core of the library is a sequence labelling model that is used to label each token in the sentence with the part of the sentence it belongs to. A data set of 75,000 example sentences is used to train and evaluate the model. See the [Model Guide](https://ingredient-parser.readthedocs.io/en/latest/guide/index.html) in the documentation for mode details.

The model has the following accuracy on a test data set of 20% of the total data used:

```
Sentence-level results:
	Accuracy: 95.86%

Word-level results:
	Accuracy 98.41%
	Precision (micro) 98.41%
	Recall (micro) 98.41%
	F1 score (micro) 98.41%
```

## Development

The development dependencies are in the ```requirements-dev.txt``` file. Details on the training process can be found in the [Model Guide](https://ingredient-parser.readthedocs.io/en/latest/guide/index.html) documentation.

Before committing anything, install [pre-commit](https://pre-commit.com/) and run
```
pre-commit install
```

to install the pre-commit hooks.

There is a simple web app for testing the parser with ingredient sentences and showing the parsed output. To run the web app, run the command

```bash
$ flask --app webapp run
```

![Screen shot of web app](docs/source/_static/app-screenshot.png)

This requires the development dependencies to be installed.

The dependencies for building the documentation are in the ```requirements-doc.txt``` file.

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
    name=IngredientText(text='pork shoulder', confidence=0.999196),
    amount=[IngredientAmount(quantity='3',
                             unit='pounds',
                             text='3 pounds',
                             confidence=0.998769,
                             APPROXIMATE=False,
                             SINGULAR=False)],
    preparation=IngredientText(text='cut into 2 inch chunks', confidence=0.995614),
    comment=None,
    sentence='3 pounds pork shoulder, cut into 2-inch chunks'
)
```

## Model accuracy

The model used for labelling tokens in sentences, provided in the ```ingredient-parser/``` directory, has the following accuracy on a test data set of 25% of the total  data used:

```
Sentence-level results:
	Total: 14982
	Correct: 14021
	Incorrect: 961
	-> 93.59% correct

Word-level results:
	Total: 105360
	Correct: 102741
	Incorrect: 2619
	-> 97.51% correct
```

## Development

The development dependencies are in the ```requirements-dev.txt``` file. Details on the training process can be found in the [Model Guide](https://ingredient-parser.readthedocs.io/en/latest/guide/index.html) documentation.

There is a simple web app for testing the parser with ingredient sentences and showing the parsed output. To run the web app, run the command

```bash
$ flask --app webapp run
```

![Screen shot of web app](docs/source/_static/app-screenshot.png)

This requires the development dependencies to be installed.

The dependencies for building the documentation are in the ```requirements-doc.txt``` file.

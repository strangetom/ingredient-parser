# Ingredient Parser

The Ingredient Parser package is a Python package for parsing structured information out of recipe ingredient sentences.

![](docs/source/_static/logo.svg)

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
    name=IngredientText(text='pork shoulder', confidence=0.997265), 
    amount=[IngredientAmount(quantity='3', 
                             unit='pounds', 
                             confidence=0.9991, 
                             APPROXIMATE=False, 
                             SINGULAR=False)], 
    preparation=IngredientText(text='cut into 2 inch chunks', confidence=0.986157),
    comment=None, 
    other=None, 
    sentence='3 pounds pork shoulder, cut into 2-inch chunks'
)
```

## Model accuracy

The model used for labelling tokens in sentences, provided in the ```ingredient-parser/``` directory, has the following accuracy on a test data set of 25% of the total  data used:

```
Sentence-level results:
	Total: 12501
	Correct: 11515
	Incorrect: 986
	-> 92.11% correct

Word-level results:
	Total: 85262
	Correct: 82718
	Incorrect: 2544
	-> 97.02% correct
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

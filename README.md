# Ingredient Parser

The Ingredient Parser package is a Python package for parsing structured information out of recipe ingredient sentences.

![](docs/source/_static/logo.svg)

## Documentation

Documentation on using the package and training the model can be found at https://ingredient-parser.readthedocs.io/en/latest/.

## Quick Start

Install the package using pip

```bash
python -m pip install ingredient-parser-nlp
```

Import the ```parse_ingredient``` function and pass it an ingredient sentence.

```python
>>> from ingredient_parser import parse_ingredient

>>> parse_ingredient("3 pounds pork shoulder, cut into 2-inch chunks")
ParsedIngredient(
    sentence='3 pounds pork should, cut into 2-inch chunks', 
    quantity='3', 
    unit='pounds', 
    name='pork shoulder', 
    comment='cut into 2-inch chunks', 
    other='', 
    confidence=ParsedIngredientConfidence(
        quantity=0.9986, 
        unit=0.9972, 
        name=0.8474, 
        comment=0.9991, 
        other=0
    )
)
```

## Model accuracy

The model used for labelling tokens in sentences, provided in ```ingredient-parser/``` directory has the following accuracy on a test data set of 25% of the total  data used:

```
Sentence-level results:
	Total: 12044
	Correct: 10834
	Incorrect: 1210
	-> 89.95% correct

Word-level results:
	Total: 76299
	Correct: 73430
	Incorrect: 2869
	-> 96.24% correct
```

## Development

The development dependencies are in the ```requirements-dev.txt``` file. Details on the training process can be found in the [Model Guide](https://ingredient-parser.readthedocs.io/en/latest/guide/index.html) documentation.

There is a simple webapp for testing the parser with ingredient sentences and showing the parsed output. To run the webapp, run the command

```bash
>>> flask --app webapp run
```

This requires the development dependencies to be installed.

The documentation dependencies are in the ```requirement-doc.txt``` file.

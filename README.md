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

The model provided in ```ingredient-parser/``` directory has the following accuracy on a test data set of 25% of the total  data used:

```
Sentence-level results:
	Total: 12030
	Correct: 10776
	Incorrect: 1254
	-> 89.58% correct

Word-level results:
	Total: 75146
	Correct: 72329
	Incorrect: 2817
	-> 96.25% correct
```

## Development

The development dependencies are in the ```requirements-dev.txt``` file.

Note that development includes training the model.

* ```Black``` is used for code formatting.
* ```ruff``` is used for linting. 
* ```pyright``` is used for type static analysis.
* ```pytest``` is used for tests, with ```coverage``` being used for test coverage.

The documentation dependencies are in the ```requirement-doc.txt``` file.

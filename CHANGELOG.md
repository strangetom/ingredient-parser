# Changelog

## 2.0.0 [unreleased]

> [!Caution]
>
> This release contains some breaking changes

1. `ParsedIngredient.name` returns a list of `IngredientText` objects, or an empty list no name is identified.

2. The `quantity_fractions` optional keyword argument has been removed. `IngredientAmount.quantity` and `IngredientAmount.quantity_max` return `fractions.Fraction` objects. Conversion to `float` can be achieved by e.g.:

    ```python
    # Round to 3 decimal places
    round(float(quantity), 3)
    ```

3. New dependency: [floret](https://github.com/explosion/floret).

### Processing

* Identify where multiple alternative ingredients are given for the stated amount. For example

    ```python
    # Simple example
    >>> parse_ingredient("2 tbsp butter or olive oil").name
    [
      IngredientText(text='butter', confidence=0.983045, starting_index=2),
      IngredientText(text='olive oil', confidence=0.930385, starting_index=4)
    ]
    # Complex example
    >>> parse_ingredient("2 cups chicken or beef stock").name
    [
      IngredientText(text='chicken stock', confidence=0.776891, starting_index=2),
      IngredientText(text='beef stock', confidence=0.94334, starting_index=4)
    ]
    ```

    This is enabled by default, but can be disabled by setting `separate_ingredients=False` in `parse_ingredient`. If disabled, the `ParsedIngredient.name` field will only contain a single `IngredientText` object.

* Set `PREPARED_INGREDIENT` flag on amounts in cases like 

  > ... to yield 2 cups ...
  
* Add `convert_to(...)` function to `IngredientAmount` dataclass. This returns the `IngredientAmount` object  converted to the given units.

  ```python
  >>> p = parse_ingredient("1 8 ounce can chopped tomatoes")
  >>> # Convert "8 ounce" to grams
  >>> p.amount[1].convert_to("g")
  IngredientAmount(quantity=Fraction(5669904625000001, 25000000000000),
                   quantity_max=Fraction(5669904625000001, 25000000000000),
                   unit=<Unit('gram')>,
                   text='226.80 gram',
                   confidence=0.999051,
                   starting_index=1,
                   APPROXIMATE=False,
                   SINGULAR=True,
                   RANGE=False,
                   MULTIPLIER=False,
                   PREPARED_INGREDIENT=False)
  
  >>> # Cannot convert where the quantity or unit is a string
  >>> p.amount[0].convert_to("g")
  TypeError: Cannot convert with string quantities or units.
  ```

  

### Model

* Include custom word embeddings as features used by the model. This requires a new dependency of the [floret](https://github.com/explosion/floret) library.

## 1.3.2

### Processing

* Fix bug that allowed fractions in the intermediate form (i.e. #1$2) to appear in the name, prep, comment, size, purpose fields of the `ParsedIngredient` output.

## 1.3.1

> [!WARNING]
>
> This version requires pint >=0.24.4

### General

* Support Python 3.13. Requires pint >= 0.24.4.

## 1.3

### Processing

* Various minor improvements to feature generation.

* Add PREPARED_INGREDIENT flag to IngredientAmount objects. This is used to indicate if the amount refers to the prepared ingredient (`PREPARED_INGREDIENT=True`) or the unpreprared ingredient (`PREPARED_INGREDIENT=False`).

* Add `starting_index` attribute to IngredientText objects, indicating the index of the token that starts the IngredientText. 

* Improve detection of composite amounts in sentences.

* Add `quantity_fractions` keyword argument to `parse_ingredient`. When True, the `quantity` and `quantity_max` fields of `IngredientAmount` objects will be `fractions.Fraction` objects instead of floats. This allows fractions such as 1/3 to be represented exactly. The default behaviour is when `quantity_fractions=False`, where quantities are floats as previously. For Example

  ```python
  >>> parse_ingredient("1 1/3 cups flour").amount[0]
  IngredientAmount(
      quantity=1.333,
      quantity_max=1.333,
      unit=<Unit('cup')>, 
      text='1 1/3 cups', 
      ...
  )
  >>> parse_ingredient("1 1/3 cups flour", quantity_fractions=True).amount[0]
  IngredientAmount(
      quantity=Fraction(4, 3),
      quantity_max=Fraction(4, 3),
      unit=<Unit('cup')>,
      text='1 1/3 cups',
      ...
  )
  ```


### Model

* Addition of new dataset: tastecooking. This is a relatively small dataset, but includes a number of unique abbreviations for units and sizes.

## 1.2

### General

* New optional keyword argument to extract foundation foods from the ingredient name. Foundation foods are the fundamental item of food, excluding any qualifiers or descriptive adjectives, e.g. for the name `organic cucumber`, the foundation food is `cucumber`. 

  See https://ingredient-parser.readthedocs.io/en/latest/guide/foundation.html for additional details.

* Some minor post processing fixes.

## 1.1.2

Require NLTK >= 3.9.1, due to change in their resources format.

## 1.1.1

Revert upgrade to NLTK 3.8.2 after 3.8.2 removed from PyPI.

## 1.1

### General

Require NLTK >= 3.8.2 due to change in POS tagger weights format.

### Model

* Include new tokens features, which help improve performance:
  * Word shape (e.g. cheese -> xxxxxx; Cheese -> Xxxxxx)
  * N-gram (n=3, 4, 5) prefixes and suffixes of tokens
* Add 15,000 new sentences to training data from AllRecipes. This dataset includes lots of branded ingredients, which the existing datasets were quite light on.
* Tweaks to the model hyperparameters have yielded a model that is ~25% smaller, but with better performance than the previous model.

### Processing

* Change processing of numbers written as words (e.g. 'one', 'two' ). If the token is labelled as QTY, then the number will converted to a digit (i.e. 'one' -> 1) or collapsed into a range (i.e. 'one or two' -> 1-2), otherwise the token is left unchanged.

## 1.0.1

> [!WARNING]
>
> This version requires NLTK >=3.8.2

NLTK 3.8.2 changes the file format (from pickle to json) of the weights used by the part of speech tagger used in this project, to address some security concerns. This patch updates the NLTK resource checks performed when `ingredient-parser` is imported to check for the new json files, and downloads them if they are not present. 

This version requires NLTK>=3.8.2.

## 1.0

### General

* Improve performance when tagging multiple sentences. For large numbers of sentences (>1000), the performance improvement is ~100x.

### Processing

* Extend support for composite amounts that have the form e.g. `1 cup plus 1 tablespoon` or `1 cup minus 1 tablespoon`. Previously the phrase `plus/minus 1 tablespoon` would be returned in the comment. Now the whole phrase is captured as a `CompositeAmount` object.
* Fix cases where the incorrect `pint.Unit` would be returned, caused by pint interpreting the unit as something else e.g. "pinch" -> "pico-inch".

## 0.1.0-beta11

### General

* Refactor package structure to make it more suitable for expansion to over languages. 

  **Note:** There aren't any plans to support other languages yet.

### Model

* Reduce duplication in training data
* Introduce PURPOSE label for tokens that describe the purpose of the ingredient, such as `for the dressing` and `for garnish`.
* Replace quantities with "!num" when determining the features for tokens so that the model doesn't need to learn all possible values quantities can take. This results in a small reduction in model size.

### Processing

* Various bug fixes to post-processing of tokens with labels NAME, COMMENT, PREP, PURPOSE, SIZE to correct punctuation and confidence calculations.
* Modification of tokeniser to split full stops from the end of tokens. This helps to model avoid treating "`token.`" and "`token`" as different cases to learn.
* Add fallback functionality to `parse_ingredient` for cases where none of the tokens are labelled as NAME. This will select name as the token with the highest confidence of being labelled NAME, even though a different label has a high confidence for that token. This can be disabled by setting `expect_name_in_output=False` in `parse_ingredient`.

## 0.1.0-beta10

### Bugfix

Fix incorrect python version specifier in package which was preventing pip in Python 3.12 downloading the latest version.

## 0.1.0-beta9

### General

- Add github actions to run tests (#7, @boxydog)

- Add pre-commit for use with development  (#10, @boxydog)

### Model 

- Add additional model performance metrics.
- Add model hyper-parameter tuning functionality with `python train.py gridsearch` to iterate over specified training algorithms and hyper-parameters.
- Add `--detailed` argument to output detailed information about model performance on test data.  (#9, @boxydog)
- Change model labels to treat label all punctuation as PUNC - this resolves some of the ambiguity in token labeling
- Introduce SIZE label for tokens that modify the size of the ingredient. Note that his only applies to size modifiers of the ingredient. Size modifiers of the unit will remain part of the unit e.g. large clove.

### Processing

- Integration of `pint` library for units

  - By default, units in `IngredientAmount` object will be returned as `pint.Unit` objects (where possible). This enables the easy conversion of amounts between different units. This can be disabled by setting `string_units=True` in the `parse_ingredient` function calls.

  - For units that have US customary and Imperial version with the same name (e.g, cup), setting `imperial_units=True` in the `parse_ingredient` function calls will return the imperial version. The default is US customary.
  - This only applies to units in `pint`'s unit registry (basically all common, standardised units). If the unit can't be found, then the string is returned as previously.

- Additions to `IngredientAmount` object:

  - New `quantity_max` field for handling upper limit of ranges. If the quantity is not a range, this will default to same as the `quantity` field.
  - Flags for RANGE and MULTIPLIER
    - RANGE is set to True for quantity ranges e.g. `1-2`
    - MULTIPLIER is set to True for quantities like `1x`
  - Conversion of quantity field to `float` where possible
- PreProcessor improvements 
  - Be less aggressive about replacing written numbers (e.g. one) with the digit version. For example, in sentences like `1 tsp Chinese five-spice`, `five-spice` is now kept as written instead of being replaced by two tokens: `5 spice`.
  - Improve handling of ranges that duplicate the units e.g. `1 pound to 2 pound` is now returned as `1-2 pound`


## 0.1.0-beta8

### General

- Support Python 3.12

### Model

- Include more training data, expanding the Cookstr and BBC data by 5,000 additional sentences each
- Change how the training data is stored. An SQLite database is now used to store the sentences and their tokens and labels. This fixes a long standing bug where tokens in the training data would be assigned the wrong label. csv exports are still available.
- Discard any sentences containing OTHER label prior to training model, so a parsed ingredient sentence can never contain anything labelled OTHER.

### Processing

- Remove `other` field from `ParsedIngredient` return from `parse_ingredient` function.

- Added `text` field to `IngredientAmount`. This is auto-generated on when the object is created and proves a human readable string for the amount e.g. "100 g"

- Allow SINGULAR flag to be set if the amount it's being applied to is in brackets

- Where a sentence has multiple related amounts e.g. `14 ounce (400 g)` , any flags set for one of the related amounts are applied to all the related amounts

- Rewrite the tokeniser so it doesn't require all handled characters to be explicitly stated

- Add an option to `parse_ingredient` to discard isolated stop words that appear in the name, comment and preparation fields.

- `IngredientAmount.amount` elements are now ordered to match the order in which they appear in the sentence.

- Initial support for composite ingredient amounts e.g. `1 lb 2 oz`  is now consider to be a single `CompositeIngredientAmount`  instead of two separate `IngredientAmount`.

  - Further work required to handle other cases such `1 tablespoon plus 1 teaspoon`.
  - This solution may change as it develops

## 0.1.0-beta7

- Automatically download required NLTK resources if they're not found when importing
- Require python version <3.12 because python-crfsuite does not yet support 3.12
- Various minor tweaks and fixes.

## 0.1.0-beta6
- Support parsing of preparation steps from ingredients e.g. finely chopped, diced
  - These are returned in the `ParsedIngredient.preparation` field instead of the comment field as previously
- Removal of StrangerFoods dataset from model training due to lack of PREP labels
- Addition of a BBC Food dataset in the model training
  - 10,000 additional ingredient sentences from the archive of 10599 recipes found at https://archive.org/details/recipes-en-201706
- Miscellaneous bug fixes to the preprocessing steps to resolve reported issues
  - Handling of fractions with the format: 1 and 1/2
  - Handling of amounts followed by 'x' e.g. 1x can
  - Handling of ranges where the units were duplicated: 100g - 200g

## 0.1.0-beta5

- Support the extraction of multiple amounts from the input sentence.
- Change output dataclass to put confidence values with each field.
  - The name, comment, other fields are output as an `IngredientText` object containing the text and confidence
  - The amounts are output as an `IngredientAmount` object containing the quantity, unit, confidence and flags for whether the amount is approximate or for a singular item of the ingredient.
- Rewrite post-processing functionality to make it more maintainable and extensible in the future.
- Add a [model card](https://github.com/strangetom/ingredient-parser/blob/master/ingredient_parser/ModelCard.md), which provides information about the data used to train and evaluate the model, the purpose of the model and it's limitations.
- Increase l1 regularisation during model training.
  - This reduces model size by a factor of ~4.
  - This should improve performance on sentences not seen before by forcing to the model to rely less on labelling specific words.
- Improve the model guide in the documentation.
- Add a simple webapp that can be used to view the output of the parser in a more human-readable way.

Example of the output at this release

```python
>>> parse_ingredient("50ml/2fl oz/3½tbsp lavender honey (or other runny honey if unavailable)")
ParsedIngredient(
    name=IngredientText(
        text='lavender honey',
        confidence=0.998829),
    amount=[
        IngredientAmount(
            quantity='50',
            unit='ml',
            confidence=0.999189,
            APPROXIMATE=False,
            SINGULAR=False),
        IngredientAmount(
            quantity='2',
            unit='fl oz',
            confidence=0.980392,
            APPROXIMATE=False,
            SINGULAR=False),
        IngredientAmount(
            quantity='3.5',
            unit='tbsps',
            confidence=0.990711,
            APPROXIMATE=False,
            SINGULAR=False)
    ],
    comment=IngredientText(
            text='(or other runny honey if  unavailable)',
            confidence=0.973682
    ),
    other=None,
    sentence='50ml/2fl oz/3½tbsp lavender honey (or other runny  honey if unavailable)'
)
```

## 0.1.0-beta4

- Include new source of training data: cookstr.

  - 10,000 additional ingredient sentences from the archive of 7918 recipes (~40,000 total ingredient sentences) found at https://archive.org/details/recipes-en-201706 are now used in the training of the model.

- The parse_ingredient function now returns a  `ParsedIngredient`  dataclass instead of a dict.
  - Remove dependency on typing_extensions as a result of this

- A model card is now provided that gives details about how the model was trained, performs, is intended to be used, and limitations.

  - The model card is distributed with the package and there is a function `show_model_card()` that will open the model card in the default application for markdown files.

- Improvements to the ingredient sentence preprocessing:

  - Expand the list of units
  - Tweak the tokenizer to handle more punctuation
  - Fix various bugs with the cleaning steps

As a result of these updates the model performance has improved to:

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

## 0.1.0-beta3

Correct minimum python version to 3.10 due to use of type hints introduced in 3.10.

## 0.1.0-beta2

- Add new feature that indicates if a token is ambiguous, for example "clove" could be a unit or a name.
- Add preprocessing step to remove trailing periods from certain units e.g. `tsp.` becomes `tsp`

## 0.1.0-beta1

- Change the features extracted from an ingredient sentence
  - Replace the word with the stem of the word
  - Add feature for follows "plus"
  - Change features combining current and next/previous part of speech to just use the next/previous part of speech
- Improve handling of plural units
  - Units are made singular before passing to CRF model. The repluralisation of units is based on whether they were made singular in the first place or not.
- Add test cases for the parser_ingredient function
  - Not all test cases pass yet - failures will be future improvements (hopefully)
- Better align behaviour of regex parser with CRF-based parser.

## 0.1.0-alpha4

- Minor fixes to documentation
- Apply re-pluralization to regex parser

## 0.1.0-alpha3

Incremental changes:

- Fix re-pluralisation of units not actually working in 0.1.0-alpha2.
- Configure development tools in pyproject.toml.
- Fixes to documentation.
- Fixes to NYT data.
- Additional sentence features:
  - is_stop_word
  - is_after_comma
- Only create features that are possible for the token e.g. there is no prev_word for the first token, so don't create the feature at all instead of using an empty string.
- Refactor code for easier maintenance and flake8 compliance .

## 0.1.0-alpha2

Incremental changes:

- Improved documentation
  - Automatically extract code and version from source files.
- Added regular expression based parser
  - This provides an alternative to the CRF-based parser, but is more limited
- Improvements to labelling of New York Times dataset
  - Label size modifiers for unit as part of the unit e.g. large clove, small bunch
  - Consistent labelling of "juice of..." variants
  - Consistent labelling of "chopped"
  - Consistent labelling of "package"
  - Reduce number of token labelled as OTHER because they were missing from the label
- Fixes and improvements to pre-processing input sentences
  - Expand list of units to be singularised
  - Fix the preprocessing incorrectly handling words with different cases
  - Improve matching and replacement of string numbers e.g. one -> 1
  - Fix unicode fraction replacement not replacing
- Improvements to post-processing the model output
  - Pluralise units if the quantity is not singular
- Start adding tests to PreProcessor class methods

## 0.1.0-alpha1

Initial release of package.

There are probably a bunch of errors to fix and improvements to make since this is my first attempt and building a python package.

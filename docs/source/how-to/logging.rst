Logging
=======

Python’s standard `logging <https://docs.python.org/3/library/logging.html>`_ module is used to implement debug log output for ingredient-parser.
This allows ingredient-parser's logging to integrate in a standard way with other application and libraries.

All logging for ingredient-parser is within ``ingredient-parser`` namespace.

* The ``ingredient-parser`` namespace contains general logging for parsing of ingredient sentences.
* The ``ingredient-parser.foundation-foods`` namespace contains logging related to the :doc:`Foundation Foods </explanation/foundation>` functionality.

For example, to output debug logs to stdout:

.. code:: python

  >>> import logging, sys
  >>> from ingredient_parser import parse_ingredient
  >>>
  >>> logging.basicConfig(stream=sys.stdout)
  >>> logging.getLogger("ingredient-parser").setLevel(logging.DEBUG)
  >>>
  >>> parsed = parse_ingredient("24 fresh basil leaves or dried basil")
  DEBUG:ingredient-parser:Parsing sentence "24 fresh basil leaves or dried basil" using "en" parser.
  DEBUG:ingredient-parser:Normalised sentence: "24 fresh basil leaves or dried basil".
  DEBUG:ingredient-parser:Tokenized sentence: ['24', 'fresh', 'basil', 'leaf', 'or', 'dried', 'basil'].
  DEBUG:ingredient-parser:Singularised tokens at indices: [3].
  DEBUG:ingredient-parser:Generating features for tokens.
  DEBUG:ingredient-parser:Sentence token labels: ['QTY', 'B_NAME_TOK', 'I_NAME_TOK', 'I_NAME_TOK', 'NAME_SEP', 'B_NAME_TOK', 'I_NAME_TOK'].

Only enabling logging for foundation foods:

.. code:: python

  >>> import logging, sys
  >>> from ingredient_parser import parse_ingredient
  >>>
  >>> logging.basicConfig(stream=sys.stdout)
  >>> logging.getLogger("ingredient-parser.foundation-foods").setLevel(logging.DEBUG)
  >>>
  >>> parsed = parse_ingredient("24 fresh basil leaves or dried basil", foundation_foods=True)
  DEBUG:ingredient-parser.foundation-foods:Matching FDC ingredient for ingredient name tokens: ['fresh', 'basil', 'leaves']
  DEBUG:ingredient-parser.foundation-foods:Prepared tokens: ['fresh', 'basil', 'leav'].
  DEBUG:ingredient-parser.foundation-foods:Loaded 13318 FDC ingredients.
  DEBUG:ingredient-parser.foundation-foods:Selecting best match from 1 candidates based on preferred FDC datatype.
  DEBUG:ingredient-parser.foundation-foods:Matching FDC ingredient for ingredient name tokens: ['dried', 'basil']
  DEBUG:ingredient-parser.foundation-foods:Prepared tokens: ['dri', 'basil'].
  DEBUG:ingredient-parser.foundation-foods:Selecting best match from 1 candidates based on preferred FDC datatype.

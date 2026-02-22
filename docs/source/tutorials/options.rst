.. _reference-options-index:

Options
=======

The :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>` function has the following optional boolean parameters:

``separate_names``
^^^^^^^^^^^^^^^^^^

Default: **True**

If the ingredient sentence includes multiple alternative ingredient names, return each name separately.

.. topic:: Example

    .. code:: python

        >>> parse_ingredient("2 tbsp olive oil or butter").name
        [
            IngredientText(text='olive oil', confidence=0.990395, starting_index=2),
            IngredientText(text='butter', confidence=0.998547, starting_index=5)
        ]

If disabled, the ``name`` field will be a list containing a single :class:`IngredientText <ingredient_parser.dataclasses.IngredientText>` object.

.. topic:: Example

    .. code:: python

        >>> parse_ingredient("2 tbsp olive oil or butter", separate_names=False).name
        [
            IngredientText(text='olive oil or butter', confidence=0.994275, starting_index=2)
        ]

``discard_isolated_stop_words``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Default: **True**

Discard stop words that appear in isolation within the name, preparation, size, purpose or comment fields.

.. topic:: Example

    .. code:: python

        >>> parse_ingredient("2 tbsp of olive oil").comment
        None

If disabled, then all words from the input sentence are retained in the parsed output.

.. topic:: Example

    .. code:: python

        >>> parse_ingredient("2 tbsp of olive oil", discard_isolated_stop_words=False).comment
        IngredientText(text='of', confidence=0.915292)

``expect_name_in_output``
^^^^^^^^^^^^^^^^^^^^^^^^^

Default: **True**

Sometimes a name isn't identified in the ingredient sentence, often due to the sentence structure being unusual or the sentence contains an ingredient name that is ambiguous.
For these cases, attempt to find the most likely name even if the words making that name are considered more likely to belong to a different field of the :class:`ParsedIngredient <ingredient_parser.dataclasses.ParsedIngredient>` object.

A minimum confidence threshold applies, meaning this does not guarantee a name is identified.

If disabled, when encountering such sentences the name field will be empty.

``string_units``
^^^^^^^^^^^^^^^^

Default: **False**

Units in the :class:`IngredientAmount <ingredient_parser.dataclasses.IngredientAmount>` objects are returned :class:`pint.Unit` objects, which allows for convenient manipulation programmatically.

.. topic:: Example

    .. code:: python

        >>> parse_ingredient("250 g plain flour").amount[0].unit
        <Unit('gram')>

If set to **True**, the :class:`IngredientAmount <ingredient_parser.dataclasses.IngredientAmount>` unit will be the string identified from the sentence.

.. topic:: Example

    .. code:: python

        >>> parse_ingredient("250 g plain flour", string_units=True).amount[0].unit
        'g'

``imperial_units``
^^^^^^^^^^^^^^^^^^

.. deprecated:: v2.5.0

    This keyword argument will be removed in a future version.

    Use the ``volumetric_units_system="imperial"`` for the same functionality.

Default: **False**

Some units have have multiple definitions versions with the same name but representing different quantities, such as fluid ounces, cups, pints, quarts or gallons.

:class:`pint.Unit` objects are assumed to be the US customary version of the unit unless this is set to **True**.

.. topic:: Example

    .. code:: python

        >>> parse_ingredient("2 pints chicken stock").amount[0].unit
        <Unit('pint')>

        >>> parse_ingredient("2 pints chicken stock", imperial_units=True).amount[0].unit
        <Unit('imperial_pint')>

This option has no effect if ``string_units=True``.

``volumetric_units_system``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Default: **us_customary**

Some units have have multiple definitions with the same name but representing different quantities, such as fluid ounces, cups, pints, quarts or gallons.

The following options are available to select between the different systems.

+------------------+-------------------------------------------------------------+
| Options          | Description                                                 |
+==================+=============================================================+
| ``us_customary`` | Uses the US customary definitions for the following units:  |
|                  |                                                             |
|                  | gallon, quart, fluid ounce pint, cup, tablespoon, teaspoon. |
+------------------+-------------------------------------------------------------+
| ``imperial``     | Uses the Imperial definitions for the following units:      |
|                  |                                                             |
|                  | gallon, quart, fluid ounce pint, cup, tablespoon, teaspoon. |
+------------------+-------------------------------------------------------------+
| ``metric``       | Uses metric definitions for the following units:            |
|                  |                                                             |
|                  | cup (250 ml), tablespoon (15 ml), teaspoon (5 ml).          |
+------------------+-------------------------------------------------------------+
| ``australian``   | Uses the Australian definitions for the following units:    |
|                  |                                                             |
|                  | pint (570 ml), tablespoon (20 ml).                          |
|                  |                                                             |
|                  | Uses metric defintions for cup and teaspoon.                |
+------------------+-------------------------------------------------------------+
| ``japanese``     | Uses the Japanese definitions for the following units:      |
|                  |                                                             |
|                  | cup (200 ml).                                               |
+------------------+-------------------------------------------------------------+

This option has no effect if ``string_units=True``.

``foundation_foods``
^^^^^^^^^^^^^^^^^^^^

Default: **False**

`Food Data Central <https://fdc.nal.usda.gov/>`_ is a database of foods and their nutritional properties.
If enabled, the ingredient names are matched to entries in the :abbr:`FDC (Food Data Central)` database and returned as a list of :class:`FoundationFood <ingredient_parser.dataclasses.FoundationFood>` objects in the ``foundation_foods`` field of the :class:`ParsedIngredient <ingredient_parser.dataclasses.ParsedIngredient>` object.
See the :doc:`Foundation Foods </explanation/foundation>` page for more details.

This is disabled by default and the ``foundation_foods`` field is an empty list.

``custom_units``
^^^^^^^^^^^^^^^^

Default: **None**

Custom units can be provided to aid the underlying model in identifying units.
The custom units should be provided as a ``dict`` of plural-singular form pairs, for example

.. code:: python

    my_units = {
        "tablespoons": "tablespoon",
    }

The provided units should not start with a capital letter (the capitalized version of the words are generated automatically), but may include capital letters in any other position.

The provided units should comprise a single word for both the plural and singular forms.
Units containing spaces are not currently supported.


.. topic:: Example

    .. code:: python

        >>> parse_ingredient("1 barrel sausages").amount[0].unit
        ''

        >>> parse_ingredient("1 barrel sausages", custom_units={"barrels": "barrel"}).amount[0].unit
        <Unit('barrel')>

.. important::

  Using a custom units dictionary does not guarantee that the word will be identified as a unit.
  The underlying model uses a number of features of each word and the surround context to determine the appropriate label.
  There may be cases where the model weight determine a different label is more appropriate for a word, despite the word being in the custom units dictionary.

  That being said, adding words to this dictionary will significantly increase the likelihood of a word being identified as a unit.

.. tip::

  By default, :class:`pint.Unit` objects are returned for units if there is a match in the Pint units registry.
  If there is any chance that a custom unit could be interpreted in a way that matches an entry in the Pint units registry, the results may be unexpected.

  You may wish to consider using the ``string_units=True`` option to prevent this.

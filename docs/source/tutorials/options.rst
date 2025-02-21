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

``foundation_foods``
^^^^^^^^^^^^^^^^^^^^

Default: **False**

Foundation foods are the core or fundamental part of an ingredient name, without any other words like descriptive adjectives or brand names.
If enabled, the foundation foods are extracted from the ingredient name and returned as a list of :class:`FoundationFood <ingredient_parser.dataclasses.FoundationFood>` objects in the ``foundation_foods`` field of the :class:`ParsedIngredient <ingredient_parser.dataclasses.ParsedIngredient>` object.
See the :doc:`Foundation Foods </explanation/foundation>` page for more details.

This is disabled by default and the ``foundation_foods`` field is an empty list.

Convert between units
=====================

Where possible, :class:`IngredientAmount <ingredient_parser.dataclass.IngredientAmount>` units are returned as a :class:`pint.Unit`. This allows easy programmatic conversion between different units. To perform unit conversion, a :class:`pint.Quantity` object should be created from the :class:`IngredientAmount <ingredient_parser.dataclasses.IngredientAmount>` quantity and unit.

.. code:: python

    >>> amount = parse_ingredient("2 cups orange juice").amount[0]
    >>> amount
    IngredientAmount(quantity=Fraction(2, 1),
                 quantity_max=Fraction(2, 1),
                 unit=<Unit('cup')>,
                 text='2 cups',
                 confidence=0.999936,
                 starting_index=0,
                 APPROXIMATE=False,
                 SINGULAR=False,
                 RANGE=False,
                 MULTIPLIER=False,
                 PREPARED_INGREDIENT=False)
    >>> q = amount.quantity * amount.unit
    >>> q
    <Quantity(2, 'cup')>

With the :class:`pint.Quantity` object, the units can be converted using the ``to()`` function.

.. code:: python

    >>> q
    <Quantity(2, 'cup')>
    >>> q.to("ml")
    <Quantity(11829411824999997/25000000000000, 'milliliter')>
    >>> float(q.to("ml")magnitude)
    473.1764729999999

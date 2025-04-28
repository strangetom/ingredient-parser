Convert between units
=====================

Where possible, :class:`IngredientAmount <ingredient_parser.dataclasses.IngredientAmount>` units are returned as a :class:`pint.Unit`.
This allows easy programmatic conversion between different units.

.. admonition:: Prerequisites

    Programmatic conversion of units is only possible if none of the ``quantity``, ``quantity_max`` and ``unit`` fields are ``str``.

The ``convert_to`` function of :class:`IngredientAmount <ingredient_parser.dataclasses.IngredientAmount>` accepts the units to convert to and, optionally, a density if the conversion is between mass and volume.

.. code:: python

    >>> amount = parse_ingredient("1.2 kg lamb shank").amount[0]
    >>> amount.convert_to("lbs")
    IngredientAmount(quantity=Fraction(66138678655463271, 25000000000000000),
        quantity_max=Fraction(66138678655463271, 25000000000000000),
        unit=<Unit('pound')>,
        text='2.65 pound',
        confidence=0.99986,
        starting_index=0,
        APPROXIMATE=False,
        SINGULAR=False,
        RANGE=False,
        MULTIPLIER=False,
        PREPARED_INGREDIENT=False
    )

The ``unit`` parameter of ``convert_to`` must a unit recognised by Pint.

:class:`CompositeIngredientAmount <ingredient_parser.dataclasses.CompositeIngredientAmount>` also supports unit conversion.
In this case, the ``convert_to`` function return a :class:`pint.Quantity` object which is the combined quantity converted to the given units.

.. code:: python

    >>> amount = parse_ingredient("1lb 2 oz lamb shank").amount[0]
    >>> amount.convert_to("kg")
    <Quantity(255145708125000060785923700000001/500000000000000000000000000000000, 'kilogram')>

The ``convert_to`` function of :class:`CompositeIngredientAmount <ingredient_parser.dataclasses.CompositeIngredientAmount>` is the same as doing

.. code:: python

    >>> CompositeIngredientAmount.combined().to(unit)

however it also support conversion between mass and volume as described below.

Converting between mass and volume
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is quite common for recipes that use US customary units to give amounts in units of volume for ingredients, such as flour and sugar, where other recipes more commonly use units of mass.
Conversion between these units is possible, but requires a density value to enable the conversion.

The density value can be provided as an optional argument to ``convert_to`` and must be given as a :class:`pint.Quantity`.
The default value is the density of water: 1000 kg/m\ :sup:`3`.

.. code:: python

    >>> amount = parse_ingredient("1 cup water").amount[0]
    >>> # Using default density value
    >>> amount.convert_to("g")
    IngredientAmount(quantity=236.58823649999997,
        quantity_max=236.58823649999997,
        unit=<Unit('gram')>,
        text='236.588 gram',
        confidence=0.999943,
        starting_index=0,
        APPROXIMATE=False,
        SINGULAR=False,
        RANGE=False,
        MULTIPLIER=False,
        PREPARED_INGREDIENT=False
    )

.. code:: python

    >>> amount = parse_ingredient("2 cups all purpose flour").amount[0]
    >>> # Using custom density value: 1 cup flour = 120 g
    >>> amount.convert_to("g", density=120 * UREG("g/cup"))
    IngredientAmount(quantity=240.0,
        quantity_max=240.0,
        unit=<Unit('gram')>,
        text='240 gram',
        confidence=0.999949,
        starting_index=0,
        APPROXIMATE=False,
        SINGULAR=False,
        RANGE=False,
        MULTIPLIER=False,
        PREPARED_INGREDIENT=False
    )

.. attention::

    When converting between mass and volume, the quantity values are convert to ``float``.

    This is a result of how Pint handles the conversion.

Resources such as King Arthur Baking's `Ingredient Weight Chart <https://www.kingarthurbaking.com/learn/ingredient-weight-chart>`_ are helpful in providing the densities for various ingredients commonly used in baking.

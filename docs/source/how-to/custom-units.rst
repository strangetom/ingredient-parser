.. _reference-how-to-custom-units:

Customize units
===============

There may be circumstances where this library does not correctly identify a word as a unit.
This is likely to be because the model has been trained on a dataset that does not exhaustively include every possible unit that can be used in the culinary domain.
To aid with this, the library includes a list of common units that are used to aid in identifying units, but this too is not exhaustive.

To help with situations where there are known units that the library should identify, a custom units dictionary can be provided.

The custom units dictionary should comply with the following rules:

#. The dictionary should contain pairs of plural - singular forms of each custom unit.
#. The plural form should be the dict key, the singular form should be the dict value.
#. If a custom unit does not have a plural form, the dict key should be set to the singular form.
#. The custom units should not start with a capital letter, but may include capital letters at any other position in the word.

   This is because the capitalized form is generated automatically.

.. tip::

    This can be useful when trying to parse non-English language ingredient sentences.

    Technically, they are not supported but the library often does a reasonable job. The exception is with units, where the actual word itself is very important.


Example
^^^^^^^

.. code:: python

    # Custom units, {plural: singular, ...}
    >>> my_units = {
        "barrels": "barrel",
        "drums": "drum",
        "shoes": "shoe",
    }

    # Without the custom dictionary
    >>> p = parse_ingredient("2 barrels sausages")
    >>> p.amount[0].unit
    ''

    # With the custom dictionary
    >>> p = parse_ingredient("2 barrels sausages", custom_units=my_units)
    >>> p.amount[0].unit
    <Unit('barrel')>  # In this case, matches an entry in the Pint units registry

    # Capitalized versions are automatically generated
    >>> p = parse_ingredient("1 Shoe red wine", custom_units=my_units)
    >>> p.amount[0].unit
    Shoe

#!/usr/bin/env python3

import re

from ._constants import FLATTENED_UNITS_LIST, STRING_NUMBERS

# Regex pattern for fraction parts.
# Matches 0+ numbers followed by 0+ white space characters followed by a number then
# a forward slash then another number.
FRACTION_PARTS_PATTERN = re.compile(r"(\d*\s*\d/\d+)")

# Regex pattern for checking if token starts with a capital letter.
CAPITALISED_PATTERN = re.compile(r"^[A-Z]")

# Regex pattern for finding quantity and units without space between them.
# Add additional strings to units set that aren't necessarily units, but we want to
# treat them like units for the purposes of splitting quantities from units.
units_list = FLATTENED_UNITS_LIST | {"in", "x"}
# The negative lookahead at the end of QUANTITY_UNITS_PATTERN is there specifically
# to handle units like 'c' where it could be the start of another word. We have to
# check that the next character after the unit is *not* another letter in order
# to match.
# "x" is excluded from the possible following characters to allow constructs
# like 2cmx2cm.
QUANTITY_UNITS_PATTERN = re.compile(rf"(\d)\-?({'|'.join(units_list)})(?![a-wyzA-WYZ])")
UNITS_QUANTITY_PATTERN = re.compile(rf"({'|'.join(units_list)})(\d)")
UNITS_HYPHEN_QUANTITY_PATTERN = re.compile(rf"({'|'.join(units_list)})\-(\d)")
STRING_QUANTITY_HYPHEN_PATTERN = re.compile(
    rf"""
    \b({'|'.join(STRING_NUMBERS.keys())})\b  # Capture string number
    \-                                       # Followed by hyphen
    \b({'|'.join(units_list)})\b             # Followed by unit
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Regex pattern for matching a range in string format e.g. 1 to 2, 8.5 to 12, 4 or 5.
# Assumes fractions have been converted to the #1$2 form.
# Allows the range to include a hyphen, which are captured in separate groups.
# Captures the two number in the range in separate capture groups.
# If a number starts with a zero, it must be followed by decimal point to be matched
STRING_RANGE_PATTERN = re.compile(
    r"""
    (0\.[0-9]|[1-9][\d\.]*?|\d*\#\d+\$\d+)  # Capture number
    \s*                                     # Optional space
    (\-)?                                   # Optional hyphen
    \s*                                     # Optional space
    (to|or)                                 # Match to or or
    \s*                                     # Optional space
    (\-)*                                   # Optional hyphen
    \s*                                     # Optional space
    (                                       # Capture next two groups together
    (0\.[0-9]+|[1-9][\d\.]*?|\d*\#\d+\$\d+) # Capture number
    (\-)?                                   # Optional hyphen
    )
    """,
    re.VERBOSE,
)

# Regex pattern to match quantities split by "and" e.g. 1 and 1/2.
# Capture the whole match, and the quantites before and after the "and".
FRACTION_SPLIT_AND_PATTERN = re.compile(r"((\d+)\sand\s(\d/\d+))")

# Regex pattern to match ranges where the unit appears after both quantities e.g.
# 100 g - 200 g. This assumes the quantites and units have already been seperated
# by a single space and that all number are decimals.
# This regex matches:
#   <quantity> <unit> - <quantity> <unit>
#   <quantity> <unit> to <quantity> <unit>
#   <quantity> <unit> or <quantity> <unit>
# returning the full match and each quantity and unit as capture groups.
DUPE_UNIT_RANGES_PATTERN = re.compile(
    r"""
    (
        ([\d\.]+|\d*\#\d+\$\d+)  # Capture decimal number or fraction
        \s                       # Space
        ([a-zA-Z]+)              # Capture text string (possible unit)
        \s*                      # Space
        (?:\-|to|or)             # Hyphen, 'to' or 'or'
        \s*                      # Space
        ([\d\.]+|\d*\#\d+\$\d+)  # Capture decimal number or fraction
        \s                       # Space
        ([a-zA-Z]+)              # Capture text string (possible unit)
    )
    """,
    re.I | re.VERBOSE,
)

# Regex pattern to match a decimal number followed by an "x" followed by a space
# e.g. 0.5 x, 1 x, 2 x. The number is captured in a capture group.
QUANTITY_X_PATTERN = re.compile(
    r"""
    ([\d\.]+|\d*\#\d+\$\d+)  # Capture decimal number or fraction
    \s                       # Space
    [xX]                     # Character 'x' or 'X'
    \s*                      # Optional space
    """,
    re.VERBOSE,
)

# Regex pattern to match a range that has spaces between the numbers and hyphen
# e.g. 0.5 - 1. The numbers are captured in capture groups.
# Allow the second number to start with # to catch fractions
# e.g. #1$4 - #1$2.
EXPANDED_RANGE = re.compile(r"(\d)\s*\-\s*([\d\#])")

LOWERCASE_PATTERN = re.compile(r"[a-z]")
UPPERCASE_PATTERN = re.compile(r"[A-Z]")
DIGIT_PATTERN = re.compile(r"[0-9]")

# Regex pattern to match a fraction token.
# This is a token for a fraction where the forward slash has been replaced by $ and
# any space between the whole part and fraction part has been replaced by #
# e.g. #1$2 for 1/2, or 1#1$3 for 1 1/3
FRACTION_TOKEN_PATTERN = re.compile(r"^\d*\#\d+\$\d+$")

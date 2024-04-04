#!/usr/bin/env python3

import re

# Regex pattern for fraction parts.
# Matches 0+ numbers followed by 0+ white space characters followed by a number then
# a forward slash then another number.
FRACTION_PARTS_PATTERN = re.compile(r"(\d*\s*\d/\d+)")

# Regex pattern for checking if token starts with a capital letter.
CAPITALISED_PATTERN = re.compile(r"^[A-Z]")

# Regex pattern for finding quantity and units without space between them.
# Assumes the quantity is always a number and the units always a letter.
QUANTITY_UNITS_PATTERN = re.compile(r"(\d)\-?([a-zA-Z])")
UNITS_QUANTITY_PATTERN = re.compile(r"([a-zA-Z])(\d)")
UNITS_HYPHEN_QUANTITY_PATTERN = re.compile(r"([a-zA-Z])\-(\d)")

# Regex pattern for matching a numeric range e.g. 1-2, 2-3.
RANGE_PATTERN = re.compile(r"\d+\s*[\-]\d+")

# Regex pattern for matching a range in string format e.g. 1 to 2, 8.5 to 12, 4 or 5.
# Assumes fake fractions and unicode fraction have already been replaced.
# Allows the range to include a hyphen, which are captured in separate groups.
# Captures the two number in the range in separate capture groups.
STRING_RANGE_PATTERN = re.compile(
    r"([\d\.]+)\s*(\-)?\s*(to|or)\s*(\-)*\s*([\d\.]+(\-)?)"
)

# Regex pattern to match quantities split by "and" e.g. 1 and 1/2.
# Capture the whole match, and the quantites before and after the "and".
FRACTION_SPLIT_AND_PATTERN = re.compile(r"((\d+)\sand\s(\d/\d+))")

# Regex pattern to match ranges where the unit appears after both quantities e.g.
# 100 g - 200 g. This assumes the quantites and units have already been seperated
# by a single space and that all number are decimals.
# This regex matches: <quantity> <unit> - <quantity> <unit>, returning
# the full match and each quantity and unit as capture groups.
DUPE_UNIT_RANGES_PATTERN = re.compile(
    r"(([\d\.]+)\s([a-zA-Z]+)\s\-\s([\d\.]+)\s([a-zA-Z]+))", re.I
)

# Regex pattern to match a decimal number followed by an "x" followed by a space
# e.g. 0.5 x, 1 x, 2 x. The number is captured in a capture group.
QUANTITY_X_PATTERN = re.compile(r"([\d\.]+)\s[xX]\s*")

# Regex pattern to match a range that has spaces between the numbers and hyphen
# e.g. 0.5 - 1. The numbers are captured in capture groups.
EXPANDED_RANGE = re.compile(r"(\d)\s*\-\s*(\d)")

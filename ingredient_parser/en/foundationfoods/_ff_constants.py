#!/usr/bin/env python3

from ...dataclasses import FoundationFood

# Dict of ingredient name tokens that bypass the usual foundation food matching process.
# We do this because the embedding distance approach sometime gives poor results when
# the name we're trying to match only has one token.
# The tokens in the dict keys are stemmed.
FOUNDATION_FOOD_OVERRIDES: dict[tuple[str, ...], FoundationFood] = {
    ("salt",): FoundationFood(
        "Salt, table, iodized", 1, 746775, "Spices and Herbs", "foundation_food", 0
    ),
    (
        "sea",
        "salt",
    ): FoundationFood(
        "Salt, table, iodized", 1, 746775, "Spices and Herbs", "foundation_food", 0
    ),
    ("egg",): FoundationFood(
        "Eggs, Grade A, Large, egg whole",
        1,
        748967,
        "Dairy and Egg Products",
        "foundation_food",
        0,
    ),
    ("butter",): FoundationFood(
        "Butter, stick, unsalted",
        1,
        789828,
        "Dairy and Egg Products",
        "foundation_food",
        0,
    ),
    ("garlic",): FoundationFood(
        "Garlic, raw",
        1,
        1104647,
        "Vegetables and Vegetable Products",
        "foundation_food",
        0,
    ),
    ("mayonnais",): FoundationFood(
        "Mayonnaise, regular",
        1,
        2710204,
        "Mayonnaise",
        "survey_fndds_food",
        0,
    ),
    ("all-purpos", "flour"): FoundationFood(
        "Flour, wheat, all-purpose, unenriched, unbleached",
        1,
        790018,
        "Cereal Grains and Pasta",
        "foundation_food",
        0,
    ),
    ("all", "purpos", "flour"): FoundationFood(
        "Flour, wheat, all-purpose, unenriched, unbleached",
        1,
        790018,
        "Cereal Grains and Pasta",
        "foundation_food",
        0,
    ),
}

# Verb stems, the presence of which indicates the food is not raw and therefore should
# not be biased towards a raw food.
NON_RAW_FOOD_VERB_STEMS = {
    "age",
    "bake",
    "black",
    "blanch",
    "boil",
    "brais",
    "brew",
    "broil",
    "butter",
    "can",
    "cook",
    "crisp",
    "cultur",
    "cure",
    "decaffein",
    "dehydr",
    "devil",
    "distil",
    "dri",
    "ferment",
    "flavor",
    "fortifi",
    "fresh",
    "fri",
    "grill",
    "ground",
    "heat",
    "hull",
    "microwav",
    "parboil",
    "pasteur",
    "pickl",
    "poach",
    "precook",
    "prepar",
    "preserv",
    "powder",
    "reconstitut",
    "refin",
    "refri",
    "reheat",
    "rehydr",
    "render",
    "roast",
    "simmer",
    "smoke",
    "soak",
    "spice",
    "steam",
    "stew",
    "toast",
    "unbak",
    "unsalt",
}
# Also include "raw" so we don't add if again if already present
NON_RAW_FOOD_VERB_STEMS.add("raw")

# Tokens that indicated following words are negated.
# NS = not specified.
NEGATION_TOKENS = {"no", "not", "without", "NS"}

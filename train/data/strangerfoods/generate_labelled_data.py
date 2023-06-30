#!/usr/bin/env python3

import argparse
import csv
import glob
import json
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Features:
    """Dataclass to store setences features"""

    name: str
    quantity: str
    unit: str
    comment: str


def load_recipes(path: str) -> List[Dict[str, Any]]:
    """Load recipes from json files

    Parameters
    ----------
    path : str
        Path to json files
        e.g. ./json/*.json

    Returns
    -------
    list
        List of dicts
    """
    jsonfiles = glob.glob(f"{path}/*.json")

    recipes = []
    for file in jsonfiles:
        with open(file, "r") as f:
            recipes.append(json.load(f))
    return recipes


def write_csv(
    ingredient_rows: List[str], feature_rows: List[Features], output: str
) -> None:
    """Generate csv file of ingredients and features

    Parameters
    ----------
    ingredient_rows : List[str]
        List of ingredients as sentences
    feature_rows : List[Features]
        List of ingredient features as a Features dataclass
    output : str
        csv file to write
    """
    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["input", "name", "quantity", "unit", "comment"])
        for ingredient, features in zip(ingredient_rows, feature_rows):
            writer.writerow(
                [
                    ingredient,
                    features.name,
                    features.quantity,
                    features.unit,
                    features.comment,
                ]
            )


def generate_rows(recipes: List[Dict[str, Any]]) -> tuple[List[str], List[Features]]:
    """Generate rows of data for writing to csv

    Parameters
    ----------
    recipes : List[Dict[str, Any]]
        List of dictionaries of recipe data

    Returns
    -------
    tuple[List[str], List[Features]]
        (list of ingredient sentences, list of Feature objects)

    """
    ingredients_list = []
    features_list = []

    for recipe in recipes:
        for ingredient in recipe["ingredients"]:
            if isinstance(ingredient, dict):
                ingredrient_string, features = extract_features(ingredient)
                ingredients_list.append(ingredrient_string)
                features_list.append(features)
            elif isinstance(ingredient, list):
                for ingred in ingredient[1:]:  # skip first row
                    ingredrient_string, features = extract_features(ingred)
                    ingredients_list.append(ingredrient_string)
                    features_list.append(features)

    return ingredients_list, features_list


def extract_features(ingredient: Dict[str, Any]) -> tuple[str, Features]:
    """Extract features from ingredient dictionary

    Parameters
    ----------
    ingredient : Dict[str, Any]
        Dictionary of ingredient information

    Returns
    -------
    tuple[str, Features]
        First element of tuple is the ingredient sentence
        Second element of the tuple of the ingredient features, as a Features tuple
    """
    quantity = ingredient["quantity"]
    unit = ingredient["unit"]
    name = ingredient["name"]
    comment = ingredient["comment"]

    if comment == "":
        string = f"{quantity} {unit} {name}".strip()
    else:
        string = f"{quantity} {unit} {name}, {comment}".strip()

    # Strip any duplicate spaces
    string = " ".join(string.split())

    return string, Features(name, quantity, unit, comment)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate recipe ingredient parser labelled data in csv form"
    )
    parser.add_argument(
        "-p",
        "--path",
        default="../Recipes/resources/json",
        help="Path to recipe json files",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="train/data/strangerfoods/sf_labelled_data.csv",
        help="Output csv file for labelled data",
    )
    args = parser.parse_args()

    recipes = load_recipes(args.path)
    ingredients, features = generate_rows(recipes)
    write_csv(ingredients, features, args.output)

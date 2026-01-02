#!/usr/bin/env python3

import argparse
import csv
import datetime
import gzip
from dataclasses import dataclass


@dataclass
class FDCIngredient:
    fdc_id: str
    data_type: str
    description: str
    publication_date: datetime.date
    category: str


def get_category_map(food_category_csv: str, wweia_food_category_csv: str) -> dict:
    """Create mapping of category ID to category name.

    Parameters
    ----------
    food_category_csv : str
        Path to food_category csv, exported from Food Data Central
    wweia_food_category_csv : str
        Path to wweia_food_category csv, exported from Food Data Central

    Returns
    -------
    dict
        Dict of category ID to category name mapping.
    """
    category_map = {}
    with open(food_category_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category_map[row["id"]] = row["description"]
    with open(wweia_food_category_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category_map[row["wweia_food_category"]] = row[
                "wweia_food_category_description"
            ]

    return category_map


def select_preferred_entry(
    new: FDCIngredient, existing: FDCIngredient, allowed_datasets: list[str]
) -> FDCIngredient:
    """Given two FDCIngredient objects, return the preferred one.

    If the data_type is the same, return the newest.
    If the data_type is different, the order of preference is:
        foundation_food, sr_legacy_food, survery_fndds_food

    Parameters
    ----------
    new : FDCIngredient
        New object to check
    existing : FDCIngredient
        Existing object to check
    allowed_datasets : list[str]
        List of allowed datasets to select ingredients from

    Returns
    -------
    FDCIngredient
        Preferred object to keep
    """
    # If same data_type, return most recent
    if new.data_type == existing.data_type:
        if new.publication_date > existing.publication_date:
            return new
        else:
            return existing

    # If different data_type, return preferred
    else:
        for data_type in allowed_datasets:
            if new.data_type == data_type:
                return new
            elif existing.data_type == data_type:
                return existing

    return new


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate CSV for foundation food matching."
    )
    parser.add_argument(
        "--food",
        help="Path to food.csv exporting from Food Data Central.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--food-categories",
        help="Path to food_category.csv exporting from Food Data Central.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--wweia-food-categories",
        help="Path to wweia_food_category.csv exporting from Food Data Central.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--datasets",
        help="Datasets to include in CSV, in order of preference.",
        choices=[
            "foundation_food",
            "sr_legacy_food",
            "survey_fndds_food",
            "branded_food",
        ],
        nargs="*",
        default=["foundation_food"],
    )
    parser.add_argument(
        "--output",
        help="Path to save gzipped csv file to.",
        type=str,
        default="ingredient_parser/en/data/fdc_ingredients.csv.gz",
    )
    args = parser.parse_args()

    category_map = get_category_map(args.food_categories, args.wweia_food_categories)

    food = {}
    with open(args.food, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["data_type"] not in args.datasets:
                continue

            if (
                "Includes foods for USDA's Food Distribution Program"
                in row["description"]
            ):
                continue

            category = category_map[row["food_category_id"]]
            # Discard baby/infant formula and baby food entries
            if "baby" in category.lower() or "formula" in category.lower():
                continue

            # Discard whole meals or dishes
            if "dishes" in category.lower() or "sandwich" in category.lower():
                continue
            if category in {"Restaurant Foods", "Pizza", "Burgers"}:
                continue

            fdc = FDCIngredient(
                fdc_id=row["fdc_id"],
                data_type=row["data_type"],
                description=row["description"],
                publication_date=datetime.date.fromisoformat(row["publication_date"]),
                category=category,
            )

            # If there are duplicate descriptions, only keep the preferred one
            if fdc.description in food:
                preferred = select_preferred_entry(
                    fdc, food[fdc.description], args.datasets
                )
                food[fdc.description] = preferred
            else:
                food[fdc.description] = fdc

    with gzip.open(args.output, "wt") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["fdc_id", "data_type", "description", "category"],  # type: ignore
        )
        writer.writeheader()
        for fdc in food.values():
            writer.writerow(
                {
                    "fdc_id": fdc.fdc_id,
                    "data_type": fdc.data_type,
                    "description": fdc.description,
                    "category": fdc.category,
                }
            )

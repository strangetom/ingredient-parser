#!/usr/bin/env python3

import glob
import json
import csv
import argparse

def load_recipes(path):
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
    jsonfiles = glob.glob(f'{path}/*.json')

    recipes = []
    for file in jsonfiles:
        with open(file, 'r') as f:
            recipes.append(json.load(f))                   
    return recipes

def generate_csv(recipes, output):
    """Generate csv file of ingredients
    
    Parameters
    ----------
    recipes : list[dict]
        List of dictionaries of recipe data
    """
    with open(output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Input', 'quantity', 'unit', 'item', 'comment'])
        for recipe in recipes:
            for ingredient in recipe['ingredients']:
                rows = generate_csv_row(ingredient)
                for row in rows:
                    writer.writerow(row)


def generate_csv_row(ingredient):
    """Generate csv row from ingredient dictionary
    
    Parameters
    ----------
    ingredient : dict or list
        Dictionary or list of dictionaries containing parsed ingredient
    """
    if isinstance(ingredient, dict):
        quantity = ingredient['quantity']
        unit = ingredient['unit']
        item = ingredient['ingredient']

        if ingredient['additional'] == "":
            string = f"{quantity} {unit} {item}".strip()
            return [(' '.join(string.split()), quantity, unit, item, '')]
        else:
            string = f"{quantity} {unit} {item}, {ingredient['additional']}".strip()
            return [(' '.join(string.split()), quantity, unit, item, ingredient['additional'])]
    elif isinstance(ingredient, list):
        rows = []
        for ingred in ingredient[1:]: # skip first row
            quantity = ingred['quantity']
            unit = ingred['unit']
            item = ingred['ingredient']

            if ingred['additional'] == "":
                string = f"{quantity} {unit} {item}".strip()
                rows.append( (' '.join(string.split()), quantity, unit, item, '') )
            else:
                string = f"{quantity} {unit} {item}, {ingred['additional']}".strip()
                rows.append( (' '.join(string.split()), quantity, unit, item, ingred['additional']) )
        return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate recipe ingredient parser training data')
    parser.add_argument('-p', '--path', default='/home/tom/Recipes/resources/json', help='Path to recipe json files')
    parser.add_argument('-o', '--output', default='training_data.csv', help='Output csv file')
    args = parser.parse_args()

    recipes = load_recipes(args.path)
    generate_csv(recipes, args.output)
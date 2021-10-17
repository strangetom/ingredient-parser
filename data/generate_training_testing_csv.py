#!/usr/bin/env python3

import glob
import json
import csv
import argparse
from collections import namedtuple

from sklearn.model_selection import train_test_split

# Features tuple
Features = namedtuple('Features', ['quantity', 'unit', 'item', 'comment'])

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

def write_csv(ingredient_rows, feature_rows, output):
    """Generate csv file of ingredients and features
    
    Parameters
    ----------
    ingredient_rows : list[str]
        List of ingredients as sentences
    feature_rows : list[Features]
        List of ingredient features as a Features tuple
    output : str
        csv file to write
    """
    with open(output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Input', 'quantity', 'unit', 'item', 'comment'])
        for ingredient, features in zip(ingredient_rows, feature_rows):
            writer.writerow([ingredient, *features])

def generate_rows(recipes):
    """Generate rows of data for writing to csv
    
    Parameters
    ----------
    recipes : list[dict]
        List of dictionaries of recipe data
    
    Returns
    -------
    tuple
        (list of ingredient sentences, list of Feature tuples)
    
    """
    ingredients_list = []
    features_list = []

    for recipe in recipes:
        for ingredient in recipe['ingredients']:
            if isinstance(ingredient, dict):
                ingredrient_string, features = extract_features(ingredient)
                ingredients_list.append(ingredrient_string)
                features_list.append(features)
            elif isinstance(ingredient, list):
                for ingred in ingredient[1:]: # skip first row
                    ingredrient_string, features = extract_features(ingred)
                    ingredients_list.append(ingredrient_string)
                    features_list.append(features)

    return ingredients_list, features_list

def extract_features(ingredient):
    """Extract features from ingredient dictionary
    
    Parameters
    ----------
    ingredient : dict
        Dictionary of ingredient information
    
    Returns
    -------
    tuple(str, Features)
        First element of tuple is the ingredient sentence
        Second element of the tuple of the ingredient features, as a Features tuple
    """
    quantity = ingredient['quantity']
    unit = ingredient['unit']
    item = ingredient['ingredient']
    additional = ingredient['additional']

    if additional == '':
        string = f"{quantity} {unit} {item}".strip()
    else:
        string = f"{quantity} {unit} {item}, {ingredient['additional']}".strip()
    
    return ' '.join(string.split()), Features(quantity, unit, item, additional)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate recipe ingredient parser training and testing data in csv form')
    parser.add_argument('-p', '--path', default='~/Recipes/resources/json', help='Path to recipe json files')
    parser.add_argument('-t', '--train_output', default='training_data.csv', help='Output csv file for training data')
    parser.add_argument('-v', '--test_output', default='testing_data.csv', help='Output csv file for testing data')
    parser.add_argument('-f', '--fraction', default=0.25, type=float, help='Fraction of data to be used for testing')
    args = parser.parse_args()

    recipes = load_recipes(args.path)
    ingredients, features = generate_rows(recipes)
    X_train, X_test, y_train, y_test = train_test_split(ingredients, features, test_size=args.fraction)
    write_csv(X_train, y_train, args.train_output)
    write_csv(X_test, y_test, args.test_output)
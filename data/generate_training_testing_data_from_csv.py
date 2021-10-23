#!/usr/bin/env python3

import argparse
import csv

from sklearn.model_selection import train_test_split
from nltk import pos_tag
from nltk.tokenize import word_tokenize

def load_csv(csv_filename):
    """Load csv file generated py ```generate_training_testing_csv.py``` and parse contents into ingredients and labels lists
    
    Parameters
    ----------
    csv_filename : str
        Name of csv file
    
    Returns
    -------
    list[str]
        List of ingredient strings
    list[dict]
        List of dictionaries, each dictionary the ingredient labels
    """
    labels, ingredients = [], []
    with open(csv_filename, 'r') as f:
        reader = csv.reader(f)
        next(reader) # skip first row
        for row in reader:
            ingredients.append(row[0])
            labels.append({'quantity': row[1].strip(), 
                             'unit': row[2].strip(), 
                             'item': row[3].strip(), 
                             'comment': row[4].strip()})
    return ingredients, labels

def create_crf(crf_filename, ingredients, labels):
    """Create a .crf file containing CRF++ formatted data.
    
    CRF++ expects files formatted in a particular way.
    Each row contains a token, its labels and its label, seperated by whitespace (tabs or spaces), e.g.
        token label_1 label_2 label
    There can an arbitrary number of labels and they should be arrange in order of importances.
    There *must* be the same number of labels for each token.
    
    Tokens are grouped in sentences by seperating sentences by a blank line.
    
    The following labels are written by this scripts:
    1. Part of speech
        Using nltk's pos_tagger to get the part of speech for each token
    2. Position in sentence
        Identified by In where n is an integer, starting from 1
    
    The labels for each token are set according BIO tagging.
    The first time a token with a given label is come across, it gets a B-* tag (B for beginning)
    Any consecutive tokens with the same label get a I-* tag (I for inside)
    Any tokens without a label get an OTHER tag (O for OTHER)
    
    Parameters
    ----------
    crf_filename : str
        Name of .crf file to write data to.
    ingredients : list[str]
        List of labels for each label dict
    labels : list[dict]
        List of dicts of labels for each label
    """
    with open(crf_filename, 'w') as f:
        for ingredient, label in zip(ingredients, labels):
            tokens = word_tokenize(ingredient)

            prev_tag = 'OTHER'
            for i, (token, pos) in enumerate(pos_tag(tokens)):
                if token in label['quantity']:
                    if prev_tag != 'B-QTY' and prev_tag != 'I-QTY':
                        tag = 'B-QTY'
                        prev_tag = 'B-QTY'
                    else:
                        tag = 'I-QTY'
                        prev_tag = 'I-QTY'
                elif token in label['unit']:
                    if prev_tag != 'B-UNIT' and prev_tag != 'I-UNIT':
                        tag = 'B-UNIT'
                        prev_tag = 'B-UNIT'
                    else:
                        tag = 'I-UNIT'
                        prev_tag = 'I-UNIT'
                elif token in label['item']:
                    if prev_tag != 'B-ITEM' and prev_tag != 'I-ITEM':
                        tag = 'B-ITEM'
                        prev_tag = 'B-ITEM'
                    else:
                        tag = 'I-ITEM'
                        prev_tag = 'I-ITEM'
                elif token in label['comment']:
                    if prev_tag != 'B-COMMENT' and prev_tag != 'I-COMMENT':
                        tag = 'B-COMMENT'
                        prev_tag = 'B-COMMENT'
                    else:
                        tag = 'I-COMMENT'
                        prev_tag = 'I-COMMENT'
                else:
                    tag = 'OTHER'
                    prev_tag = 'OTHER'

                f.write(f'{token}\t{pos}\tI{i+1}\t{tag}\n')
            f.write('\n')
 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate CRF++ compatible training and testing data files from csv')
    parser.add_argument('-i', '--input', help='Path to input csv file')
    parser.add_argument('-o', '--train', help='Path to training output crf file')
    parser.add_argument('-t', '--test', help='Path to testing output crf file')
    parser.add_argument('-s', '--split', default=0.25, type=float, help='Fraction of data to be used for testing')
    args = parser.parse_args()

    ingredients, labels = load_csv(args.input)
    ingredients_train, ingredients_test, labels_train, labels_test = train_test_split(ingredients, labels, test_size=args.split)
    
    create_crf(args.train, ingredients_train, labels_train)
    create_crf(args.test, ingredients_test, labels_test)
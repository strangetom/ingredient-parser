#!/usr/bin/env python3

import argparse
import csv
from nltk import pos_tag
from nltk.tokenize import word_tokenize

def load_csv(csv_filename):
    """Load csv file generated py ```generate_training_testing_csv.py``` and parse contents into lst
    
    Parameters
    ----------
    csv_filename : str
        Name of csv file
    
    Returns
    -------
    list[dict]
        List of dictionaries, each dictionary contains a row from the csv
    """
    data = []
    with open(csv_filename, 'r') as f:
        reader = csv.reader(f)
        next(reader) # skip first row
        for row in reader:
            data.append( {'string': row[0], 
                          'quantity': row[1].split(), 
                          'unit': row[2].split(), 
                          'item': row[3].split(), 
                          'comment': row[4].split()})
    return data

def create_crf(crf_filename, data):
    """Create a .crf file containing CRF++ formatted data.

    CRF++ expects files formatted in a particular way.
    Each row contains a token, its features and its label, seperated by whitespace (tabs or spaces), e.g.
        token feature_1 feature_2 label
    There can an arbitrary number of features and they should be arrange in order of importances.
    There *must* be the same number of features for each token.

    Tokens are grouped in sentences by seperating sentences by a blank line.

    The following features are written by this scripts:
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
    data : list[dict]
        Output from load_csv function
    """
    with open(crf_filename, 'w') as f:
        for ingredient in data:
            tokens = word_tokenize(ingredient['string'])

            prev_tag = 'OTHER'
            for i, (token, pos) in enumerate(pos_tag(tokens)):
                if token in ingredient['quantity']:
                    if prev_tag != 'B-QTY' and prev_tag != 'I-QTY':
                        tag = 'B-QTY'
                        prev_tag = 'B-QTY'
                    else:
                        tag = 'I-QTY'
                        prev_tag = 'I-QTY'
                elif token in ingredient['unit']:
                    if prev_tag != 'B-UNIT' and prev_tag != 'I-UNIT':
                        tag = 'B-UNIT'
                        prev_tag = 'B-UNIT'
                    else:
                        tag = 'I-UNIT'
                        prev_tag = 'I-UNIT'
                elif token in ingredient['item']:
                    if prev_tag != 'B-ITEM' and prev_tag != 'I-ITEM':
                        tag = 'B-ITEM'
                        prev_tag = 'B-ITEM'
                    else:
                        tag = 'I-ITEM'
                        prev_tag = 'I-ITEM'
                elif token in ingredient['comment']:
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
    parser.add_argument('-o', '--output', help='Path to output crf file')
    args = parser.parse_args()

    data = load_csv(args.input)
    create_crf(args.output, data)
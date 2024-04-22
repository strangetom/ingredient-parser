#!/usr/bin/env python3

import argparse
import re
import xml.etree.ElementTree as ET
from itertools import chain

from tqdm import tqdm

from .training_utils import load_datasets

## Tokeniser from preprocess.py ##
# Define regular expressions used by tokenizer.
# Matches one or more whitespace characters
WHITESPACE_TOKENISER = re.compile(r"\S+")
# Matches and captures one of the following: ( ) [ ] { } , " / : ;
PUNCTUATION_TOKENISER = re.compile(r"([\(\)\[\]\{\}\,\"/:;])")


def tokenize(sentence: str) -> list[str]:
    """Tokenise an ingredient sentence.
    The sentence is split on whitespace characters into a list of tokens.
    If any of these tokens contains of the punctuation marks captured by
    PUNCTUATION_TOKENISER, these are then split and isolated as a seperate
    token.

    The returned list of tokens has any empty tokens removed.

    Parameters
    ----------
    sentence : str
        Ingredient sentence to tokenize

    Returns
    -------
    list[str]
        List of tokens from sentence.

    Examples
    --------
    >>> tokenize("2 cups (500 ml) milk")
    ["2", "cups", "(", "500", "ml", ")", "milk"]

    >>> tokenize("1-2 mashed bananas: as ripe as possible")
    ["1-2", "mashed", "bananas", ":", "as", "ripe", "as", "possible"]
    """
    tokens = [
        PUNCTUATION_TOKENISER.split(tok)
        for tok in WHITESPACE_TOKENISER.findall(sentence)
    ]
    return [tok for tok in chain.from_iterable(tokens) if tok]


def score_sentence_similarity(first: str, second: str) -> float:
    """Calculate Dice coefficient for two strings.

    The dice coefficient is a measure of similarity determined by calculating
    the proportion of shared bigrams.

    Parameters
    ----------
    first : str
        First string
    second : str
        Second string

    Returns
    -------
    float
        Similarity score between 0 and 1.
        0 means the two strings do not share any bigrams.
        1 means the two strings are identical.
    """

    if first == second:
        # Indentical sentences have maximum score of 1
        return 1

    first_tokens = set(tokenize(first))
    second_tokens = set(tokenize(second))

    intersection = first_tokens & second_tokens

    return 2.0 * len(intersection) / (len(first_tokens) + len(second_tokens))


def create_html_table(
    indices: list[int],
    sentences: list[str],
    labels: list[list[str]],
    tokens: list[list[str]],
    sentence_source: list[tuple[str, int]],
) -> ET.Element:
    """Create HTM table to show similar sentences and their labels

    Parameters
    ----------
    indices : list[int]
        Indices of sentences to turn into table
    sentences : list[str]
        List of all sentences
    labels : list[dict[str, str]]
        List of labels for each sentence

    """
    table = ET.Element("table")

    header_tr = ET.Element("tr")
    for heading in [
        "Dataset",
        "Index",
        "Sentence",
        "Name",
        "Size",
        "Quantity",
        "Unit",
        "Preparation",
        "Comment",
    ]:
        td = ET.Element("td", attrib={"class": "row-heading"})
        td.text = heading
        header_tr.append(td)

    table.append(header_tr)

    for idx in indices:
        sentence = sentences[idx]
        dataset, dataset_idx = sentence_source[idx]

        tr = ET.Element("tr")

        dataset_td = ET.Element("td", attrib={"class": "row"})
        dataset_td.text = dataset
        tr.append(dataset_td)

        index_td = ET.Element("td", attrib={"class": "row"})
        index_td.text = str(dataset_idx + 2)
        tr.append(index_td)

        sentence_td = ET.Element("td", attrib={"class": "row"})
        sentence_td.text = sentence
        tr.append(sentence_td)

        name_td = ET.Element("td", attrib={"class": "row"})
        name_td.text = " ".join(
            [tok for tok, label in zip(tokens[idx], labels[idx]) if label == "NAME"]
        )
        tr.append(name_td)

        size_td = ET.Element("td", attrib={"class": "row"})
        size_td.text = " ".join(
            [tok for tok, label in zip(tokens[idx], labels[idx]) if label == "SIZE"]
        )
        tr.append(size_td)

        quantity_td = ET.Element("td", attrib={"class": "row"})
        quantity_td.text = " ".join(
            [tok for tok, label in zip(tokens[idx], labels[idx]) if label == "QTY"]
        )
        tr.append(quantity_td)

        unit_td = ET.Element("td", attrib={"class": "row"})
        unit_td.text = " ".join(
            [tok for tok, label in zip(tokens[idx], labels[idx]) if label == "UNIT"]
        )
        tr.append(unit_td)

        prep_td = ET.Element("td", attrib={"class": "row"})
        prep_td.text = " ".join(
            [tok for tok, label in zip(tokens[idx], labels[idx]) if label == "PREP"]
        )
        tr.append(prep_td)

        comment_td = ET.Element("td", attrib={"class": "row"})
        comment_td.text = " ".join(
            [tok for tok, label in zip(tokens[idx], labels[idx]) if label == "COMMENT"]
        )
        tr.append(comment_td)

        table.append(tr)

    return table


def results_to_html(
    similar: dict[int, list[int]],
    sentences: list[str],
    labels: list[list[str]],
    tokens: list[list[str]],
    sentence_source: list[tuple[str, int]],
) -> None:
    """Output similarity results to html file.
    The file contains a table for each group of similar sentences

    Parameters
    ----------
    similar : dict[int, list[int]]
        Dictionary of sentence index and list of similar sentence indices
    sentences : list[str]
        List of ingredient sentences
    labels : list[dict[str, str]]
        List of dictionary of ingredient sentence labels
    sentence_source : list[tuple[str, int]]
        List of tuples of (dataset_name, index_in_dataset) for each ingredient sentence
    """
    html = ET.Element("html")
    head = ET.Element("head")
    body = ET.Element("body")
    html.append(head)
    html.append(body)

    style = ET.Element("style", attrib={"type": "text/css"})
    style.text = """
    body {
      font-family: sans-serif;
      margin: 2rem;
    }
    table {
      margin-bottom: 2rem;
      border-collapse: collapse;
      border: black 3px solid;
    }
    td {
      padding: 0.5rem 1rem;
      border: black 1px solid;
    }
    .mismatch {
      font-weight: 700;
      background-color: #CC6666;
    }
    .row-heading {
      font-style: italic;
      background-color: #ddd;
    }
    """
    head.append(style)

    heading = ET.Element("h1")
    heading.text = "Similar sentences and their labels"
    body.append(heading)

    for k, v in similar.items():
        idx = [k] + v
        table = create_html_table(idx, sentences, labels, tokens, sentence_source)
        body.append(table)

    ET.indent(html, space="    ")
    with open("consistency_results.html", "w") as f:
        f.write("<!DOCTYPE html>\n")
        f.write(ET.tostring(html, encoding="unicode", method="html"))


def check_label_consistency(args: argparse.Namespace) -> None:
    """Check label consistency across dataset(s) by identifying similar
    sentences and showing how their tokens are labelled.

    Parameters
    ----------
    args : argparse.Namespace
        Cleaning utility configuration
    """
    vectors = load_datasets(
        args.database, args.table, args.datasets, discard_other=False
    )
    sentences = vectors.sentences
    sentence_source = [(source, i) for i, source in enumerate(vectors.source)]

    similar = {}
    unmatched_indices = set(range(len(sentences)))
    # This set contains the index of each entry in the dataframe
    # Once an input has been matched, we will remove it's index from this set
    # If the index is not in the set, we cannot match it again,
    # nor will we find matches for it
    for i, sentence in tqdm(
        enumerate(sentences), total=len(sentences), unit="sentence"
    ):
        if i not in unmatched_indices:
            continue

        unmatched_indices.remove(i)

        scores = [score_sentence_similarity(sentence, other) for other in sentences[i:]]
        matches = [
            i + j
            for j, score in enumerate(scores)
            if score > 0.85 and i + j in unmatched_indices
        ]

        for m in matches:
            unmatched_indices.remove(m)

        if len(matches) > 0:
            similar[i] = matches

    max_similarity = dict(
        sorted(similar.items(), key=lambda item: len(item[1]), reverse=True)
    )

    results_to_html(
        max_similarity, sentences, vectors.labels, vectors.tokens, sentence_source
    )

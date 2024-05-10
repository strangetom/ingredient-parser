#!/usr/bin/env python3

import argparse
import re
import xml.etree.ElementTree as ET
from collections import Counter
from itertools import chain

from sklearn.cluster import HDBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

from .training_utils import load_datasets

# Define regular expressions used by tokenizer.
# Matches one or more whitespace characters
WHITESPACE_TOKENISER = re.compile(r"\S+")
# Matches and captures one of the following: ( ) [ ] { } , " / : ;
PUNCTUATION_TOKENISER = re.compile(r"([\(\)\[\]\{\}\,/:;])")
# Matches and captures full stop at end of string
# (?>!\.\w) is a negative lookbehind that prevents matches if the last full stop
# is preceded by a a full stop then a word character.
FULL_STOP_TOKENISER = re.compile(r"(?<!\.\w)(\.)$")


def tokenize(sentence: str) -> list[str]:
    """Tokenise an ingredient sentence.

    The sentence is split on whitespace characters into a list of tokens.
    If any of these tokens contains of the punctuation marks captured by
    PUNCTUATION_TOKENISER, these are then split and isolated as a separate
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

    >>> tokenize("1.5 kg bananas, mashed")
    ["1.5", "kg", "bananas", ",", "mashed"]

    >>> tokenize("Freshly grated Parmesan cheese, for garnish.")
    ["Freshly", "grated", "Parmesan", "cheese", ",", "for", "garnish", "."]
    """
    tokens = [
        PUNCTUATION_TOKENISER.split(tok)
        for tok in WHITESPACE_TOKENISER.findall(sentence)
    ]
    flattened = [tok for tok in chain.from_iterable(tokens) if tok]

    # Second pass to separate full stops from end of tokens
    tokens = [FULL_STOP_TOKENISER.split(tok) for tok in flattened]

    return [tok for tok in chain.from_iterable(tokens) if tok]


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
        "Purpose",
    ]:
        td = ET.Element("td", attrib={"class": "row-heading"})
        td.text = heading
        header_tr.append(td)

    table.append(header_tr)

    # Sort sentences
    sorted_idx = sorted([(sentences[idx], idx) for idx in indices], key=lambda x: x[0])

    for sentence, idx in sorted_idx:
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

        purpose_td = ET.Element("td", attrib={"class": "row"})
        purpose_td.text = " ".join(
            [tok for tok, label in zip(tokens[idx], labels[idx]) if label == "PURPOSE"]
        )
        tr.append(purpose_td)

        table.append(tr)

    return table


def results_to_html(
    similar: list[int],
    sentences: list[str],
    labels: list[list[str]],
    tokens: list[list[str]],
    sentence_source: list[tuple[str, int]],
) -> None:
    """Output similarity results to html file.
    The file contains a table for each group of similar sentences

    Parameters
    ----------
    similar : list[int]
        List of similar sentence indices
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

    for idx in similar:
        table = create_html_table(idx, sentences, labels, tokens, sentence_source)
        body.append(table)

    ET.indent(html, space="    ")
    with open("consistency_results.html", "w") as f:
        f.write("<!DOCTYPE html>\n")
        f.write(ET.tostring(html, encoding="unicode", method="html"))


def cluster_sentence_ids(model, sources: list[tuple[str, int]], cluster_id: int):
    """Return list of IDs for sentence in cluster.

    Parameters
    ----------
    model : TYPE
        Description
    sources : list[tuple[str, int]]
        Description
    cluster_id : int
        ID of cluster to return sentence IDs for

    Returns
    -------
    list[int]
        List of sentence ids for cluster
    """
    return [
        uid
        for label, (source, uid) in zip(model.labels_, sources)
        if label == cluster_id
    ]


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

    pipeline = Pipeline(
        steps=[
            ("vectorize", TfidfVectorizer(tokenizer=tokenize, token_pattern=None)),
            (
                "cluster",
                HDBSCAN(
                    min_cluster_size=15,
                    cluster_selection_epsilon=0.5,
                    n_jobs=4,
                    cluster_selection_method="leaf",
                ),
            ),
        ],
        verbose=True,
    )
    pipeline.fit(sentences)
    model = pipeline.named_steps.get("cluster")
    label_counts = Counter(model.labels_)

    similar = []
    for label, _ in label_counts.most_common():
        if label == -1:
            continue

        ids = cluster_sentence_ids(model, sentence_source, label)
        similar.append(ids)

    results_to_html(similar, sentences, vectors.labels, vectors.tokens, sentence_source)

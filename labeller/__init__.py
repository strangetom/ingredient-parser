#!/usr/bin/env python3

import json
import re
import sqlite3
import string
from collections import Counter

from flask import Flask, Response, redirect, render_template, request, url_for

from ingredient_parser import inspect_parser

sqlite3.register_adapter(list, json.dumps)
sqlite3.register_converter("json", json.loads)

app = Flask(__name__)

DATABASE = "train/data/training.sqlite3"


@app.route("/")
def home():
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        c = conn.cursor()
        c.execute("SELECT source FROM en")
        sources = [source for (source,) in c.fetchall()]

    conn.close()

    count = Counter(sources)
    return render_template("index.html.jinja", datasets=list(count.items()))


@app.route("/edit/<string:dataset>", methods=["GET"])
def edit(dataset: str):
    """Show page to edit sentence token labels.

    The view shows the <range> of sentences, starting from <start>, where <start>
    and <range> and URL query parameters.

    Parameters
    ----------
    dataset : str
        Source dataset to select sentences from

    Returns
    -------
    str
        Rendered HTML template
    """
    start = request.args.get("start", None)
    count = request.args.get("range", None)

    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM en WHERE source IS ? LIMIT ? OFFSET ?;",
            (dataset, count, start),
        )
        data = [dict(row) for row in c.fetchall()]
    conn.close()

    return render_template(
        "label-editor.html.jinja",
        dataset=dataset,
        data=data,
        page_start_idx=int(start),
        page_range=int(count),
    )


@app.route("/index", methods=["GET"])
def sentences_by_id():
    """Show page to edit sentence token labels for sentences with ID specified in the
    list of IDs in the index URL query parameter.

    Returns
    -------
    str
        Rendered HTML template
    """
    indices = request.args.get("indices", None)
    if indices is None or indices == "":
        return render_template(
            "label-editor.html.jinja",
            dataset="",
            data=[],
            page_start_idx=None,
            page_range=None,
        )

    indices = [int(i) for i in indices.split(",")]
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            f"SELECT * FROM en WHERE id IN ({','.join(['?']*len(indices))});",
            indices,
        )
        data = [dict(row) for row in c.fetchall()]
    conn.close()

    sources = {entry["source"] for entry in data}

    return render_template(
        "label-editor.html.jinja",
        dataset=", ".join(sources),
        data=data,
        page_start_idx=None,
        page_range=None,
    )


@app.route("/filter", methods=["POST"])
def filter():
    if request.method == "POST":
        form = request.form
        return apply_filter(form)


@app.route("/insert", methods=["POST"])
def insert():
    if request.method == "POST":
        form = request.form
        return insert_sentences(form)


@app.route("/save", methods=["POST"])
def save():
    """Endpoint for saving sentences to database from /edit, /shuffle or /index pages

    Returns
    -------
    Response
        Response code indicating success or failure.
    """
    if request.method == "POST":
        form = request.form
        update = json.loads(form["data"])

        with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            c = conn.cursor()
            c.executemany(
                """UPDATE en 
                SET 
                sentence = :sentence, 
                tokens = :tokens, 
                labels = :labels, 
                foundation_foods = :foundation_foods
                WHERE id = :id;""",
                update["entries"],
            )
        conn.close()

        return Response(status=200)


@app.route("/delete/<int:index>")
def delete(index: int):
    """Delete entry with <index> from <dataset>

    Parameters
    ----------
    index : int
        Index of entry to delete

    Returns
    -------
    Response
        Success response
    """
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM en WHERE id = ?", (index,))

    return Response(status=200)


def apply_filter(params: dict[str, str]):
    """Apply selected filter to database and return page for editing sentences that
    match the filter.

    Parameters
    ----------
    params : dict[str, str]
        Filter settings

    Returns
    -------
    Response
        Redirection to sentences_by_id page.
    """
    # Select data from database
    datasets = [
        key.split("-")[-1]
        for key, value in params.items()
        if key.startswith("dataset-") and value == "on"
    ]
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            f"SELECT * FROM en WHERE source IN ({','.join(['?']*len(datasets))})",
            (datasets),
        )
        data = [dict(row) for row in c.fetchall()]
    conn.close()

    # Get list of selected labels
    labels = [
        key.split("-")[-1]
        for key, value in params.items()
        if key.startswith("label-") and value == "on"
    ]

    # Create regex for search query
    escaped = re.escape(params["filter-string"])
    if params.get("whole-word", "") == "on":
        # Strip trailing punctuation to make this work how I want it to, otherwise the
        # trailing punctuation in <escaped> means the trailing <\b> in the regex does
        # not match anything.
        while escaped[-1] in string.punctuation:
            escaped = escaped[:-1]
        expression = rf"\b{escaped}\b"
    else:
        expression = escaped

    if params.get("case-sensitive", "") == "on":
        query = re.compile(expression, re.UNICODE)
    else:
        query = re.compile(expression, re.UNICODE | re.IGNORECASE)

    # 9 possible labels in total
    if len(labels) == 9:
        # Search through sentences
        indices = []
        for entry in data:
            if query.search(entry["sentence"]):
                indices.append(str(entry["id"]))

        return redirect(url_for("sentences_by_id", indices=",".join(indices)))
    else:
        # Build string to search through from tokens with specified labels
        indices = []
        for entry in data:
            partial_sentence = " ".join(
                [
                    tok
                    for tok, label in zip(entry["tokens"], entry["labels"])
                    if label in labels
                ]
            )
            if query.search(partial_sentence):
                indices.append(str(entry["id"]))

        return redirect(url_for("sentences_by_id", indices=",".join(indices)))


def insert_sentences(params: dict[str, str]):
    """Insert new sentences to database, setting the source to the selected value.
    New sentences are tokenised automatically but have their labels set to "

    Parameters
    ----------
    params : dict[str, str]
        Sentences and source

    Returns
    -------
    Response
        Redirection to sentences_by_id page.
    """
    # If new dataset ID is set, use that as source. Otherwise use source from dropdown.
    if params.get("insert-new-dataset", False):
        source = params.get("insert-new-dataset")
    else:
        source = params.get("insert-dataset")

    sentences = params.get("insert-sentences", "").splitlines()
    guess_labels = params.get("guess-labels", "") == "on"

    indices = []
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        c = conn.cursor()
        for sentence in sentences:
            if not sentence:
                continue

            ins = inspect_parser(sentence, foundation_foods=True)
            tokens = ins.PostProcessor.tokens
            if guess_labels:
                labels = ins.PostProcessor.token_labels

                ff_tokens = " ".join(ff.text for ff in ins.foundation_foods)
                ff = [
                    idx
                    for idx, (token, label) in enumerate(zip(tokens, labels))
                    if token in ff_tokens and label == "NAME"
                ]
                name_labels = ["O"] * len(tokens)
            else:
                labels = [""] * len(tokens)
                ff = []
                name_labels = ["O"] * len(tokens)

            c.execute(
                """
                INSERT INTO en 
                (source, sentence, tokens, labels, foundation_foods, foundation_labels)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (source, sentence, tokens, labels, ff, name_labels),
            )
            indices.append(str(c.lastrowid))

    return redirect(url_for("sentences_by_id", indices=",".join(indices)))

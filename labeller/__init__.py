#!/usr/bin/env python3

import json
import random
import sqlite3
from pathlib import Path

from flask import Flask, Response, render_template, request

sqlite3.register_adapter(list, json.dumps)
sqlite3.register_converter("json", json.loads)

app = Flask(__name__)

DATABASE = "train/data/training.sqlite3"


@app.route("/")
def index():
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        c = conn.cursor()
        c.execute("SELECT DISTINCT source FROM training")
        res = c.fetchall()

    conn.close()

    datasets = [source for source, in res]
    return render_template("index.html.jinja", datasets=datasets)


@app.route("/edit/<string:dataset>", methods=["GET"])
def edit(dataset: str):
    """Return homepage

    Returns
    -------
    str
        Rendered HTML template
    """
    start = request.args.get("start", None)
    count = request.args.get("range", None)
    # indices = request.args.get("indices", None)

    if start is not None and count is not None:
        with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT id, sentence, tokens, labels FROM training WHERE source IS ? LIMIT ? OFFSET ?;",
                (dataset, count, start),
            )
            data = [dict(row) for row in c.fetchall()]
        conn.close()

    # elif indices is not None:
    #    indices = [int(i) for i in indices.split(",")]
    #    data = [entry for i, entry in enumerate(data) if i in indices]

    return render_template(
        "label-editor.html.jinja",
        dataset=dataset,
        data=data,
        page_start_idx=int(start) if start is not None else None,
        page_range=int(count) if count is not None else None,
    )


@app.route("/shuffle", methods=["GET"])
def shuffle():
    data = []
    for name, path in DATASETS.items():
        with open(path, "r") as f:
            dataset = json.load(f)

            # Set index and origin dataset for each entry
            for i, entry in enumerate(dataset):
                entry["index"] = i
                entry["dataset"] = name

        data.extend(dataset)

    # Shuffle
    random.shuffle(data)

    count = int(request.args.get("range", 500))
    return render_template(
        "label-editor-shuffle.html.jinja",
        data=data[:count],
    )


@app.route("/save", methods=["POST"])
def save():
    if request.method == "POST":
        form = request.form
        update = json.loads(form["data"])

        with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            c = conn.cursor()
            c.executemany(
                "UPDATE training SET sentence = :sentence, tokens = :tokens, labels = :labels WHERE id = :id;",
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
        c.execute("DELETE FROM training WHERE id = ?", (index,))

    return Response(status=200)

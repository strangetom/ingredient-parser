#!/usr/bin/env python3

import json
import sqlite3

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
            "SELECT * FROM training WHERE source IS ? LIMIT ? OFFSET ?;",
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

    indices = [int(i) for i in indices.split(",")]
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            f"SELECT * FROM training WHERE id IN ({','.join(['?']*len(indices))});",
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


@app.route("/shuffle", methods=["GET"])
def shuffle():
    """Return <range> random sentences from database, where <range> is a URL
    query paramters.

    Returns
    -------
    str
        Rendered HTML template
    """
    count = int(request.args.get("range", 500))

    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM training ORDER BY RANDOM() LIMIT ?;",
            (count,),
        )
        data = [dict(row) for row in c.fetchall()]
    conn.close()

    return render_template(
        "label-editor-shuffle.html.jinja",
        data=data[:count],
    )


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

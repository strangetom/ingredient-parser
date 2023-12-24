#!/usr/bin/env python3

import json
import random
from pathlib import Path

from flask import Flask, Response, render_template, request

app = Flask(__name__)


def locate_datasets() -> dict[str, str]:
    """Locate all .json datasets with train/data folder.
    Assumes all datasets are json files located in folders within the train/data folder.

    Returns
    -------
    dict[str, str]
        Dict of dataset name and pahh

    """
    datasets = {}

    path = Path("train/data")
    for folder in path.iterdir():
        if not folder.is_dir():
            continue

        json_files = folder.glob("*.json")
        for file in json_files:
            datasets[file.stem] = str(file)

    return datasets


DATASETS = locate_datasets()


@app.route("/")
def index():
    return render_template("index.html.jinja", datasets=DATASETS)


@app.route("/edit/<string:dataset>", methods=["GET"])
def edit(dataset: str):
    """Return homepage

    Returns
    -------
    str
        Rendered HTML template
    """
    dataset_path = DATASETS[dataset]
    with open(dataset_path, "r") as f:
        data = json.load(f)

    # Set index for each entry
    for i, entry in enumerate(data):
        entry["index"] = i

    start = request.args.get("start", None)
    count = request.args.get("range", None)
    indices = request.args.get("indices", None)

    if start is not None and count is not None:
        data = data[int(start) : int(start) + int(count)]
    elif indices is not None:
        indices = [int(i) for i in indices.split(",")]
        data = [entry for i, entry in enumerate(data) if i in indices]

    return render_template(
        "label-editor.html.jinja",
        dataset=dataset,
        dataset_path=dataset_path,
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

        dataset_path = DATASETS[update["dataset"]]
        with open(dataset_path, "r") as f:
            data = json.load(f)

        for entry in update["entries"]:
            data[entry["id"]] = {
                "sentence": entry["sentence"],
                "tokens": entry["tokens"],
                "labels": entry["labels"],
            }

        with open(dataset_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return Response(status=200)


@app.route("/delete/<string:dataset>")
def delete(dataset: str):
    """Delete entry with <index> from <dataset>

    Parameters
    ----------
    dataset : str
        Dataset from which to delete entry
    index : int
        Index of entry to delete

    Returns
    -------
    Response
        Success response
    """

    index = int(request.args.get("index", None))
    if index is None:
        return Response(status=404)

    dataset_path = DATASETS[dataset]
    with open(dataset_path, "r") as f:
        data = json.load(f)
        del data[index]

    with open(dataset_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return Response(status=200)

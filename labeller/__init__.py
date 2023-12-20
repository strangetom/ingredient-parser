#!/usr/bin/env python3

import json
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

    start = int(request.args.get("start", 0))
    count = int(request.args.get("range", 500))

    print(count)

    return render_template(
        "label-editor.html.jinja",
        dataset=dataset,
        dataset_path=dataset_path,
        data=data[start : start + count],
        page_start_idx=start,
        page_range=count,
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

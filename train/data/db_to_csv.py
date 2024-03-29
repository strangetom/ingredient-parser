#!/usr/bin/env python3

import csv
import json
import sqlite3

sqlite3.register_converter("json", json.loads)

BBC_CSV = "train/data/bbc/bbc-ingredients-snapshot-2017.csv"
COOKSTR_CSV = "train/data/cookstr/cookstr-ingredients-snapshot-2017.csv"
NYT_CSV = "train/data/nytimes/nyt-ingredients-snapshot-2015.csv"

DATABASE = "train/data/training.sqlite3"


def load_from_db(source: str) -> list[dict[str, str]]:
    """Get all training sentences for the given source

    Parameters
    ----------
    source : str
        "nyt", "cookstr", "bbc"

    Returns
    -------
    list[dict[str, str]]
        List of database rows as dicts
    """
    rows = []
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        data = c.execute("SELECT * FROM training WHERE source = ?", (source,))

    rows = [dict(d) for d in data]
    conn.close()

    return rows


def load_csv(path: str) -> list[dict[str, str]]:
    """Load csv file, returning rows as dicts

    Parameters
    ----------
    path : str
        Path to csv file

    Returns
    -------
    list[dict[str, str]]
        List of csv rows as dicts
    """
    sentences, rows = [], []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            sentences.append(row["input"])

    return rows, sentences


def create_csv_value(db_row: dict[str, str], label: str) -> str:
    """Create the value to insert into a csv field given by label for
    db_row.

    The value in simply all the tokens with label joined with a space

    Parameters
    ----------
    db_row : dict[str, str]
        Database row to create value from
    label : str
        Label to create csv value for

    Returns
    -------
    str
        Constructed value to insert into csv
    """
    tokens = [
        tok for tok, lab in zip(db_row["tokens"], db_row["labels"]) if lab == label
    ]
    return " ".join(tokens)


def write_csv(path: str, csv_rows: list[dict]) -> None:
    """Write csv rows to file

    Parameters
    ----------
    path : str
        Path to csv file to write
    csv_rows : list[dict]
        List of dicts to write to each row of the csv
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "input",
            "name",
            "quantity",
            "unit",
            "size",
            "preparation",
            "comment",
        ]
        writer = csv.DictWriter(f, fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)


if __name__ == "__main__":
    source_csv = {
        "bbc": BBC_CSV,
        "cookstr": COOKSTR_CSV,
        "nyt": NYT_CSV,
    }

    for source, csv_file in source_csv.items():
        db_rows = load_from_db(source)
        csv_rows, csv_sentences = load_csv(csv_file)

        for db_row in db_rows:
            try:
                index = csv_sentences.index(db_row["sentence"])
            except ValueError as e:
                print(f"Failed on {db_row}")
                raise e

            csv_rows[index]["name"] = create_csv_value(db_row, "NAME")
            csv_rows[index]["quantity"] = create_csv_value(db_row, "QTY")
            csv_rows[index]["unit"] = create_csv_value(db_row, "UNIT")
            csv_rows[index]["size"] = create_csv_value(db_row, "SIZE")
            csv_rows[index]["preparation"] = create_csv_value(db_row, "PREP")
            csv_rows[index]["comment"] = create_csv_value(db_row, "COMMENT")

            # Set value at index to None so we can't match it again if there are
            # duplicate sentences
            csv_sentences[index] = None

        write_csv(csv_file, csv_rows)

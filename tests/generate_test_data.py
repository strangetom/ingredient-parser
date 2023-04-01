#!/usr/bin/env python3

import json
import random


def load_csv(csv_filename: str) -> tuple[List[str], List[Dict[str, str]]]:
    """Load csv file generated py ```generate_training_testing_csv.py``` and parse
    contents into ingredients and labels lists

    Parameters
    ----------
    csv_filename : str
        Name of csv file

    Returns
    -------
    List[str]
        List of ingredient strings
    List[Dict[str, str]]
        List of dictionaries, each dictionary the ingredient labels
    """
    labels, sentences = [], []
    with open(csv_filename, "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip first row
        for row in reader:
            sentences.append(row[0])
            labels.append(
                {
                    "name": row[1].strip().lower(),
                    "quantity": row[2].strip().lower(),
                    "unit": row[3].strip().lower(),
                    "comment": row[4].strip().lower(),
                }
            )
    return sentences, labels


if __name__ == "__main__":

    # Load NYT and SF data
    SF_sentences, SF_labels = load_csv("train/data/strangerfoods/sf_labelled_data.csv")
    NYT_sentences, NYT_labels = load_csv(
        "train/data/nytimes/nyt-ingredients-snapshot-2015.csv"
    )
    # Limit NYT data to first 20_000 items
    NYT_sentences, NYT_labels = NYT_sentences[:20_000], NYT_labels[:20_000]

    # Select 250 random samples from each data set
    NYT_indices = random.choices(range(0, 20_000), k=250)
    SF_indices = random.choices(range(0, len(SF_sentences)), k=250)

    data = []
    for idx in NYT_indices:
        sent = NYT_sentences[idx]
        labels = NYT_labels[idx]
        data.append({"sentence": sent, "labels": labels})
    for idx in SF_indices:
        sent = SF_sentences[idx]
        labels = SF_labels[idx]
        data.append({"sentence": sent, "labels": labels})

    # Write to file in newline delimited json
    with open("tests/test_parser.json", "w") as f:
        f.write("\n".join(json.dumps(line) for line in data))

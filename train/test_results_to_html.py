import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingredient_parser import PreProcessor


def test_results_to_html(
    sentences: List[str],
    labels_truth: List[List[str]],
    labels_prediction: List[List[str]],
) -> None:
    """Output results for test vectors that failed to label entire sentence with the truth labels
    in HTML format

    Parameters
    ----------
    sentences : List[str]
        List of ingredient sentences
    labels_truth : List[List[str]]
        True labels for sentence
    labels_prediction : List[List[str]]
        Predicted labels for sentence
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
    .row-title {
      font-style: italic;
      background-color: #ddd;
    }
    """
    head.append(style)

    heading = ET.Element("h1")
    heading.text = "Incorrect sentences in test data"
    body.append(heading)

    incorrect = 0
    for (sentence, truth, prediction) in zip(
        sentences, labels_truth, labels_prediction
    ):
        if truth != prediction:
            tokens: List[str] = PreProcessor(
                sentence, defer_pos_tagging=True
            ).tokenized_sentence
            table = create_html_table(tokens, truth, prediction)
            p = ET.Element("p")
            p.text = sentence
            body.append(p)
            body.append(table)

            incorrect += 1

    heading2 = ET.Element("h2")
    heading2.text = f"{incorrect:,} incorrect sentences."
    body.insert(1, heading2)

    ET.indent(html, space="    ")
    with open("test_results.html", "w") as f:
        f.write("<!DOCTYPE html>\n")
        f.write(ET.tostring(html, encoding="unicode", method="html"))


def create_html_table(
    tokens: List[str], labels_truth: List[str], labels_prediction: List[str]
) -> ET.Element:
    """Create HTM table for a sentence to show tokens, true labels and predicted labels

    Parameters
    ----------
    tokens : List[str]
        List of tokens for sentence
    labels_truth : List[str]
        True labels for each token
    labels_prediction : List[str]
        Predicted labels for each token
    """
    table = ET.Element("table")

    tokens_tr = ET.Element("tr")
    truth_tr = ET.Element("tr")
    prediction_tr = ET.Element("tr")

    tokens_title = ET.Element("td", attrib={"class": "row-title"})
    tokens_title.text = "Token"
    tokens_tr.append(tokens_title)
    truth_title = ET.Element("td", attrib={"class": "row-title"})
    truth_title.text = "Truth"
    truth_tr.append(truth_title)
    prediction_title = ET.Element("td", attrib={"class": "row-title"})
    prediction_title.text = "Prediction"
    prediction_tr.append(prediction_title)

    for (token, truth, prediction) in zip(tokens, labels_truth, labels_prediction):

        token_td = ET.Element("td")
        token_td.text = token

        truth_td = ET.Element("td")
        truth_td.text = truth
        prediction_td = ET.Element("td")
        prediction_td.text = prediction
        if truth != prediction:
            truth_td.attrib = {"class": "mismatch"}
            prediction_td.attrib = {"class": "mismatch"}

        tokens_tr.append(token_td)
        truth_tr.append(truth_td)
        prediction_tr.append(prediction_td)

    table.append(tokens_tr)
    table.append(truth_tr)
    table.append(prediction_tr)

    return table


if __name__ == "__main__":
    raise NotImplementedError()

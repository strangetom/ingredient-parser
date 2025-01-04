#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_results_to_html(
    sentences: list[str],
    sentence_tokens: list[str],
    labels_truth: list[list[str]],
    labels_prediction: list[list[str]],
    scores_prediction: list[list[float]],
    sentence_sources: list[str],
) -> None:
    """Output results for test vectors that failed to label entire sentence with the
    truth labels in HTML format.

    Parameters
    ----------
    sentences : list[str]
        List of ingredient sentences
    sentence_tokens : list[str]
        List of tokens for sentence
    labels_truth : list[list[str]]
        True labels for tokens
    labels_prediction : list[list[str]]
        Predicted labels for tokens
    scores_prediction : list[list[float]]
        Scores for predicted labels for tokens
    sentence_sources : list[str]
        List of sentence sources
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
    div > div {
      display: flex;
      align-items: center;
    }
    .mismatch {
      font-weight: 700;
      background-color: #CC6666;
    }
    .low-score {
      font-weight: 700;
      background-color: #FFCC00;
    }
    .row-title {
      font-style: italic;
      background-color: #ddd;
    }
    h4 {
      margin-bottom: 0;
    }
    label {
      margin-right: 1rem;
      text-transform: uppercase;
    }
    .copy {
      margin-left: 1rem;
    }
    .hidden {
      display: none;
    }
    """
    head.append(style)

    heading = ET.Element("h1")
    heading.text = "Incorrect sentences in test data"
    body.append(heading)

    incorrect = []
    mismatch_counts = set()
    # Sort by sentence sort
    for src, sentence, tokens, truth, prediction, scores in sorted(
        zip(
            sentence_sources,
            sentences,
            sentence_tokens,
            labels_truth,
            labels_prediction,
            scores_prediction,
        )
    ):
        if truth != prediction:
            # Count mismatches and only include if greater than 0
            mismatches = sum(i != j for i, j in zip(truth, prediction))
            if mismatches > 0:
                mismatch_counts.add(mismatches)
                table = create_html_table(tokens, truth, prediction, scores)
                div = ET.Element("div")
                p = ET.Element("p")
                p.text = f"[{src.upper()}] {sentence}"
                copy_button = ET.Element("button", attrib={"class": "copy"})
                copy_button.text = "Copy text"
                div.append(p)
                div.append(copy_button)

                wrapper = ET.Element(
                    "div",
                    attrib={
                        "class": "wrapper hidden",
                        "data-mismatches": str(mismatches),
                        "data-src": src,
                    },
                )
                wrapper.append(div)
                wrapper.append(table)
                body.append(wrapper)

                incorrect.append(src)

    total_count = Counter(sentence_sources)
    incorrect_count = Counter(incorrect)
    src_count_str = "".join(
        [
            f"{k.upper()}: {v} ({100*v/total_count[k]:.2f}%), "
            for k, v in incorrect_count.items()
        ]
    )

    body.insert(1, create_filter_elements(mismatch_counts, set(sentence_sources)))

    heading2 = ET.Element("h2")
    heading2.text = f"{len(incorrect):,} incorrect sentences. [{src_count_str}]"
    body.insert(1, heading2)

    # Script to add "click" event listener to all copy buttons
    script = ET.Element("script")
    script.text = """
    let copyButtons = document.querySelectorAll("button.copy");
    copyButtons.forEach((button) => {
        button.addEventListener("click", (e) => {
            let text = e.target.previousElementSibling.innerText;
            // Strip off source from beginning
            text = text.substring(text.indexOf(" ")+1);
            navigator.clipboard.writeText(text);
        });
    });
    function applyFilter() {
        let filtered_src = {};
        let sentences = document.querySelectorAll(".wrapper");
        let mismatch_filters = [...document.querySelectorAll("input.mismatch")]
            .filter(el => el.checked)
            .map(el => el.dataset.value);
        let src_filters = [...document.querySelectorAll("input.src")]
            .filter(el => el.checked)
            .map(el => el.dataset.value);
        sentences.forEach((sent) => {
            if (mismatch_filters.includes(sent.dataset.mismatches) &&
                src_filters.includes(sent.dataset.src)) {
                sent.classList.remove("hidden");
                if (filtered_src[sent.dataset.src] == undefined){
                    filtered_src[sent.dataset.src] = 1;
                } else {
                    filtered_src[sent.dataset.src] += 1;
                }
            } else {
                sent.classList.add("hidden");
            }
        })
        let filter_counts = []
        for (const [k, v] of Object.entries(filtered_src)) {
            filter_counts.push(`${k.toUpperCase()}: ${v}, `);
        };
        let filter_count_el = document.querySelector("#filter-counts");
        filter_count_el.innerText = " [" + filter_counts.join("") + "]";
    };
    let filterInputs = document.querySelectorAll("input[type='checkbox']");
    filterInputs.forEach((input) => {
        input.addEventListener("change", (e) => {
            applyFilter();
        })
    });
    """
    body.append(script)

    ET.indent(html, space="    ")
    with open("test_results.html", "w") as f:
        f.write("<!DOCTYPE html>\n")
        f.write(ET.tostring(html, encoding="unicode", method="html"))


def create_html_table(
    tokens: list[str],
    labels_truth: list[str],
    labels_prediction: list[str],
    scores: list[float],
) -> ET.Element:
    """Create HTM table for a sentence to show tokens, true labels and predicted labels

    Parameters
    ----------
    tokens : list[str]
        List of tokens for sentence
    labels_truth : list[str]
        True labels for each token
    labels_prediction : list[str]
        Predicted labels for each token
    scores : list[float]
        Score for predicted label for each token
    """
    table = ET.Element("table")

    tokens_tr = ET.Element("tr")
    truth_tr = ET.Element("tr")
    prediction_tr = ET.Element("tr")
    score_tr = ET.Element("tr")

    tokens_title = ET.Element("td", attrib={"class": "row-title"})
    tokens_title.text = "Token"
    tokens_tr.append(tokens_title)
    truth_title = ET.Element("td", attrib={"class": "row-title"})
    truth_title.text = "Truth"
    truth_tr.append(truth_title)
    prediction_title = ET.Element("td", attrib={"class": "row-title"})
    prediction_title.text = "Prediction"
    prediction_tr.append(prediction_title)
    score_title = ET.Element("td", attrib={"class": "row-title"})
    score_title.text = "Score"
    score_tr.append(score_title)

    for token, truth, prediction, score in zip(
        tokens, labels_truth, labels_prediction, scores
    ):
        token_td = ET.Element("td")
        token_td.text = token

        truth_td = ET.Element("td")
        truth_td.text = truth
        prediction_td = ET.Element("td")
        prediction_td.text = prediction
        if truth != prediction:
            truth_td.attrib = {"class": "mismatch"}
            prediction_td.attrib = {"class": "mismatch"}

        score_td = ET.Element("td")
        score_td.text = f"{100*score:.1f}%"
        if score <= 0.6:
            score_td.attrib = {"class": "low-score"}

        tokens_tr.append(token_td)
        truth_tr.append(truth_td)
        prediction_tr.append(prediction_td)
        score_tr.append(score_td)

    table.append(tokens_tr)
    table.append(truth_tr)
    table.append(prediction_tr)
    table.append(score_tr)

    return table


def create_filter_elements(mismatch_counts: set[int], sources: set[str]) -> ET.Element:
    """Create div element containing checkboxes for filter incorrect sentences by
    numbers of incorrect tokens and by source.

    Parameters
    ----------
    mismatch_counts : set[int]
        Filter options for mismatches
    sources : set[str]
        Filter options for sources

    Returns
    -------
    ET.Element
        Elelemt to insert into test results HTML
    """
    div = ET.Element("div")

    h4 = ET.Element("h4")
    h4.text = "Filter by number of mismatches."
    span = ET.Element("span", attrib={"id": "filter-counts"})
    h4.append(span)
    div.append(h4)

    div_mismatch_filters = ET.Element("div")
    for count in mismatch_counts:
        inp = ET.Element(
            "input",
            attrib={
                "type": "checkbox",
                "class": "mismatch",
                "name": f"filter-{count}",
                "id": f"filter-{count}",
                "data-value": f"{count}",
            },
        )
        label = ET.Element("label", attrib={"for": f"filter-{count}"})
        label.text = f"{count}"

        div_mismatch_filters.append(inp)
        div_mismatch_filters.append(label)

    div_src_filters = ET.Element("div")
    for src in sources:
        inp = ET.Element(
            "input",
            attrib={
                "type": "checkbox",
                "class": "src",
                "name": f"filter-{src}",
                "id": f"filter-{src}",
                "data-value": f"{src}",
            },
        )
        label = ET.Element("label", attrib={"for": f"filter-{src}"})
        label.text = f"{src}"

        div_src_filters.append(inp)
        div_src_filters.append(label)

    div.append(div_mismatch_filters)
    div.append(div_src_filters)

    return div

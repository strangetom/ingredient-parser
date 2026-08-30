#!/usr/bin/env python3

import logging
import xml.etree.ElementTree as ET
from collections import Counter
from itertools import chain

logger = logging.getLogger(__name__)


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
      position: relative;
    }
    div > div {
      display: flex;
      align-items: center;
    }
    div.filters {
      display: flex;
      gap: 1rem;
    }
    div.filter-options {
      display: flex;
      flex-direction: column;
      width: 23ch;
      border: 1px solid black;
      border-radius: .25rem;
      padding: .5rem;
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
    h4, h5 {
      margin: 0;
    }
    h4 {
      display: inline;
    }
    label {
      text-transform: uppercase;
    }
    .copy {
      margin-left: 1rem;
    }
    .hidden {
      display: none;
    }
    tr:first-of-type {
      counter-reset: token-counter;
      counter-set: token-counter -1;
    }
    tr:first-of-type td:not(:first-of-type)::after {
      counter-increment: token-counter;
      content: counter(token-counter);
      position: absolute;
      top: 0;
      right: .25rem;
      font-size: .7rem;
      color: #999;
    }
    """
    head.append(style)

    heading = ET.Element("h1")
    heading.text = "Incorrect sentences in test data"
    body.append(heading)

    incorrect = []
    label_errors = []
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
                sentence_label_errors = list(
                    chain.from_iterable(
                        [{i, j} for i, j in zip(truth, prediction) if i != j]
                    )
                )
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
                        "data-errors": ",".join(sentence_label_errors),
                    },
                )
                wrapper.append(div)
                wrapper.append(table)
                body.append(wrapper)

                incorrect.append(src)
                label_errors.extend(sentence_label_errors)

    body.insert(
        1,
        create_filter_elements(
            mismatch_counts,
            Counter(incorrect),
            Counter(sentence_sources),
            Counter(label_errors),
        ),
    )

    heading2 = ET.Element("h2")
    heading2.text = f"{len(incorrect)} incorrect sentences."
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
    let selectAllButtons = document.querySelectorAll("button.select-all");
    selectAllButtons.forEach(button => {
        button.addEventListener("click", (e) => {
            let parent = e.target.parentElement;
            let checkboxes = parent.querySelectorAll("input[type='checkbox']");
            checkboxes.forEach(box => box.checked = true);
            applyFilter();
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

        let error_filters = [...document.querySelectorAll("input.error")]
            .filter(el => el.checked)
            .map(el => el.dataset.value);
        error_filters = new Set(error_filters);

        let token_filters = document.querySelector("#token-filter").value.split(" ")
            .map(token => token.toLowerCase());
        if (token_filters == "") {
            token_filters = new Set();
        }else{
            token_filters = new Set(token_filters);
        }

        sentences.forEach((sent) => {
            let sentence_tokens = [...sent.querySelectorAll("tr:first-of-type > td")]
                .map(td => td.innerText.toLowerCase());
            sent_tokens = new Set(sentence_tokens);
            
            let errors = new Set(sent.dataset.errors.split(","));
            if (mismatch_filters.includes(sent.dataset.mismatches) &&
                src_filters.includes(sent.dataset.src) && 
                errors.intersection(error_filters).size > 0 && 
                (
                  token_filters.size == 0 || 
                  sent_tokens.intersection(token_filters).size == token_filters.size)
                ) {
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
        let total = 0
        for (const [k, v] of Object.entries(filtered_src)) {
            filter_counts.push(`${k.toUpperCase()}: ${v}, `);
            total += v;
        };
        let filter_count_el = document.querySelector("#filter-counts");
        let filter_text = " [" + filter_counts.join("") + "] (" + total + " total)"
        filter_count_el.innerText = filter_text;
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
    logger.info("HTML output of incorrect sentence written to 'test_results.html'.")


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
        score_td.text = f"{100 * score:.1f}%"
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


def create_filter_elements(
    mismatch_counts: set[int],
    incorrect_source: Counter,
    total_source: Counter,
    label_errors: Counter,
) -> ET.Element:
    """Create div element containing checkboxes for filter incorrect sentences by
    numbers of incorrect tokens, sentence source and label error.

    Parameters
    ----------
    mismatch_counts : set[int]
        Filter options for mismatches.
    incorrect_source : Counter
        Counter object detailing number of errors for each source.
    total_source : Counter
        Counter object detailing number of test sentences for each source.
    label_errors : Counter
        Counter object detailing number of errors for each label.

    Deleted Parameters
    ------------------
    sources : set[str]
        Filter options for sources.

    No Longer Returned
    ------------------
    ET.Element
        Element to insert into test results HTML
    """
    details = ET.Element("details")

    summary = ET.Element("summary")
    h4 = ET.Element("h4")
    h4.text = "Filter by number of mismatches, source and label error."
    span = ET.Element("span", attrib={"id": "filter-counts"})
    h4.append(span)
    summary.append(h4)
    details.append(summary)

    div_filter_optons = ET.Element("div", attrib={"class": "filters"})
    details.append(div_filter_optons)

    div_mismatch_filters = ET.Element("div", attrib={"class": "filter-options"})
    h5_mismatch_filters = ET.Element("h5")
    h5_mismatch_filters.text = "Number of errors"
    div_mismatch_filters.append(h5_mismatch_filters)
    div_mismatch_filters.append(create_select_all_button())
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
        label.append(inp)

        div_mismatch_filters.append(label)

    div_src_filters = ET.Element("div", attrib={"class": "filter-options"})
    h5_src_filters = ET.Element("h5")
    h5_src_filters.text = "Source"
    div_src_filters.append(h5_src_filters)
    div_src_filters.append(create_select_all_button())
    for src, count in sorted(incorrect_source.items(), key=lambda x: x[0]):
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
        label.text = f"{src} ({count} = {100 * count / total_source[src]:.1f}%)"
        label.append(inp)

        div_src_filters.append(label)

    div_label_filters = ET.Element("div", attrib={"class": "filter-options"})
    h5_label_filters = ET.Element("h5")
    h5_label_filters.text = "Label error"
    div_label_filters.append(h5_label_filters)
    div_label_filters.append(create_select_all_button())
    for lab, count in sorted(label_errors.items(), key=lambda x: x[0]):
        inp = ET.Element(
            "input",
            attrib={
                "type": "checkbox",
                "class": "error",
                "name": f"filter-{lab}",
                "id": f"filter-{lab}",
                "data-value": f"{lab}",
            },
        )
        label = ET.Element("label", attrib={"for": f"filter-{lab}"})
        label.text = f"{lab} ({count})"
        label.append(inp)

        div_label_filters.append(label)

    div_token_filter = ET.Element("div", attrib={"class": "filter-options"})
    h5_token_filters = ET.Element("h5")
    h5_token_filters.text = "Filter by token"
    div_token_filter.append(h5_token_filters)
    filter_input = ET.Element(
        "input",
        attrib={
            "type": "search",
            "id": "token-filter",
            "name": "token-filter",
        },
    )
    token_filter_button = ET.Element(
        "button",
        attrib={
            "type": "button",
            "class": "select-all",
        },
    )
    token_filter_button.text = "Filter by tokens"
    div_token_filter.append(filter_input)
    div_token_filter.append(token_filter_button)

    div_filter_optons.append(div_mismatch_filters)
    div_filter_optons.append(div_src_filters)
    div_filter_optons.append(div_label_filters)
    div_filter_optons.append(div_token_filter)

    return details


def create_select_all_button() -> ET.Element:
    """Return HTML Button element

    Returns
    -------
    ET.Element
        Button HTML Element
    """
    button = ET.Element(
        "button",
        attrib={
            "type": "button",
            "class": "select-all",
        },
    )
    button.text = "Select all"
    return button
    button

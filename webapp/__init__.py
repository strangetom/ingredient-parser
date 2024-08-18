#!/usr/bin/env python3


from flask import Flask, render_template, request

from ingredient_parser import inspect_parser
from ingredient_parser.dataclasses import IngredientText, ParserDebugInfo

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    """Return homepage.

    Returns
    -------
    str
        Rendered HTML template
    """
    sentence = request.args.get("sentence", None)
    discard_isolated_stop_words = (
        request.args.get("discard_isolated_stop_words", None) == "on"
    )
    expect_name_in_output = request.args.get("expect_name_in_output", None) == "on"
    string_units = request.args.get("string_units", None) == "on"
    imperial_units = request.args.get("imperial_units", None) == "on"
    core_names = request.args.get("core_names", None) == "on"

    if sentence is None:
        return render_template(
            "index.html.jinja",
            display=False,
            sentence="",
            discard_isolated_stop_words=True,
            expect_name_in_output=True,
            string_units=False,
            imperial_units=False,
            core_names=False,
        )

    parser_info = inspect_parser(
        sentence,
        discard_isolated_stop_words=discard_isolated_stop_words,
        expect_name_in_output=expect_name_in_output,
        string_units=string_units,
        imperial_units=imperial_units,
        core_names=core_names,
    )
    parsed = parser_info.PostProcessor.parsed
    marginals = get_all_marginals(parser_info)

    return render_template(
        "index.html.jinja",
        display=True,
        sentence=sentence,
        discard_isolated_stop_words=discard_isolated_stop_words,
        expect_name_in_output=expect_name_in_output,
        string_units=string_units,
        imperial_units=imperial_units,
        core_names=core_names,
        tokens=zip(
            parser_info.PostProcessor.tokens,
            parser_info.PostProcessor.labels,
            marginals,
        ),
        name=parsed.name if parsed.name is not None else IngredientText("", 0),
        size=parsed.size if parsed.size is not None else IngredientText("", 0),
        amounts=parsed.amount,
        preparation=parsed.preparation
        if parsed.preparation is not None
        else IngredientText("", 0),
        comment=parsed.comment if parsed.comment is not None else IngredientText("", 0),
        purpose=parsed.purpose if parsed.purpose is not None else IngredientText("", 0),
    )


def get_all_marginals(parser_info: ParserDebugInfo) -> list[dict[str, float]]:
    """Return marginals for each label for each token in sentence.

    Parameters
    ----------
    parser_info : ParserDebugInfo
        Parser debug info.

    Returns
    -------
    list[dict[str, flaot]]
        Dict of label-score pairs for each token.
    """
    labels = [
        "NAME_CORE",
        "NAME_DESC",
        "QTY",
        "UNIT",
        "PREP",
        "PURPOSE",
        "COMMENT",
        "SIZE",
        "PUNC",
    ]

    marginals = []
    tagger = parser_info.tagger
    for i, _ in enumerate(parser_info.PostProcessor.tokens):
        token_marginals = {}
        for label in labels:
            token_marginals[label] = tagger.marginal(label, i)

        marginals.append(token_marginals)

    return marginals

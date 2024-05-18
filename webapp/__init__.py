#!/usr/bin/env python3


from flask import Flask, render_template, request

from ingredient_parser import inspect_parser
from ingredient_parser.dataclasses import IngredientText

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
    guess_name_fallback = request.args.get("guess_name_fallback", None) == "on"
    string_units = request.args.get("string_units", None) == "on"
    imperial_units = request.args.get("imperial_units", None) == "on"

    if sentence is None:
        return render_template(
            "index.html.jinja",
            display=False,
            sentence="",
            discard_isolated_stop_words=True,
            guess_name_fallback=True,
            string_units=False,
            imperial_units=False,
        )

    parser_info = inspect_parser(
        sentence,
        discard_isolated_stop_words=discard_isolated_stop_words,
        guess_name_fallback=guess_name_fallback,
        string_units=string_units,
        imperial_units=imperial_units,
    )
    parsed = parser_info.PostProcessor.parsed

    return render_template(
        "index.html.jinja",
        display=True,
        sentence=sentence,
        discard_isolated_stop_words=discard_isolated_stop_words,
        guess_name_fallback=guess_name_fallback,
        string_units=string_units,
        imperial_units=imperial_units,
        tokens=zip(
            parser_info.PostProcessor.tokens,
            parser_info.PostProcessor.labels,
            parser_info.PostProcessor.scores,
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

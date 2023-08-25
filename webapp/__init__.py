#!/usr/bin/env python3


from flask import Flask, render_template, request

from ingredient_parser import inspect_parser

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    """Return homepage

    Returns
    -------
    str
        Rendered HTML template
    """
    sentence = request.args.get("sentence", None)
    if sentence is None:
        return render_template(
            "index.html.jinja",
            display=False,
            sentence="",
        )

    parser_info = inspect_parser(sentence)
    parsed = parser_info.PostProcessor.parsed()

    return render_template(
        "index.html.jinja",
        display=True,
        sentence=sentence,
        tokens=zip(parser_info.PostProcessor.tokens, parser_info.PostProcessor.labels),
        name=parsed.name,
        amounts=parsed.amount,
        comment=parsed.comment,
        other=parsed.other,
    )

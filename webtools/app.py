#!/usr/bin/env python3

import json
import random
import sqlite3
import traceback
from fractions import Fraction
from http import HTTPStatus
from importlib.metadata import PackageNotFoundError, distribution
from typing import Any, List, Union

from _globals import (
    MODEL_REQUIREMENTS,
    NPM_BUILD_DIRECTORY,
    RESERVED_DOTNUM_RANGE_CHARS,
    RESERVED_LABELLER_SEARCH_CHARS,
    SQL3_DATABASE,
    SQL3_DATABASE_TABLE,
)
from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS, cross_origin
from pint import Unit
from search import id_search, list_all_entries, string_search

from ingredient_parser import inspect_parser
from ingredient_parser.dataclasses import (
    CompositeIngredientAmount,
    IngredientAmount,
    IngredientText,
    ParserDebugInfo,
)
from ingredient_parser.en._loaders import load_parser_model

# SQLite
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_converter("json", json.loads)


# Flask
class JsonProviderIngredientSerializable(DefaultJSONProvider):
    """Custom serialization for non-natively serializable types, namely Fraction."""

    @staticmethod
    def default(entity: Any):
        if isinstance(entity, Fraction):
            return str(entity)
        elif isinstance(entity, Unit):
            return str(entity)
        return DefaultJSONProvider.default(entity)


app = Flask(__name__, static_folder=NPM_BUILD_DIRECTORY, static_url_path="/")
app.json_provider_class = JsonProviderIngredientSerializable
app.json = JsonProviderIngredientSerializable(app)
cors = CORS(app)

# Reset on load @lru_cache
load_parser_model.cache_clear()


# Helpers
def is_valid_dotnum_range(value: str) -> bool:
    """Checks str against the format "{digit}..{digit}"""
    return bool(RESERVED_DOTNUM_RANGE_CHARS.fullmatch(value))


def jsonify_error(
    status: int,
    exception: Union[Exception, None] = None,
):
    """Boilerplate json response for all HTTP errors

    Parameters
    -------
    status : int
        Any HTTPCode value, e.g. 200, 404, etc
    exception: Exception | None
        Exception handle to display traceback message

    Returns
    -------
    Flask JSONify Response

    """

    try:
        return jsonify(
            {
                "status": HTTPStatus(status).value,
                "error": f"{HTTPStatus(status).name}",
                "traceback": "".join(
                    traceback.TracebackException.from_exception(exception).format()
                )
                if exception
                else "",
                "description": HTTPStatus(status).description,
            }
        ), HTTPStatus(status).value
    except Exception as ex:
        return jsonify(
            {
                "status": 500,
                "error": f"{HTTPStatus.INTERNAL_SERVER_ERROR.value}",
                "traceback": "".join(
                    traceback.TracebackException.from_exception(ex).format()
                ),
                "description": HTTPStatus.INTERNAL_SERVER_ERROR.description,
            }
        ), 500


def get_all_marginals(parser_info: ParserDebugInfo) -> list[dict[str, float]]:
    """
    Return marginals for each label for each token in sentence.

    Parameters
    -------
    parser_info: ParserDebugInfo
        For token extraction, and access to marginal calculations

    Returns
    -------
    list[dict[str, float]]
        List of marginals, e.g. [ { 'B_NAME_TOK': 0.04, 'QTY': 0.56 }, ... ]
    """

    labels = [
        "B_NAME_TOK",
        "I_NAME_TOK",
        "NAME_VAR",
        "NAME_MOD",
        "NAME_SEP",
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
            token_marginals[label] = round(tagger.marginal(label, i), 4)

        marginals.append(token_marginals)
    return marginals


def amount_resolver(
    amounts: List[Union[CompositeIngredientAmount, IngredientAmount]],
) -> List[Union[IngredientAmount, List[IngredientAmount]]]:
    """
    Iterates over a polymorphic list of ingredient amounts

    Parameters
    -------
    amounts: List[Union[CompositeIngredientAmount, IngredientAmount]]

    Returns
    -------
    List[Union[IngredientAmount, List[IngredientAmount]]]

    """

    return [
        (amount.amounts if isinstance(amount, CompositeIngredientAmount) else amount)
        for amount in amounts
    ]


# routes
@app.route("/parser", methods=["POST"])
@cross_origin()
def parser():
    """Endpoint for testing and seeing results for the parser from a sentence"""

    if request.method == "POST":
        data = request.json

        if data is None:
            return jsonify_error(status=404)

        try:
            sentence = data.get("sentence", "")
            discard_isolated_stop_words = data.get("discard_isolated_stop_words", True)
            expect_name_in_output = data.get("expect_name_in_output", True)
            string_units = data.get("string_units", False)
            imperial_units = data.get("imperial_units", False)
            foundation_foods = data.get("foundation_foods", True)
            optimistic_cache_reset = data.get("optimistic_cache_reset", False)
            separate_names = data.get("separate_names", True)

            if optimistic_cache_reset:
                load_parser_model.cache_clear()

            parser_info = inspect_parser(
                sentence=sentence,
                discard_isolated_stop_words=discard_isolated_stop_words,
                expect_name_in_output=expect_name_in_output,
                string_units=string_units,
                imperial_units=imperial_units,
                foundation_foods=foundation_foods,
                separate_names=separate_names,
            )
            parsed = parser_info.PostProcessor.parsed
            marginals = get_all_marginals(parser_info)

            data_response = {
                "tokens": list(
                    zip(
                        parser_info.PostProcessor.tokens,
                        parser_info.PostProcessor.labels,
                        marginals,
                    )
                ),
                "name": parsed.name
                if parsed.name is not None
                else [IngredientText("", 0, 0)],
                "size": parsed.size
                if parsed.size is not None
                else IngredientText("", 0, 0),
                "amounts": amount_resolver(parsed.amount)
                if parsed.amount is not None
                else [],
                "preparation": parsed.preparation
                if parsed.preparation is not None
                else IngredientText("", 0, 0),
                "comment": parsed.comment
                if parsed.comment is not None
                else IngredientText("", 0, 0),
                "purpose": parsed.purpose
                if parsed.purpose is not None
                else IngredientText("", 0, 0),
                "foundation_foods": parsed.foundation_foods
                if parsed.foundation_foods is not None
                else [],
            }

            return jsonify(data_response)

        except Exception as ex:
            return jsonify_error(status=500, exception=ex)

    else:
        return jsonify_error(status=404)


@app.route("/labeller/preupload", methods=["POST"])
@cross_origin()
def preupload():
    """Endpoint for getting parsed sentences in prep for uploading new entries"""
    if request.method == "POST":
        data = request.json

        if data is None:
            return jsonify_error(status=404)

        try:
            sentences = data.get("sentences", [])
            data_response = []

            for sentence in sentences:
                parser_info = inspect_parser(sentence=sentence)
                data_response.append(
                    {
                        "id": "".join(
                            random.choice("0123456789ABCDEF") for _ in range(6)
                        ),
                        "sentence": sentence,
                        "tokens": list(
                            zip(
                                parser_info.PostProcessor.tokens,
                                parser_info.PostProcessor.labels,
                            )
                        ),
                    }
                )

            return jsonify(data_response)

        except Exception as ex:
            return jsonify_error(status=500, exception=ex)

    else:
        return jsonify_error(status=404)


@app.route("/labeller/available-sources", methods=["GET"])
@cross_origin()
def available_sources():
    """Endpoint for retrieving all sources from database"""

    if request.method == "GET":
        data_response = []

        try:
            with sqlite3.connect(
                SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES
            ) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(f"SELECT DISTINCT source FROM {SQL3_DATABASE_TABLE}")
                rows = cursor.fetchall()
                data_response = [source[0] for source in rows]

            conn.close()

            return jsonify(data_response)

        except Exception as ex:
            return jsonify_error(status=500, exception=ex)

    else:
        return jsonify_error(status=404)


@app.route("/labeller/save", methods=["POST"])
@cross_origin()
def labeller_save():
    """Endpoint for saving sentences to database"""

    if request.method == "POST":
        data = request.json

        if data is None:
            return jsonify_error(status=404)

        try:
            edited = []

            for item in data["edited"]:
                tkn, lbl = list(zip(*item["tokens"]))
                tkn = list(tkn)
                lbl = list(lbl)
                edited.append({**item, "tokens": tkn, "labels": lbl})

            removals = [item["id"] for item in data["removed"]]

            with sqlite3.connect(
                SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES
            ) as conn:
                cursor = conn.cursor()

                if edited and len(edited) != 0:
                    cursor.executemany(
                        f"""
                            UPDATE {SQL3_DATABASE_TABLE}
                            SET
                                sentence = :sentence,
                                tokens = :tokens,
                                labels = :labels
                            WHERE id = :id;
                        """,
                        edited,
                    )

                if removals and len(removals) != 0:
                    cursor.execute(
                        f"""
                        DELETE FROM {SQL3_DATABASE_TABLE}
                        WHERE id IN ({",".join(["?"] * len(removals))})
                        """,
                        tuple(removals),
                    )

                conn.commit()

            conn.close()
            data_response = {"success": True}

            return jsonify(data_response)

        except Exception as ex:
            return jsonify_error(status=500, exception=ex)

    else:
        return jsonify_error(status=404)


@app.route("/labeller/bulk-upload", methods=["POST"])
@cross_origin()
def labeller_bulk_upload():
    """Endpoint for saving entirely new sentences in bulk to database"""

    if request.method == "POST":
        data = request.json

        if data is None:
            return jsonify_error(status=404)

        try:
            bulk = []

            for item in data:
                tkn, lbl = list(zip(*item["tokens"]))
                tkn = list(tkn)
                lbl = list(lbl)
                item.pop("id")
                bulk.append(
                    {**item, "tokens": tkn, "labels": lbl, "sentence_split": []}
                )

            with sqlite3.connect(
                SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES
            ) as conn:
                cursor = conn.cursor()

                cursor.executemany(
                    f"""
                    INSERT INTO {SQL3_DATABASE_TABLE}
                    (source, sentence, tokens, labels, sentence_split)
                    VALUES
                    (:source, :sentence, :tokens, :labels, :sentence_split);
                    """,
                    bulk,
                )
                conn.commit()

            conn.close()
            data_response = {"success": True}

            return jsonify(data_response)

        except Exception as ex:
            return jsonify_error(status=500, exception=ex)

    else:
        return jsonify_error(status=404)


@app.route("/labeller/search", methods=["POST"])
@cross_origin()
def labeller_search():
    """Endpoint for applying selected filter to database and returning editable
    sentence."""
    if request.method == "POST":
        data = request.json

        if data is None:
            return jsonify_error(status=404)

        try:
            offset = data.get("offset", 0)
            sources = data.get("sources", [])
            labels = data.get("labels", [])
            sentence = data.get("sentence", "")
            whole_word = data.get("wholeWord", False)
            case_sensitive = data.get("caseSensitive", False)

            reserved_char_search = RESERVED_LABELLER_SEARCH_CHARS.search(sentence)
            reserved_char_match = (
                reserved_char_search.group() if reserved_char_search else None
            )

            if reserved_char_match == "==":
                # Search by ID
                ids_reserved = []
                ids_actual = [
                    ix.strip()
                    for ix in set(sentence[2:].split(","))
                    if ix.strip().isdigit() or is_valid_dotnum_range(ix.strip())
                ]

                for id_ in ids_actual:
                    if is_valid_dotnum_range(id_):
                        start, stop = id_.split("..")
                        ids_reserved.extend(range(int(start), int(stop) + 1))
                    elif id_.isdigit():
                        ids_reserved.append(int(id_))

                matches = id_search(ids_reserved)

            elif reserved_char_match in ["**", "~~"]:
                # Return all results
                matches = list_all_entries()

            else:
                # Search by user input string
                matches = string_search(
                    sentence, labels, sources, case_sensitive, whole_word
                )

            # Convert tokens field to required format for frontend
            matches = [
                {**m, "tokens": list(zip(m["tokens"], m["labels"]))} for m in matches
            ]
            data_response = {
                "data": matches[offset : offset + 250],
                "total": len(matches),
                "offset": offset,
            }
            return jsonify(data_response)

        except Exception as ex:
            return jsonify_error(status=500, exception=ex)

    else:
        return jsonify_error(status=404)


@app.route("/precheck", methods=["GET"])
@cross_origin()
def pre_check():
    """Endpoint to determine if requirements are met for the train feature
    Looks at requirements.txt files"""

    checks = {"passed": [], "failed": []}
    satisfied = True

    with open(MODEL_REQUIREMENTS, "r") as file:
        requirements = file.readlines()

    requirements = [
        req.strip()
        for req in requirements
        if req.strip() and not req.strip().startswith("-")
    ]

    for req in requirements:
        package_name, *version_spec = req.split(
            "=="
        )  # Handle exact version specification
        package_name = package_name.strip()

        try:
            # Check if package is installed
            dist = distribution(package_name)
            if version_spec:
                installed_version = dist.version
                if installed_version != version_spec[0]:
                    checks["failed"].append(f"{req}@{installed_version}")
                else:
                    checks["passed"].append(f"{req}")
            else:
                checks["passed"].append(f"{req}")
        except PackageNotFoundError:
            satisfied = False
            checks["failed"].append(f"{req}")

    data_response = {"checks": checks, "passed": satisfied}

    return jsonify(data_response)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
@cross_origin()
def catch_all(path):
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

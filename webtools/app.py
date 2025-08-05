#!/usr/bin/env python3

# {{DEFAULT}}
import traceback, json, sqlite3, sys, random, re
from importlib.metadata import distribution, PackageNotFoundError
from pathlib import Path
# {{LIBRARIES}}
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
# {{INTERNAL}}
sys.path.append("..") # force use of local, not system wide ingredient parser installed
from ingredient_parser.en._loaders import load_parser_model
from ingredient_parser import inspect_parser
from ingredient_parser.dataclasses import FoundationFood, IngredientAmount, IngredientText, ParserDebugInfo

# globals
parent_dir = Path(__file__).parent.parent
NPM_BUILD_DIRECTORY = 'build'
SQL3_DATABASE_TABLE = 'en'
SQL3_DATABASE = parent_dir / 'train/data/training.sqlite3'
MODEL_REQUIREMENTS = parent_dir / 'requirements-dev.txt'

# sqlite
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_converter("json", json.loads)

# flask
app = Flask(__name__, static_folder=NPM_BUILD_DIRECTORY, static_url_path="/")
cors = CORS(app)

# @lru_cache decorator reset on load
load_parser_model.cache_clear()

def error_response(status: int, message: str = ""):
    """Boilerplate for errors"""
    if status == 400:
        return jsonify({
            "status": 400,
            "error": 'Sorry, bad params',
            "message": None
        }), 400
    elif status == 404:
        return jsonify({
            "status": 404,
            "error": 'Sorry, resource not found',
            "message": None
        }), 404
    elif status == 500:
        return jsonify({
            "status": 404,
            "error": 'Sorry, api failed',
            "message": message
        }), 500
    else:
        return jsonify({
            "status": status,
            "error": 'Sorry, something failed',
            "message": None
        }), 500

def get_all_marginals(parser_info: ParserDebugInfo) -> list[dict[str, float]]:
    """
    Return marginals for each label for each token in sentence.
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



@app.route("/parser", methods=["POST"])
@cross_origin()
def parser():
    """Endpoint for testing and seeing results for the parser from a sentence"""

    if request.method == "POST":
        data = request.json

        if data is None:
            return error_response(status=404)

        try:
            sentence = data.get("sentence", "")
            discard_isolated_stop_words = data.get("discard_isolated_stop_words", False)
            expect_name_in_output = data.get("expect_name_in_output", False)
            string_units = data.get("string_units", False)
            imperial_units = data.get("imperial_units", False)
            foundation_foods = data.get("foundation_foods", False)
            optimistic_cache_reset = data.get("optimistic_cache_reset", False)

            if optimistic_cache_reset:
                load_parser_model.cache_clear()

            parser_info = inspect_parser(
                sentence=sentence,
                discard_isolated_stop_words=discard_isolated_stop_words,
                expect_name_in_output=expect_name_in_output,
                string_units=string_units,
                imperial_units=imperial_units,
                foundation_foods=foundation_foods
            )
            parsed = parser_info.PostProcessor.parsed
            marginals = get_all_marginals(parser_info)

            return jsonify({
                "tokens": list(zip(
                    parser_info.PostProcessor.tokens,
                    parser_info.PostProcessor.labels,
                    marginals,
                )),
                "name": parsed.name if parsed.name is not None else [IngredientText("", 0,0)],
                "size": parsed.size if parsed.size is not None else IngredientText("", 0,0),
                "amounts": [
                    IngredientAmount(quantity=str(amount.quantity), quantity_max=str(amount.quantity_max), text=amount.text, confidence=amount.confidence, starting_index=amount.starting_index, unit=str(amount.unit), APPROXIMATE=amount.APPROXIMATE, SINGULAR=amount.SINGULAR, RANGE=amount.RANGE, MULTIPLIER=amount.MULTIPLIER, PREPARED_INGREDIENT=amount.PREPARED_INGREDIENT) for amount in parsed.amount
                ] if parsed.amount is not None else [],
                "preparation": parsed.preparation if parsed.preparation is not None else IngredientText("", 0,0),
                "comment": parsed.comment if parsed.comment is not None else IngredientText("", 0,0),
                "purpose": parsed.purpose if parsed.purpose is not None else IngredientText("", 0,0),
                "foundation_foods": [
                    FoundationFood(text=food.text, confidence=food.confidence, fdc_id=food.fdc_id,category=food.category, data_type=food.data_type) for food in parsed.foundation_foods
                ] if parsed.foundation_foods is not None else [],
            })

        except Exception as ex:
            traced = ''.join(traceback.TracebackException.from_exception(ex).format())
            return error_response(status=500, message=traced)

    else:
        return error_response(status=404)

@app.route("/labeller/preupload", methods=["POST"])
@cross_origin()
def preupload():
    """Endpoint for getting parsed sentences in prep for uploading new entries"""
    if request.method == "POST":
        data = request.json

        if data is None:
            return error_response(status=404)

        try:
            sentences = data.get("sentences", [])
            collector = []

            for sentence in sentences:
                parser_info = inspect_parser(sentence=sentence)
                collector.append({
                    "id": ''.join(random.choice('0123456789ABCDEF') for _ in range(6)),
                    "sentence": sentence,
                    "tokens": list(zip(
                        parser_info.PostProcessor.tokens,
                        parser_info.PostProcessor.labels
                    ))
                })

            return jsonify(collector)

        except Exception as ex:
            traced = ''.join(traceback.TracebackException.from_exception(ex).format())
            return error_response(status=500, message=traced)

    else:
        return error_response(status=404)

@app.route("/labeller/available-sources", methods=["GET"])
@cross_origin()
def available_sources():
    if request.method == "GET":

        available_sources = []

        try:
            with sqlite3.connect(SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:

                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """SELECT DISTINCT source FROM en"""
                )
                rows = cursor.fetchall()
                available_sources = [source[0] for source in rows]

            conn.close()

            return jsonify(available_sources)

        except Exception as ex:
            traced = ''.join(traceback.TracebackException.from_exception(ex).format())
            return error_response(status=500, message=traced)

    else:
        return error_response(status=404)

@app.route("/labeller/save", methods=["POST"])
@cross_origin()
def labeller_save():
    """Endpoint for saving sentences to database"""

    if request.method == "POST":
        data = request.json

        if data is None:
            return error_response(status=404)

        try:
            edited = []

            for item in data["edited"]:
                tkn, lbl = list(zip(*item["tokens"]))
                tkn = list(tkn)
                lbl = list(lbl)
                edited.append({**item, "tokens": tkn, "labels": lbl})

            removals = []

            for item in data["removed"]:
                removals.append(item["id"])

            with sqlite3.connect(SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
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
                        WHERE id IN ({','.join(['?']*len(removals))})
                        """,
                        tuple(removals),
                    )

                conn.commit()

            conn.close()

            return jsonify({ "success": True })

        except Exception as ex:
            traced = ''.join(traceback.TracebackException.from_exception(ex).format())
            print(traced)
            return error_response(status=500, message=traced)

    else:
        return error_response(status=404)

@app.route("/labeller/bulk-upload", methods=["POST"])
@cross_origin()
def labeller_bulk_upload():
    """Endpoint for saving entirely new sentences in bulk to database"""

    if request.method == "POST":
        data = request.json

        if data is None:
            return error_response(status=404)

        try:
            bulk = []

            for item in data:
                tkn, lbl = list(zip(*item["tokens"]))
                tkn = list(tkn)
                lbl = list(lbl)
                item.pop("id")
                bulk.append({**item, "tokens": tkn, "labels": lbl, "sentence_split": [] })


            with sqlite3.connect(SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                cursor = conn.cursor()

                cursor.executemany(
                    f"""
                    INSERT INTO {SQL3_DATABASE_TABLE} (source, sentence, tokens, labels, sentence_split)
                    VALUES (:source, :sentence, :tokens, :labels, :sentence_split);
                    """,
                    bulk,
                )
                conn.commit()

            conn.close()

            return jsonify({ "success": True })

        except Exception as ex:
            traced = ''.join(traceback.TracebackException.from_exception(ex).format())
            return error_response(status=500, message=traced)

    else:
        return error_response(status=404)

@app.route("/labeller/search", methods=["POST"])
@cross_origin()
def labeller_search():
    """Endpoint for applying selected filter to database and returning editable sentences that match the filter. TODO: Some skilled SQLite queries should be used for better readibility and performance"""

    if request.method == "POST":
        data = request.json

        if data is None:
            return error_response(status=404)

        try:

            with sqlite3.connect(SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                offset = data.get("offset", 0)
                sources = data.get("sources", [])
                labels = data.get("labels", [])
                sentence = data.get("sentence", "")
                whole_word = data.get("wholeWord", False)
                case_sensitive = data.get("caseSensitive",False)

                # reserve ** or ~~ for wildcard, treat as empty string
                sentence = " " if re.search(r"\*\*|~~", sentence) else sentence

                escaped = re.escape(sentence)

                if whole_word:
                    expression = rf"\b{escaped}\b"
                else:
                    expression = escaped

                if case_sensitive:
                    query = re.compile(expression, re.UNICODE)
                else:
                    query = re.compile(expression, re.UNICODE | re.IGNORECASE)

                cursor.execute(
                    f"""
                    SELECT *
                    FROM {SQL3_DATABASE_TABLE}
                    WHERE source IN ({','.join(['?']*len(sources))})
                    """,
                    (sources),
                )
                rows = cursor.fetchall()

                indices = []

                for row in rows:

                    if len(labels) == 9:
                        if query.search(row["sentence"]):
                            indices.append(row["id"])
                    else:
                        partial_sentence = " ".join(
                            [
                                tok
                                for tok, label in list(zip(row["tokens"], row["labels"]))
                                if label in labels
                            ]
                        )
                        if query.search(partial_sentence):
                            indices.append(row["id"])

                batch_size = 250 # SQLite has a default limit of 999 parameters
                rows = []
                for i in range(0, len(indices), batch_size):
                    batch = indices[i:i + batch_size]
                    cursor.execute(
                        f"""
                        SELECT *
                        FROM en
                        WHERE id IN ({','.join(['?']*len(batch))})
                        """,
                        (batch),
                    )
                    rows += cursor.fetchall()

                data = []
                for row in rows:
                    data.append({
                        **row,
                        "tokens": list(zip(row["tokens"], row["labels"]))
                    })

                batch_size = 999 # SQLite has a default limit of 999 parameters
                count = []
                for i in range(0, len(indices), batch_size):
                    batch = indices[i:i + batch_size]
                    cursor.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM en
                        WHERE id IN ({','.join(['?']*len(batch))})
                        """,
                        (batch),
                    )
                    count += [cursor.fetchone()[0]]

                final = dict({
                    "data": data[offset:offset+250],
                    "total": sum(count),
                    "offset": offset
                })


            conn.close()

            return jsonify(final)

        except Exception as ex:
            traced = ''.join(traceback.TracebackException.from_exception(ex).format())
            return error_response(status=500, message=traced)

    else:
        return error_response(status=404)


@app.route('/precheck', methods=["GET"])
@cross_origin()
def pre_check():
    """Endpoint for a precheck to determine if the 'train model' feature should be available on the web tool; looks at requirements.txt files"""

    checks = { "passed": [], "failed": [] }
    satisfied = True

    with open(MODEL_REQUIREMENTS, 'r') as file:
        requirements = file.readlines()

    requirements = [
        req.strip() for req in requirements
        if req.strip() and not req.strip().startswith('-')
    ]

    for req in requirements:
        package_name, *version_spec = req.split('==')  # Handle exact version specification
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

    return jsonify({ "checks": checks, "passed": satisfied })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@cross_origin()

def catch_all(path):
    return app.send_static_file("index.html")

if __name__ == '__main__':
    app.run(port=5000, debug=True)

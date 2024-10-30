#!/usr/bin/env python3

import traceback, json, sqlite3, time, subprocess, json, random, logging, re
from importlib.metadata import distribution, PackageNotFoundError
from pathlib import Path
from flask import Flask, Response, jsonify, request
from flask_cors import CORS, cross_origin
from flask_sock import Sock
from ingredient_parser import inspect_parser
from ingredient_parser.dataclasses import IngredientText, ParserDebugInfo

parent_dir = Path(__file__).parent.parent

NPM_BUILD_DIRECTORY = 'build'
SQL3_DATABASE = parent_dir / 'train/data/training.sqlite3'
MODEL_REQUIREMENTS = parent_dir / 'requirements-dev.txt'

sqlite3.register_adapter(list, json.dumps)
sqlite3.register_converter("json", json.loads)

app = Flask(__name__, static_folder=NPM_BUILD_DIRECTORY, static_url_path="/")
cors = CORS(app)
sock = Sock(app)

logging.basicConfig(level=logging.INFO)

def error_response(status: int, message: str = ""):
    """
    Boilerplate for errors
    """
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
        "NAME",
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
    """
    Endpoint for testing and seeing results for the parser from a sentence
    """
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

            parser_info = inspect_parser(
                sentence=sentence,
                discard_isolated_stop_words=discard_isolated_stop_words,
                expect_name_in_output=expect_name_in_output,
                string_units=string_units,
                imperial_units=imperial_units,
                foundation_foods=foundation_foods
            )
            parsed = parser_info.PostProcessor.parsed
            parsed.foundation_foods = parser_info.foundation_foods
            marginals = get_all_marginals(parser_info)

            return jsonify({
                "tokens": list(zip(
                    parser_info.PostProcessor.tokens,
                    parser_info.PostProcessor.labels,
                    marginals,
                )),
                "name": parsed.name if parsed.name is not None else IngredientText("", 0),
                "size": parsed.size if parsed.size is not None else IngredientText("", 0),
                "amounts": [IngredientText(text=amount.text, confidence=amount.confidence) for amount in parsed.amount] if parsed.amount is not None else [],
                "preparation": parsed.preparation if parsed.preparation is not None else IngredientText("", 0),
                "comment": parsed.comment if parsed.comment is not None else IngredientText("", 0),
                "purpose": parsed.purpose if parsed.purpose is not None else IngredientText("", 0),
                "foundation_foods": [IngredientText(text=food.text, confidence=food.confidence) for food in parsed.foundation_foods] if parsed.foundation_foods is not None else [],
            })

        except Exception as ex:
            traced = ''.join(traceback.TracebackException.from_exception(ex).format())
            return error_response(status=500, message=traced)

    else:
        return error_response(status=404)

@app.route("/labeller/preupload", methods=["POST"])
@cross_origin()
def preupload():
    """
    Endpoint for getting parsed sentences in prep for uploading new entries
    """
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
                    "id": ''.join(random.choice('0123456789ABCDEF') for _ in range(4)),
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

@app.route("/labeller/save", methods=["POST"])
def labeller_save():
    """
    Endpoint for saving sentences to database
    """
    if request.method == "POST":
        data = request.json

        if data is None:
            return error_response(status=404)

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

            if edited:
                cursor.executemany(
                    """UPDATE en
                    SET
                    sentence = :sentence,
                    tokens = :tokens,
                    labels = :labels,
                    foundation_foods = :foundation_foods
                    WHERE id = :id;""",
                    edited,
                )

            if removals:
                cursor.execute(
                    f"""
                    DELETE FROM en
                    WHERE id IN ({','.join(['?']*len(removals))})
                    """,
                    (removals),
                )
        conn.close()

        return jsonify({ "test": 1 })

    else:
        return error_response(status=404)

@app.route("/labeller/search", methods=["POST"])
def labeller_search():
    """
    Endpoint for applying selected filter to database and returning editable sentences that match the filter.

    TODO: Some skilled SQLite queries should be used for better readibility and performance
    """

    if request.method == "POST":
        data = request.json

        if data is None:
            return error_response(status=404)

        with sqlite3.connect(SQL3_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            offset = data.get("offset", 0)
            sources = data.get("sources", [])
            labels = data.get("labels", [])
            sentence = data.get("sentence", "")
            whole_word = data.get("wholeWord", False)
            case_sensitive = data.get("caseSensitive",False)

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
                FROM en
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

    else:
        return error_response(status=404)


@app.route('/train/precheck')
def pre_check():
    """
    Endpoint for a precheck to determine if the 'train model' feature should be available on the web tool; looks at requirements.txt files
    """

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

@sock.route('/echo')
def echo(ws):
    """
    Endpoint for testing basic websockets with comms between webtool and server to trigger and monitor processed

    TODO: Needs a little TLC and engineering perspective before deciding best approach
    """

    while True:

        data = ws.receive()
        msg = data.strip()

        if msg == 'connection':
            ws.send(json.dumps({"status":"successfully connected", "output": None }))

        elif msg == 'train':

            proc = subprocess.Popen(
                #["python3.12", "train.py", "train", "--model", "parser", "--database", "train/data/training.sqlite3"],
                ['bash', '-c', 'for i in {1..5}; do echo "Current time: $(date)"; sleep 1; done'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )

            while proc.poll() is None:

                data = ws.receive()
                msg = data.strip()

                if msg == 'check' or msg == 'train':
                    ws.send(json.dumps({"status":"training in progress", "output": None }))

                elif msg == 'interrupt':
                    subprocess.call(['kill', str(proc.pid)])
                    ws.send(json.dumps({"status":"interrupted", "output": None }))


            stdout, stderr = proc.communicate()

            if stderr.decode('utf-8') == '':
                ws.send(json.dumps({
                    "status": "done",
                    "output": stdout.decode('utf-8').splitlines()
                }))
            else:
                ws.send(json.dumps({
                    "status": "done",
                    "output": stderr.decode('utf-8').splitlines()
                }))


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@cross_origin()
def catch_all(path):
    return app.send_static_file("index.html")

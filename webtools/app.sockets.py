#!/usr/bin/env python3

# {{DEFAULT}}
import argparse
import contextlib
import io
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from random import randint
from threading import Event, Lock, Thread
from typing import Any, Dict, TextIO

# {{FLASK|SOCKETS}}
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# {{INTERNAL}}
sys.path.append("..")  # force use of local, not system wide ingredient parser installed
from train import (
    grid_search,
    set_redirect_log_stream,
    set_temp_working_directory,
    train_multiple,
    train_single,
)

# globals
parent_dir = Path(__file__).parent.parent
NPM_BUILD_DIRECTORY = "build"
SQL3_DATABASE = parent_dir / "train/data/training.sqlite3"
SAVED_MODEL = parent_dir / "ingredient_parser/en/data/model.en.crfsuite"
MODEL_REQUIREMENTS = parent_dir / "requirements-dev.txt"

# flask
app = Flask(__name__, static_folder=NPM_BUILD_DIRECTORY, static_url_path="/")
cors = CORS(app)

# logging for app_sockets.py
logger = logging.getLogger(__name__)

# flask socket-io
#
# Set async_mode to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(
    app, async_mode=async_mode, async_handlers=True, cors_allowed_origins="*"
)  # path='/trainer', logger=True, engineio_logger=True
thread = None
thread_native_id = 0
thread_lock = Lock()
thread_event = Event()


def safe_json_load(json_string: str) -> Dict[str, Any]:
    """
    Safely loads a JSON string and returns the JSON dictionary
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return {}


def background_thread(thread_event, input_data):
    """Background thread for training behind web sockets"""

    try:
        args = {}
        task = input_data.get("task", None)
        is_verbose = input_data.get("debugLevel", 0)

        if task == "gridsearch":
            algos_global_params = input_data.get("algosGlobalParams", "{}")
            algos_ap_params = input_data.get("algosAPParams", "{}")
            algos_pa_params = input_data.get("algosPAParams", "{}")
            algos_lbfgs_params = input_data.get("algosLBFGSParams", "{}")
            algos_arow_params = input_data.get("algosAROWParams", "{}")
            algos_l2sgd_params = input_data.get("algosL2SGDParams", "{}")

            args = {
                "database": str(SQL3_DATABASE),
                "table": "en",
                "datasets": input_data["sources"],
                "save_model": str(SAVED_MODEL),
                "split": input_data.get("split", 0.2),
                "seed": input_data.get("seed", randint(0, 1_000_000_000)),
                "processes": input_data.get("processes", os.cpu_count() - 1),
                "combine_name_labels": input_data.get("combineNameLabels", False)
                or None,
                "algos": input_data.get("algos", ["lbfgs"]),
                "keep_models": False,
                "global_params": safe_json_load(algos_global_params),
                "lbfgs_params": safe_json_load(algos_lbfgs_params),
                "ap_params": safe_json_load(algos_ap_params),
                "l2sgd_params": safe_json_load(algos_l2sgd_params),
                "pa_params": safe_json_load(algos_pa_params),
                "arow_params": safe_json_load(algos_arow_params),
            }
        elif task == "training":
            args = {
                "database": str(SQL3_DATABASE),
                "table": "en",
                "datasets": input_data["sources"],
                "save_model": str(SAVED_MODEL),
                "split": input_data.get("split", 0.2),
                "seed": input_data.get("seed", randint(0, 1_000_000_000)),
                "html": input_data.get("html", False) or None,
                "detailed": input_data.get("detailed", False) or None,
                "confusion": input_data.get("confusion", False) or None,
                "combine_name_labels": input_data.get("combineNameLabels", False)
                or None,
            }

            if (
                input_data["task"] == "training"
                and input_data["runsCategory"] == "multiple"
                and input_data["runs"] >= 1
            ):
                args = {
                    **args,
                    "runs": input_data.get("runs", 1),
                    "processes": input_data.get("processes", os.cpu_count() - 1),
                }
        else:
            raise Exception(
                "Input task needs to be supplied, either training or gridsearch"
            )

        def monitor_stdout(output_buffer: TextIO, interval=0.1):
            """Monitors the output buffer for new content"""
            if isinstance(output_buffer, StringIO):
                last_position = 0
                while True:
                    time.sleep(interval)
                    current_output = str(output_buffer.getvalue())
                    if len(current_output) > last_position:
                        new_output = current_output[last_position:]
                        if thread_event.is_set():
                            socketio.emit(
                                "trainer",
                                {
                                    "data": [
                                        ln.strip() for ln in new_output.splitlines()
                                    ],
                                    "indicator": "Logging",
                                    "message": "",
                                },
                            )
                        last_position = len(current_output)

        captured_output = io.StringIO()
        monitor_thread = Thread(
            target=monitor_stdout,
            args=(captured_output,),
        )
        monitor_thread.daemon = (
            True  # allow the main thread to exit even if this is running
        )
        monitor_thread.start()

        logging.basicConfig(
            stream=captured_output,
            level=(logging.DEBUG if is_verbose else logging.INFO),
            format="[%(levelname)s] (%(module)s) %(message)s",
        )

        with set_redirect_log_stream(captured_output):
            with contextlib.redirect_stdout(captured_output):
                logger.debug(
                    f"{input_data['task'].capitalize()} requested"
                    f" @ {datetime.now().strftime('%H:%M:%S')} on PID {os.getpid()}"
                )
                logger.debug(
                    f"{input_data['task'].capitalize()} inputs "
                    f" {', '.join([f'{k}={v}' for k, v in args.items()])}"
                )

                start_time = time.monotonic()

                with set_temp_working_directory(parent_dir):
                    if (
                        input_data["task"] == "training"
                        and input_data["runsCategory"] == "multiple"
                    ):
                        train_multiple(argparse.Namespace(**args))
                    elif (
                        input_data["task"] == "training"
                        and input_data["runsCategory"] == "single"
                    ):
                        train_single(argparse.Namespace(**args))
                    elif input_data["task"] == "gridsearch":
                        grid_search(argparse.Namespace(**args))
                period_time = time.monotonic() - start_time
                period_seconds = timedelta(seconds=int(period_time)).total_seconds()

                logger.debug(
                    f"{input_data['task'].capitalize()} ended"
                    f" @ {datetime.now().strftime('%H:%M:%S')} on PID {os.getpid()}"
                )
                logger.debug(
                    f"Took approximately"
                    f" {int(period_seconds // 60)}mins {int(period_seconds % 60)}s"
                )

                time.sleep(1)  # allow buffer time to readout final output

        socketio.emit(
            "status",
            {
                "data": [],
                "indicator": "Completed",
                "message": "Training round completed. View console output for results.",
            },
        )

        monitor_thread.join()

    except Exception as e:
        socketio.emit(
            "status",
            {
                "data": [],
                "indicator": "Error",
                "message": "Training round encountered an issue. {}".format(str(e)),
            },
        )

    finally:
        thread_event.clear()


@socketio.on("train")
def train_start(input_data):
    """Web socket receives request to start the training"""
    global thread
    global thread_native_id
    with thread_lock:
        thread_event.set()
        thread = socketio.start_background_task(
            background_thread, thread_event, input_data
        )
        thread_native_id = thread.native_id
        emit(
            "status",
            {
                "data": [],
                "indicator": "Running",
                "message": "Training started",
            },
        )


@socketio.on("connect")
def connect():
    """Web socket sends comms to connect"""
    emit("status", {"data": [], "indicator": "Connected", "message": ""})


@socketio.on("disconnect")
def disconnect():
    """Web socket sends comms to disconnect"""

    global thread_event
    global thread
    global thread_native_id

    emit("status", {"data": [], "indicator": "Disconnected", "message": ""})

    thread_event.clear()
    thread = None
    thread_native_id = None


if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=5001)

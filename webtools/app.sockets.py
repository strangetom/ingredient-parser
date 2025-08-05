#!/usr/bin/env python3

# {{DEFAULT}}
import argparse, time, sys, io, contextlib, os
from datetime import datetime
from threading import Event, Thread
from pathlib import Path
from random import randint
from threading import Lock
# {{FLASK|SOCKETS}}
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
# {{INTERNAL}}
sys.path.append("..") # force use of local, not system wide ingredient parser installed
from train import train_single

# globals
parent_dir = Path(__file__).parent.parent
NPM_BUILD_DIRECTORY = 'build'
SQL3_DATABASE = parent_dir / 'train/data/training.sqlite3'
SAVED_MODEL = parent_dir / 'ingredient_parser/en/model.en.crfsuite'
MODEL_REQUIREMENTS = parent_dir / 'requirements-dev.txt'

# flask
app = Flask(__name__, static_folder=NPM_BUILD_DIRECTORY, static_url_path="/")
cors = CORS(app)

# flask socket-io
#
# Set async_mode to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode, async_handlers=True, cors_allowed_origins="*") # path='/trainer', logger=True, engineio_logger=True
thread = None
thread_native_id = 0
thread_lock = Lock()
thread_event = Event()

def background_thread(thread_event, input_data):
    """Background thread for training behind web sockets"""

    try:
        if not input_data["sources"] and not input_data["model"]:
            raise Exception("Input data sources and model need to be supplied")

        args = {
            'database': str(SQL3_DATABASE),
            'table': 'en',
            'datasets': input_data["sources"],
            'model': input_data["model"],
            'save_model': str(SAVED_MODEL),
            'split': input_data.get("split", 0.2),
            'seed': input_data.get("seed", randint(0, 1_000_000_000)),
            'html': input_data.get("html", False) or None,
            'detailed': input_data.get("detailed", False) or None,
            'confusion': input_data.get("confusion", False) or None
        }

        def monitor_stdout(output_buffer, interval=0.1):
            """Monitors the output buffer for new content"""
            last_position = 0
            while True:
                time.sleep(interval)
                current_output = str(output_buffer.getvalue())
                if len(current_output) > last_position:
                    new_output = current_output[last_position:]
                    if thread_event.is_set():
                        socketio.emit('trainer', {
                            'data': [ln.strip() for ln in new_output.splitlines()],
                            'indicator': 'Logging',
                            'message': ''
                        })
                    last_position = len(current_output)


        captured_output = io.StringIO()
        monitor_thread = Thread(target=monitor_stdout, args=(captured_output,),)
        monitor_thread.daemon = True  # allow the main thread to exit even if this is running
        monitor_thread.start()

        with contextlib.redirect_stdout(captured_output):
            print(
                "------------------------------\n TRAINING STARTED [time={}] [pid={}] \n------------------------------\n INPUTS \n{} ------------------------------\n"
                .format(datetime.now().strftime('%H:%M:%S'), os.getpid(), ''.join([f'[{k}={v}] \n' for k, v in args.items()]))
            )
            train_single(argparse.Namespace(**args))
            print(
                "------------------------------\n TRAINING ENDED [time={}] [pid={}] \n------------------------------\n"
                .format(datetime.now().strftime('%H:%M:%S'), os.getpid())
            )
            time.sleep(1) # allow buffer time to readout final output

        socketio.emit('status', {
            'data': [],
            'indicator': 'Completed',
            'message': 'Training round completed. View console output for results.'
        })

        monitor_thread.join()

    except Exception as e:
        socketio.emit('status', {
            'data': [],
            'indicator': 'Error',
            'message': 'Training round encountered an issue. {}'.format(str(e))
        })

    finally:
        thread_event.clear()

@socketio.on('train')
def train_start(input_data):
    """Web socket receives request to start the training"""
    global thread
    global thread_native_id
    with thread_lock:
        thread_event.set()
        thread = socketio.start_background_task(background_thread, thread_event, input_data)
        thread_native_id = thread.native_id
        emit('status', {
            'data': [],
            'indicator': 'Training',
            'message': 'Training started (PID = {})'.format(os.getpid())
        })

'''
@socketio.on('interrupt')
def train_interrupted(data):
    """Web socket receives request to cancel — killing Python threading is discouraged, see https://docs.python.org/3/library/threading.html"""
    global thread
    global thread_native_id
    with thread_lock:
        if thread is not None:
            thread_event.clear()
            emit('status', {
                'data': [],
                'indicator': 'Interrupted',
                'message': 'Be aware that interupting the training will not terminate the process due to how threading works (PID = {})'.format(os.getpid())
            })
            thread.join()
            thread = None
            thread_native_id = None
'''

@socketio.on('connect')
def connect():
    """Web socket sends comms to connect"""
    emit('status', {
        'data': [],
        'indicator': 'Connected',
        'message': ''
    })

@socketio.on('disconnect')
def disconnect():
    """Web socket sends comms to disconnect"""

    global thread_event
    global thread
    global thread_native_id

    emit('status', {
        'data': [],
        'indicator': 'Disconnected',
        'message': ''
    })

    thread_event.clear()
    thread = None
    thread_native_id = None

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=5001)

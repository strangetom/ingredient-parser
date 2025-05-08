#!/usr/bin/env python3

# {{DEFAULT}}
import argparse, time, sys, io, contextlib
from threading import Event, Thread
from pathlib import Path
# {{LIBRARIES}}
from flask import Flask
from flask_cors import CORS
from threading import Lock
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
thread_lock = Lock()
thread_event = Event()

def background_thread(thread_event):
    """Background thread for training behind web sockets"""

    global thread

    try:

            args = {
                'database': str(SQL3_DATABASE),
                'table': 'en',
                'datasets': ["bbc", "cookstr", "nyt", "allrecipes", "tc"],
                'model': 'parser',
                'save_model': str(SAVED_MODEL),
                'split': 0.20,
                'seed': None,
                'html': None,
                'detailed': None,
                'confusion': None
            }

            def monitor_stdout(output_buffer, interval=0.1):
                """Monitors the output buffer for new content and calls my_function."""
                last_position = 0
                while True:
                    time.sleep(interval)
                    current_output = str(output_buffer.getvalue())
                    if len(current_output) > last_position:
                        new_output = current_output[last_position:]
                        if thread_event.is_set():
                            socketio.emit('trainer', {'data': [ln.strip() for ln in new_output.splitlines()], 'indicator': 'Logging', 'message': '' })
                        last_position = len(current_output)


            captured_output = io.StringIO()

            # Start the monitoring thread
            monitor_thread = Thread(target=monitor_stdout, args=(captured_output,),)
            monitor_thread.daemon = True  # Allow the main thread to exit even if this is running
            monitor_thread.start()

            with contextlib.redirect_stdout(captured_output):
                train_single(argparse.Namespace(**args))
                print("end 1")

            print("end 2")

            socketio.emit('status', {'data': [], 'indicator': 'Completed', 'message': ''})

    except Exception as e:
        socketio.emit('status', {'data': [], 'indicator': 'Error', 'message': e})

    finally:
        thread_event.clear()
        thread = None

@socketio.on('train')
def train_start(data):
    """Web socket receives request to start the training"""
    global thread
    global thread_native_id
    with thread_lock:
        if thread is None:
            thread_event.set()
            thread = socketio.start_background_task(background_thread, thread_event)
            thread_native_id = thread.native_id
            emit('status', {'data': [], 'indicator': 'Training', 'message': 'Thread ID is {}'.format(thread_native_id) })

@socketio.on('interrupt')
def train_interrupted(data):
    """Web socket receives request to cancel — killing Python threading is discouraged, see https://docs.python.org/3/library/threading.html"""
    global thread
    global thread_native_id
    thread_event.clear()
    with thread_lock:
        if thread is not None:
            emit('status', {'data': [], 'indicator': 'Interrupted', 'message': 'Be aware that interupting the training will not terminate the process due to how threading works (thread ID ={})'.format(thread_native_id) })
            thread.join()
            thread = None
            thread_native_id = None

@socketio.on('connect')
def connect():
    """Web socket sends comms to connect"""
    emit('status', {'data': [], 'indicator': 'Connected', 'message': '' })

@socketio.on('disconnect')
def disconnect():
    """Web socket sends comms to disconnect"""
    emit('status', {'data': [], 'indicator': 'Disconnected', 'message': ''})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)

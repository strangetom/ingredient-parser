#!/usr/bin/env python3

import subprocess, os, sys, time
from subprocess import Popen, PIPE
from flask import Flask

class color: # ASCII text color
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

class bgcolor: #ASCII background color
    BLACK = "\033[40m"
    RED = "\033[41m"
    GREEN = "\033[42m"
    YELLOW = "\033[43m"
    BLUE = "\033[44m"
    MAGENTA = "\033[45m"
    CYAN = "\033[46m"
    WHITE = "\033[47m"

app = Flask(__name__)

def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor

spinner = spinning_cursor()

def spin():
    for _ in range(50):
        sys.stdout.write(color.YELLOW + next(spinner) + color.RESET)
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')

def notice(msg):
    sys.stdout.write(color.GREEN + msg + color.RESET + '\n')

def alert(msg):
    sys.stdout.write(color.RED + msg + color.RESET + '\n')

def log(msg):
    sys.stdout.write(color.WHITE + msg + color.RESET + '\n')

@app.cli.command("cook")
def cook():

    try:

        with Popen(
            ['npm', 'install', '--quiet'],
            stdout=subprocess.DEVNULL,
            bufsize=1,
            universal_newlines=True,
            cwd="./webtools"
        ) as proc:

            while proc.poll() is None:
                spin()

            if proc.returncode == 0:
               notice(":: NPM packages installed ::")

    except subprocess.CalledProcessError as err:
        alert(":: NPM error ::" + "\n\n" + err.stderr)
        return

    try:

        with Popen(
            ['npx', 'vite', 'build'],
            stdout=subprocess.DEVNULL,
            bufsize=1,
            universal_newlines=True,
            cwd="./webtools"
        ) as proc:

            while proc.poll() is None:
                spin()

            if proc.returncode == 0:
                notice(":: Bundled and built React/Typescript @ Vite ::")

    except subprocess.CalledProcessError as err:
        alert(":: NPM Vite error ::" + "\n\n" + err.stderr)
        return

    env = os.environ.copy()
    env["FLASK_APP"] = 'webtools/app.py'

    with Popen(
        ['flask', 'run', '--debug'],
        stdout=PIPE,
        bufsize=1,
        universal_newlines=True,
        env=env
    ) as proc:

        try:

            notice(":: Running Flask server ::")

            while proc.stdout is not None:
                for line in proc.stdout:
                    log(line)

        except subprocess.CalledProcessError as err:
            alert(":: Flask error ::" + "\n\n" + err.stderr)
            return

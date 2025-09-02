.. _reference-tutorials-web-app:

Web App
=======

The ingredient parser library provides a convenient web interface that you can run locally to access most of the library's functionality. The web app (**webtools**), supports basic workflow needs, namely:

* Testing and using the trained parser (a.k.a. :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>`)
* Browsing the ingredient training database (:ref:`view data/labels page <reference-explanation-data>`)
* Labeling ingredient training entries (:ref:`view data/labels page <reference-explanation-data>`)
* Training and tuning the parser (a.k.a. :func:`train_single <train.train_single>`, :func:`train_multiple <train.train_multiple>`, :func:`grid_search <train.grid_search>`)

Requirements and Setup
~~~~~~~~~~~~~~~~~~~~~~~~

To run the **webtools**, install all python libraries in ``requirements-dev.txt``. Next, install `Node <https://nodejs.org/en/download>`_, the Javascript runtime, on your machine. Lastly, navigate to the ``webtools`` directory and run the following commands:

.. code:: bash

    $ npm install
    $ npm run dev


Screenshots
~~~~~~~~~~~~~

.. grid:: 1 2 2 3

    .. grid-item::

        .. figure:: /_static/webtools/app.parser.screenshot.png
            :alt: Webtools parser screenshot

    .. grid-item::

        .. figure:: /_static/webtools/app.labeller.screenshot.png
            :alt: Webtools labeller screenshot

    .. grid-item::

        .. figure:: /_static/webtools/app.trainer.screenshot.png
            :alt: Webtools trainer screenshot

Tech Stack
~~~~~~~~~~~~~

The web technology stack (packages, libraries, & tooling) includes:
`Typescript <https://www.typescriptlang.org/>`_, `React <https://react.dev/>`_, `Mantine <https://mantine.dev/>`_, `Zustand <https://zustand-demo.pmnd.rs/>`_, `Vite <https://vite.dev>`_, `BiomeJS <https://vite.dev>`_, `Socket.IO <https://socket.io>`_, `Flask <https://flask.palletsprojects.com/en/stable/>`_, `Flask-SocketIO <https://flask-socketio.readthedocs.io/en/latest/>`_, and `Flask-CORS <https://corydolphin.com/flask-cors/>`_ (subject to change; only for informational purposes)

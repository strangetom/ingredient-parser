.. _reference-tutorials-webtools:

Webtools
========

The ingredient parser library provides a convenient web interface that you can run locally to access most of the library's functionality for testing and development purposes.
The web app (**webtools**) supports basic workflow needs, namely:

* Testing and using the trained parser (a.k.a. :func:`parse_ingredient <ingredient_parser.parsers.parse_ingredient>`)
* Browsing the ingredient sentence training database (see :ref:`Explanation/Training data <reference-explanation-data>`)
* Editing the labels of ingredient sentence training entries (see :ref:`Explanation/Training data <reference-explanation-data>`)
* Training and tuning the parser (a.k.a. :func:`train_single <train.train_single>`, :func:`train_multiple <train.train_multiple>`, :func:`grid_search <train.grid_search>`)

  * ``train_single`` trains a model using the provided hyper-parameters and outputs the model accuracy statistics.
  * ``train_multiple`` trains multiple models using different random seeds values and outputs the aggregated accuracy statistics.
  * ``grid_search`` trains multiple models using different hyper-parameters and outputs the accuracy statistics for each set of hyper-parameters.

Requirements and Setup
~~~~~~~~~~~~~~~~~~~~~~~~

To run the **webtools**, clone the repository and install all python libraries in ``requirements-dev.txt``.
Next, install `Node <https://nodejs.org/en/download>`_, a Javascript runtime, on your machine.
Lastly, navigate to the ``webtools`` directory and install using ``npm``:

.. code:: bash

    # Clone repository
    $ git clone https://github.com/strangetom/ingredient-parser.git
    $ cd ingredient-parser

    # Create venv and install required packages
    $ python -m venv venv
    $ source venv/bin/activate
    $ python -m pip install -r requirements-dev.txt

    # Install webtools
    $ cd webtools
    $ npm install
    $ npm run dev

The **webtools** can be accessed at http://localhost:5000 in your browser.

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

The web technology stack (packages, libraries, and tooling) includes:

* `Typescript <https://www.typescriptlang.org/>`_
* `React <https://react.dev/>`_
* `Mantine <https://mantine.dev/>`_
* `Zustand <https://zustand-demo.pmnd.rs/>`_
* `Vite <https://vite.dev>`_, `BiomeJS <https://vite.dev>`_
* `Socket.IO <https://socket.io>`_
* `Flask <https://flask.palletsprojects.com/en/stable/>`_
* `Flask-SocketIO <https://flask-socketio.readthedocs.io/en/latest/>`_
* `Flask-CORS <https://corydolphin.com/flask-cors/>`_

The list is subject to change as the **webtools** evolve to support changing needs or new functionality.

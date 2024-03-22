import os
import sys
from datetime import date

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Ingredient Parser"
copyright = f"{date.today().year}, Tom Strange"
author = "Tom Strange"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
]

# autodoc_typehints = "none"
napoleon_numpy_docstring = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_use_keyword = False

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Modify path to make ingredient_parser package available for autodoc
sys.path.insert(0, os.path.abspath("../.."))

import ingredient_parser

version = ingredient_parser.__version__


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css", "pygments.css"]
html_title = f"Ingredient Parser {version}"
html_context = {"default_mode": "dark"}


html_theme_options = {
    "pygment_dark_style": "gruvbox-dark",
    "repository_url": "https://github.com/strangetom/ingredient-parser",
    "repository_branch": "master",
    "use_repository_button": True,
    "navigation_with_keys": False,
}

intersphinx_mapping = {
    "pint": ("https://pint.readthedocs.io/en/stable/", None),
    "sklean": ("https://scikit-learn.org/stable/", None),
}

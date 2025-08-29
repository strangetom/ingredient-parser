import os
import sys

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Ingredient Parser"
copyright = "2025, Tom Strange"
author = "Tom Strange"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "numpydoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_favicon",
    "sphinxcontrib.lightbox2",
    "myst_parser",
]

numpydoc_xref_param_type = True
numpydoc_class_members_toctree = False

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
html_logo = "_static/logos/logo_small_source.svg"

html_theme_options = {
    "pygment_dark_style": "gruvbox-dark",
    "repository_url": "https://github.com/strangetom/ingredient-parser",
    "repository_branch": "master",
    "use_repository_button": True,
    "navigation_with_keys": False,
    "logo": {
        "alt_text": f"Ingredient Parser {version}",
        "text": f"Ingredient Parser {version}",
        "image_light": "_static/logos/logo_small_source.svg",
        "image_dark": "_static/logos/logo_small_source.svg",
    },
}

favicons = [
    {"rel": "icon", "href": "favicon/favicon.svg", "type": "image/svg+xml"},
    {
        "rel": "icon",
        "sizes": "16x16",
        "href": "favicon/favicon-16x16.png",
        "type": "image/png",
    },
    {
        "rel": "icon",
        "sizes": "32x32",
        "href": "favicon/favicon-32x32.png",
        "type": "image/png",
    },
    {
        "rel": "icon",
        "sizes": "144x144",
        "href": "favicon/favicon-144x144.png",
        "type": "image/png",
    },
    {
        "rel": "icon",
        "sizes": "512x512",
        "href": "favicon/favicon-512x512.png",
        "type": "image/png",
    },
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pint": ("https://pint.readthedocs.io/en/stable/", None),
    "sklean": ("https://scikit-learn.org/stable/", None),
}

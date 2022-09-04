import os
import sys

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Ingredient Parser'
copyright = '2022, Tom Strange'
author = 'Tom Strange'
release = '0.1.0-alpha1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
  'sphinx.ext.autodoc', 
  'sphinx.ext.napoleon',
  'sphinx_design'
]
autodoc_typehints = 'none'

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Modify path to make ingredient_parser package available for autodoc
sys.path.insert(0, os.path.abspath('../..'))

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
html_css_files = ['custom.css', 'pygments.css']

html_context = {
   "default_mode": "dark"
}


html_theme_options = {
  "collapse_navigation": True,
   "pygment_light_style": "gruvbox-light",
   "pygment_dark_style": "gruvbox-dark"
}

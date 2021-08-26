# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

import pkg_resources
import sphinx_rtd_theme

project = "Best Buy Bullet Bot"
copyright = "2021, Leon Shams-Schaal"
author = "Leon Shams-Schaal"

release = pkg_resources.get_distribution("3b-bot").version


# -- General configuration ---------------------------------------------------

needs_sphinx = "4.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
source_suffix = ".rst"
exclude_patterns = []

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ["_static"]

html_logo = "assets/logo.png"
html_theme_options = {"logo_only": True}

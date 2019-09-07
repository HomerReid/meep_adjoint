# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

import numpy as np

import meep as mp
sys.path.insert(0,os.path.abspath('..'))
import meep_adjoint

######################################################################
# setting this environment variable replicates the build as executed
# on readthedocs
######################################################################
on_rtd = os.environ.get('READTHEDOCS') == 'True'

# -- Project information -----------------------------------------------------

project = 'meep_adjoint'
copyright = '2019, MEEP project'
author = 'Homer Reid'

# The full version, including alpha/beta/rc tags
release = '1.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
 'recommonmark',
 'sphinx.ext.autodoc',
 'sphinx.ext.autosummary',
 'sphinx.ext.mathjax',
 'sphinx.ext.viewcode',
 'sphinx.ext.napoleon',
 'sphinx.ext.intersphinx',
 'sphinx.ext.todo',
 'IPython.sphinxext.ipython_console_highlighting',
 'IPython.sphinxext.ipython_directive'
]

pygments_style = 'friendly'
# pygments_style = 'breeze'
#pygments_style = 'solarizedlight'
#pygments_style = 'sphinx'
inline_highlight_respect_highlight = True
inline_highlight_literals = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# suffix(es) of source filenames
source_suffix = ['.rst', '.md']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'Shorthand.rst']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_theme_path = ["."]
html_css_files = ['custom.css']

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

autodoc_default_options = {
   'members':          True,
   'show-inheritance': True
 }
autosummary_generate = True

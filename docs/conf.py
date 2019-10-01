# Sphinx configuration file for meep_adjoint documentation

import os
import sys

import numpy as np

import sphinx_rtd_theme

import meep as mp
sys.path.insert(0,os.path.abspath('..'))
import meep_adjoint

######################################################################
# setting this environment variable replicates the build as executed
# on readthedocs
######################################################################
on_rtd = os.environ.get('READTHEDOCS') == 'True'

######################################################################
# project info
######################################################################
project = 'meep_adjoint'
copyright = '2019, MEEP project'
author = 'Homer Reid'
release = '1.0'

######################################################################
# sphinx search paths and extension modules
######################################################################
templates_path = ['_templates']
source_suffix = ['.rst', '.md']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'Shorthand.rst']

extensions = [
 'recommonmark',
 'sphinx.ext.autodoc',
 'sphinx.ext.autosummary',
 'sphinx.ext.mathjax',
 'sphinx.ext.viewcode',
 'sphinx.ext.napoleon',
 'sphinx.ext.intersphinx',
 'sphinx.ext.todo',
 'sphinx_rtd_theme',
 'IPython.sphinxext.ipython_console_highlighting',
 'IPython.sphinxext.ipython_directive'
]

######################################################################
# pygments
######################################################################
pygments_style = 'friendly'
# pygments_style = 'breeze'
#pygments_style = 'solarizedlight'
#pygments_style = 'sphinx'
inline_highlight_respect_highlight = True
inline_highlight_literals = True

######################################################################
# HTML output
######################################################################
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

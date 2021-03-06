"""Sphinx configuration file for meep_adjoint documentation."""

import os
import sys
import re

import numpy as np
import meep as mp
sys.path.insert(0, os.path.abspath('..'))
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
 'sphinx.ext.autosectionlabel',
 'sphinx.ext.mathjax',
 'sphinx.ext.viewcode',
 'sphinx.ext.napoleon',
 'sphinx.ext.intersphinx',
 'sphinx.ext.todo',
 'sphinx_rtd_theme',
 'IPython.sphinxext.ipython_console_highlighting',
 'IPython.sphinxext.ipython_directive'
]

default_role = 'py:obj'

nitpicky = True    # issue warnings for all broken links

######################################################################
# text to be automatically included at top and bottom of all .rst files
######################################################################
rst_prolog = """
.. include:: /_static/preamble.rst
"""

rst_epilog = """
.. include:: /_static/postamble.rst
"""

######################################################################
# pygments
######################################################################
pygments_style = 'cobalt2'
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
html_css_files = ['custom.css', 'theme_overrides.css']
html_js_files = ['toggle_visibility.js']
html_static_path = ['_static']
html_compact_lists = False
#html_logo =
#html_favicon =

######################################################################
# autogenerated API documentation
######################################################################
autodoc_default_options = {
   'members':          True,
   'show-inheritance': True,
   'exclude-members': '__weakref__'
 }
autoclass_content = 'both'
autodoc_member_order = 'bysource'
autosummary_generate = True
add_module_names = False

modindex_common_prefix = ['meep_adjoint.']


######################################################################
# hook to autogenerate tables of configuration options
#
#  note: this only needs to run when one of the source files
#        containing lists of option templates is updated,
#        but doing it that way didn't seem to work, so we
#        do it at the start of every build
######################################################################
def pre_build_hook(app):

    from meep_adjoint import option_almanac, adjoint_options, visualization_options
    from meep_adjoint.option_almanac import document_options

    with open('customization/adj_opt_docs.rst','w') as f:
        for title,templates in adjoint_options.option_categories.items():
            f.write( document_options(title,templates) )
            f.write('\n\n\n\n')


    with open('customization/sec_vis_opt_docs.rst','w') as f:
        title = 'Sectioned visualization options'
        templates = visualization_options.sectioned_templates
        f.write( document_options(title,templates) )


    with open('customization/oth_vis_opt_docs.rst','w') as f:
        title = 'Other visualization options'
        templates = visualization_options.other_templates
        f.write( document_options(title,templates) )


######################################################################
# hook to do some minor post-processing of html files after sphinx build
######################################################################
OLD = 'meep_adjoint: A python module for adjoint sensitivity analysis in MEEP'
NEW = '<code class=xref>meep_adjoint</code>: A python module for adjoint sensitivity analysis in <span class="codename">meep</span>'
def cleanup_html_file(file):
    with open(file,'r') as f:
        lines = f.readlines()
    with open(file,'w') as f:
        for line in lines:
            line = line.replace(OLD,NEW)
            f.write(line)

def post_build_hook(app, exception):
    for root, dirs, files in os.walk(app.outdir):
        for file in files:
            if file.endswith(".html"):
                cleanup_html_file(root + '/' + file)

######################################################################
# install hooks
######################################################################
def setup(app):
    app.connect('builder-inited', pre_build_hook)
    app.connect('build-finished', post_build_hook)

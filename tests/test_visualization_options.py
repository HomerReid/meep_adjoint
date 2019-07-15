""" Test handling of visualization-related options. This is based on the
    functionality provided by OptionsAlmanac, which is tested elsewhere,
    but adds the additional complication of section-specific overrides
    of option values.
"""
import sys
import os
from os import environ as env
import pytest

sys.path.insert(0, os.path.abspath('..'))
from meep_adjoint import set_visualization_option_defaults as set_vis_opt_defaults
from meep_adjoint import get_visualization_options as vis_opts
from meep_adjoint import get_visualization_option as vis_opt

sys.path.insert(0, os.path.abspath('.'))
from helpers import TestEnvironment


######################################################################
# The next few lines hard-code the content of various environmental
# elements (files, environment variables, and command-line options)
# as we want the test code to see them.
######################################################################
RCLOCAL_NAME = 'meep_visualization.rc'
RCLOCAL_BODY = """\
[default]
cmap = viridis
linewidth = 0.6
fcolor = '#123456'
linecolor = '#ff5673'
alpha = 0.23

[eps]
alpha = 0.1
linewidth = 0.2
linecolor = '#999900'

[src_region]
alpha = 0.9
linewidth = 0.34
linecolor = '#678123'

"""

TEST_FILES = [ (RCLOCAL_NAME,  RCLOCAL_BODY) ]

TEST_ENV = { 'src_cb_pad': 0.11, 'cb_pad': 0.9, 'eps_alpha':0.44 }

TEST_ARGS = { 'alpha': 2.22, 'eps_alpha': 0.75, 'src_alpha': 0.2,
              'zmin': 0.5, 'eps_zmin': 0.234, 'src_region_zmin': 0.3,
              'zmax': 0.97
            }


######################################################################
######################################################################
######################################################################
def test_visualization_options():

    with TestEnvironment(TEST_FILES, TEST_ENV, TEST_ARGS) as testenv:
        custom_defaults = { 'method': 'imshow', 'zmin': 0.2, 'eps_zmin': 0.123 }
        set_vis_opt_defaults(custom_defaults)



    assert vis_opt('cmap')       == 'viridis'
    assert vis_opt('alpha')      == 2.22

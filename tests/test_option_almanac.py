""" Test of basic generic framework for parsing options.

    This is a test of the core functionality of the general-purpose
    OptionAlmanac class, using a simple artificial set of
    configuration options. It only tests code in util.py and
    does not refer to anything related to adjoint solvers or
    visualization. (See test_visualization_options for
    a test that engages with details specific to the meep_adjoint
    package.

    For this test, we have a global config file, a local config file,
    options specified by environment variables, and command-line arguments.
    We test that option values set by later entries in this
    hierarchy override those set by earlier entries.
"""
import sys
from tempfile import TemporaryDirectory
import shutil
import os
from os.path import dirname, abspath, expanduser, isfile
from os import environ as env
import pytest


PWD = dirname(abspath(__file__))
sys.path.insert(0,PWD)
from helpers import TestEnvironment

sys.path.insert(0,dirname(PWD + '..'))
from meep_adjoint.util import OptionTemplate, OptionAlmanac


######################################################################
# data defining the set of options
######################################################################
templates = [
    OptionTemplate( 'verbose', False,       'generate verbose output' ),
    OptionTemplate( 'index',   4,           'integer in range [0-12]' ),
    OptionTemplate( 'mass',    19.2,        'mass of sample'          ),
    OptionTemplate( 'omega',   3.14,        'angular frequency'       ),
    OptionTemplate( 'title',   'MyTitle',   'title string'            )]

RCFILE = 'test_option_almanac.rc'


######################################################################
# hard-coded test data describing files, environment variables, and
# command-line options that mimic a typical user's environment
######################################################################

RCGLOBAL_NAME = '~/.{}'.format(RCFILE)
RCGLOBAL_BODY = """\
[default]
verbose = True
index = 0
omega = 0.00
title = 'Title zero'
"""

RCLOCAL_NAME = RCFILE
RCLOCAL_BODY = """\
[default]
index = 1
omega = 1.11
title = 'Title one'
"""

TEST_FILES = [ (RCGLOBAL_NAME, RCGLOBAL_BODY),
               (RCLOCAL_NAME,  RCLOCAL_BODY)]

TEST_ENV  = { 'omega': 2.22, 'title' : 'Title two'  }
TEST_ARGS = { 'title': 'Title three' }


######################################################################
######################################################################
######################################################################
def test_option_almanac():

    with TestEnvironment(TEST_FILES, TEST_ENV, TEST_ARGS):
        options = OptionAlmanac(templates, filename=RCFILE)


    assert options('title')    == 'Title three'
    assert options('omega')    == 2.22
    assert options('index')    == 1
    assert options('mass')     == 19.2
    assert options('verbose')  == True

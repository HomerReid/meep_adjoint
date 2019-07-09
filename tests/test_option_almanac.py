import sys
from tempfile import TemporaryDirectory
import shutil
from os.path import expanduser, isfile
from os import environ as env
import pytest

sys.path.insert(0, os.path.abspath('../meep_adjoint'))

from util import OptionTemplate, OptionAlmanac

def test_options():
    """ Test of basic framework for parsing options.

        This is a test of the core functionality of the general-purpose
        OptionAlmanac class, using a simple artificial set of
        configuration options. It only tests code in util.py and
        does not refer to anything related to adjoint solvers or
        visualization. (See test_adj_vis_opt for a test of the
        actual adjoint / visualization configuration.)

        In this test, we have a global config file,
        a local config file, options specified by environment
        variables, and command-line arguments. We test
        that option values set by later entries in this
        hierarchy override those set by earlier entries.
    """

    ######################################################################
    # data defining the set of options
    ######################################################################
    templates = [
        OptionTemplate( 'verbose', False,       'generate verbose output' ),
        OptionTemplate( 'index',   4,           'integer in range [0-12]' ),
        OptionTemplate( 'mass',    19.2,        'mass of sample'          ),
        OptionTemplate( 'omega',   3.14,        'angular frequency'       ),
        OptionTemplate( 'title',   'MyTitle',   'title string'            )]
    RCFILE = 'test_options.rc'

    ######################################################################
    # test data mimicking a typical user's environment
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

    TEST_ENV = { 'omega': 2.22, 'title' : 'Title two'  }
    TEST_ARGS = { 'title': 'Title three' }

    ######################################################################
    # parse options in a temporary context representing test environment
    ######################################################################
    with TestEnvironment(TEST_FILES, TEST_ENV, TEST_ARGS) as testenv:
        import ipdb; ipdb.set_trace()
        testopts = OptionAlmanac(templates, filename=RCFILE)

    assert testopts('title')    == 'Title three'
    assert testopts('omega')    == 2.22
    assert testopts('index')    == 1
    assert testopts('mass')     == 19.2
    assert testopts('verbose')  == True



class TestEnvironment(object):
    """ Context manager for setting up and tearing down test environment while
        preserving any pre-existing files that get overwritten.

        More specifically, this class sets up:
            (a) input files
            (b) environment variables
            (c) command-line options
        with the guarantee that any existing files that would be overwritten
        by step (a) are temporarily relocated on entry and restored on exit.

        Constructor inputs:
            test_files: list of (filename, filebody) tuples for input files that
                        should exist with the given content for the duration of the context.
            test_env:   dict of { var:value } records that should be present in
                        sys.environ for the duration of the context
            test_args:  dict of { arg:value } records that should be present in
                        sys.argv for the duration of the context

        Class data fields:
            self.files = list of (file_path,copy_path) pairs, where
                         file_path is the full path to a file and
                         copy_path is the full path to which the
                         pre-existing version of that file has been
                         temporarily moved pending exit from the context,
                         or None if the file did not previously exist
            self.tmpdir = temporary directory in which pre-existing
                          files are stored, or None if there were no
                          pre-existing files
    """
    def __init__(self, test_files=[], test_env={}, test_args={}):
        # Step 1: Ensure that all required files exist and have
        # the given content, taking care to avoid rewriting existing files.
        self.files, self.tmpdir = [], None
        for nf, (name,body) in enumerate(test_files):
            path = expanduser(name)
            if isfile(path):
                self.tmpdir = self.tmpdir or TemporaryDirectory()
                copy = '{}/f{}'.format(self.tmpdir.name,nf)
                shutil.move(path, copy)
            else:
                copy = None
            self.files += [(path,copy)]
            with open(path,'w') as f:
                f.write(body)

        # Steps 2,3: Add environment variables and command-line arguments.
        os.environ.update( {k:str(v) for k,v in test_env.items() } )

        sys.argv=sys.argv[0:1]
        for (t,v) in test_args.items():
            sys.argv += ['--{}'.format(t)] + ( ['{}'.format(v)] if v else [] )


    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        """For all test files, restore the pre-existing
           version of the file, or simply delete it if the file
           did not previously exist. Then clean up the
           temporary directory, if we created one.
        """
        for (path,copy) in self.files:
            if copy is not None:
                shutil.move(copy,path)
            else:
                os.remove(path)
        if self.tmpdir:
            self.tmpdir.cleanup()

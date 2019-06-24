import sys
from os.path import expanduser
from os import environ as env
import pytest


from meep_adjoint.util import OptionTemplate, OptionSettings


def test_options():
    """ Test option processing with priorities.

        In this test, we have a global config file,
        a local config file, options specified by environment
        variables, and command-line arguments. We test
        that option values set by later entries in this
        hierarchy override those set by earlier entries.
    """

    ######################################################################
    # data for options test ##############################################
    ######################################################################
    templates = [
        OptionTemplate( 'verbose', False,       'generate verbose output' ),
        OptionTemplate( 'index',   4,           'integer in range [0-12]' ),
        OptionTemplate( 'mass',    19.2,        'mass of sample'          ),
        OptionTemplate( 'omega',   3.14,        'angular frequency'       ),
        OptionTemplate( 'title',   'MyTitle',   'title string'            )]

    RCFILE = 'test_options_moby_dick.rc'

    GLOBAL_CONFIG=""" [default]
                      verbose = True
                      index = 0
                      omega = 0.00
                      title = 'Title zero'"""

    LOCAL_CONFIG=""" [default]
                     index = 1
                     omega = 1.11
                     title = 'Title one'"""

    ENV_OPTS = { 'omega': 2.22, 'title' : 'Title two'  }
    ARG_OPTS = { 'title': 'Title three' }

    ######################################################################
    # configure mock environment for options parser: write global/local
    # config files, set environment variables and command-line arguments
    ######################################################################
    rcglobal, rclocal = expanduser('~/.{}'.format(RCFILE)), RCFILE
    with open(rcglobal,'w') as fglobal, open(rclocal,'w') as flocal:
        fglobal.write(GLOBAL_CONFIG)
        flocal.write(LOCAL_CONFIG)
    env.update( {k:str(v) for k,v in ENV_OPTS.items() } )
    sys.argv=sys.argv[0:1]
    for (t,v) in ARG_OPTS.items():
        sys.argv += ['--{}'.format(t), v ]

    ######################################################################
    ######################################################################
    ######################################################################
    testopts = OptionSettings(templates, filename=RCFILE)
    return testopts

    assert testopts('title')    == 'Title three'
    assert testopts('omega')    == 2.22
    assert testopts('index')    == 1
    assert testopts('mass')     == 19.2
    assert testopts('verbose')  == True

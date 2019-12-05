"""miscellaneous general-purpose utility routines for meep_adjoint"""
import os
from os.path import sep as PATHSEP
import sys
import io
import traceback
import socket
import re
import warnings
from datetime import datetime as dt2
from tempfile import gettempdir

"""module-global filename and timestamp format for log files"""
LOGFILE, LOGFMT = None, '%D<>%T.%f '

def init_log(filename='meep_adjoint.log', usecs=None):
    """configure global logfile settings

    Args:
        filename (str): name of logfile or '' to disable logging.
        usecs (bool): True/False for microsecond/second resolution in logfile timestamps

    Returns:
        Nothing (sets module-global variables LOGFILE, LOGFMT)
    """
    global LOGFILE, LOGFMT
    if filename is not None:
        LOGFILE = filename or None
    if LOGFILE and LOGFILE!=os.path.abspath(LOGFILE):
        LOGFILE = gettempdir() + PATHSEP + LOGFILE
    if usecs is not None:
        LOGFMT = '%D<>%T' + ('.%f ' if usecs else ' ')


def log(msg):
    global LOGFILE
    if msg and LOGFILE:
        with open(LOGFILE,'a') as f:
            f.write(dt2.now().strftime(LOGFMT) + msg + '\n')


def warn(msg, retval=None):
    log('warning: ' + msg)
    warnings.warn(msg)
    return retval


def get_exception_info(msg=None,warning=False):
    """Return a detailed description of an exception in string form.

    Usage example:
        try:
            tricky_thing()
        except:
            errmsg = get_exception_info(msg='failed to accomplish tricky thing')

    Args:
        msg (str): optional contextualizing string to precede exception info
        warning (bool): If True, print the exception info as a warning message
                        on the console. Note that the info is logged via
                        log() regardless of the setting of warning.
    """
    errmsg, exc_info = io.StringIO(), sys.exc_info()
    errmsg.write('{}{}\n'.format(msg + ':' if msg else  '',exc_info[0]))
    errmsg.write('Exception value: {}\n'.format(exc_info[1]))
    traceback.print_tb(exc_info[2],limit=None,file=errmsg)
    dummy = warn(errmsg.getvalue()) if warning else log(errmsg.getvalue())
    return errmsg.getvalue()



#_term = 'initialize_me'
#
#def termsty(sty):
#    """context-aware generation of terminal escape codes
#
#    usage example:
#        print( termsty('red') + 'red text' + termsty() )
#
#    Parameters
#    ----------
#    sty: str
#        text style indicator:
#           (a) 'red', 'white', ...
#           (b) 'on_red', 'on_white', ...
#           (c) '1',  '2',  ...
#           (d) 'on_1', 'on_2', ...
#           (e) 'bold', 'italic', etc.
#           (f) '' for normal text
#
#    Returns
#    -------
#    code: str
#        terminal escape sequence
#    """
#    global _term
#    if isinstance(_term,'str'):
#        try:
#            import blessings
#            _term = blessings.Terminal()
#        except:
#            _term = None
#
#    if not _term:
#        return ''
#
#    if msty(sty):
#        stage, mta, mtb = 'SOURCES', 0, last_source_time

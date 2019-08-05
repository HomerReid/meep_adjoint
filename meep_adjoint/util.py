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

######################################################################
######################################################################
######################################################################
LOGFILE, LOGFMT = None, '%D<>%T '

LOGFILE, LOGFMT = 'meep_adjoint.log', '%D<>%T.%f '

def init_log(filename=None, usecs=None):
    """configure global logfile settings

    Args:
        filename (str): name of logfile or '' to disable logging.
        usecs (bool): True/False for microsecond/second resolution in logfile timestamps

    Returns:
        Nothing (sets global variables LOGFILE, LOGFMT)
    """
    global LOGFILE, LOGFMT
    if filename is not None:
        LOGFILE = filename or None
    if LOGFILE != os.path.abspath(LOGFILE):
        LOGFILE = gettempdir() + PATHSEP + LOGFILE
    if usecs is not None:
        LOGFMT = '%D<>%T' + ('.%f ' if usecs else ' ')


def log(msg):
    if msg and LOGFILE:
        with open(LOGFILE,'a') as f:
            f.write(dt2.now().strftime(LOGFMT) + msg + '\n')


def warn(msg, retval=None):
    log('warning: ' + msg)
    warnings.warn(msg)
    return retval


def get_exception_info(exc_info=None,msg=None,warning=False):
    errmsg, exc_info = io.StringIO(), exc_info or sys.exc_info()
    errmsg.write('{}{}\n'.format(msg + ':' if msg else  '',exc_info[0]))
    errmsg.write('Exception value: {}\n'.format(exc_info[1]))
    traceback.print_tb(exc_info[2],limit=None,file=errmsg)
    dummy = warn(errmsg.getvalue()) if warning else log(errmsg.getvalue())
    return errmsg.getvalue()

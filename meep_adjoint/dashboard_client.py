""" Client-side implementation for the GUI dashboard.

This module exports the package-global routines
{launch, update, close}_dashboard.

"""
import os
from os.path import dirname, abspath
from os.path import sep as PATHSEP
import socket
import psutil
from psutil import process_iter as procs
import subprocess
import asyncio
import time
from tempfile import gettempdir
import contextlib

import meep as mp

from . import log, warn, get_exception_info
from . import get_adjoint_option as adj_opt


"""module-global variables describing dashboard connection status"""
dashboard_socket, dbserver_process = None, None


def launch_dashboard(name=None):
    """ try to connect to dashboard server and launch GUI dashboard """

    # check if dashboard already running or disabled by configuration options
    global dashboard_socket, dbserver_process
    host, port, size = [adj_opt('dashboard_' + s) for s in ['host','port','size'] ]
    if dashboard_socket is not None or size==0.0:
        return

    # fork server process if necessary
    if host=='localhost':
        fork_dashboard_server()

    try:
        dashboard_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dashboard_socket.settimeout(nw_timeout())
        log('connecting to dashboard server: {}:{}...'.format(host,port))
        dashboard_socket.connect( (host, port) )
        title = 'meep_adjoint dashboard' + (' for {}'.format(name)) if name else ''
        cpus = mp.count_processors()
        update_dashboard(['clear', 'title ' + title, 'cpus {}'.format(cpus)])
    except:
        dashboard_socket=None
        get_exception_info(msg='failed to connect to dashboard server',warning=True)


def update_dashboard(updates):
    """
    """
    global dashboard_socket, dbserver_process
    if not dashboard_socket:
        return
    content = ''.join( (s+'\n') for s in ([updates] if isinstance(updates,str) else updates) )

    try:
        dashboard_socket.send( bytes(content,'utf-8') )
        condition = 'terminated by client' if content.startswith('terminate') else None
    except:
        condition = get_exception_info(msg='error writing to dashboard', warning=True)

    if condition:
        log('closing dashboard: ' + condition)
        dashboard_socket.close()
        if dbserver_process and not dbserver_process.wait(nw_timeout()):
            dbserver_process.kill()
        dashboard_socket, dbserver_process = None, None


def close_dashboard():
    update_dashboard('terminate')


def nw_timeout():
    return 5 if adj_opt('dashboard_host') == 'localhost' else 30


def fork_dashboard_server():
    """Launch a single-session dashboard server as a subprocess."""
    try:
        # refer to our own process info to get python interpreter and server script
        pycmd = psutil.Process(os.getpid()).cmdline()[0]
        pyscript = dirname(abspath(__file__)) + os.path.sep + 'dashboard_server.py'
        argv = [ pycmd, pyscript, '--single_session' ]

        # check if server is already running
        for proc, pid in [ (p,p.pid) for p in procs() if len(p.cmdline())>1 ]:
            if proc.cmdline()[0:2] == argv[0:2]:
                return log('found dashboard server (PID {}), not relaunching'.format(pid))

        # add any dashboard-related command-line arguments to server command line
        original_argv = adj_opt('original_cmdline').split()
        for narg, arg in enumerate(original_argv):
            if arg.startswith('--dashboard'):
                argv += original_argv[narg:narg+2]

        # launch new server in subprocess
        global dbserver_process
        if adj_opt('dashboard_loglevel') == 'debug':
            cm = open(gettempdir() + PATHSEP + 'dashboard.log','a')
        else:
            cm = contextlib.nullcontext(subprocess.DEVNULL)
        with cm as stdout:
            dbserver_process = subprocess.Popen(argv,stdout=stdout,stderr=subprocess.STDOUT)
        log('launched new dashboard server (PID {})'.format(dbserver_process.pid))
        time.sleep(1) # pause to let server complete initialization

    except:
        get_exception_info(msg='failed to launch dashboard server',warning=True)
        dbserver_process = None



# meep_process = None
# def cpu_percent():
#     global meep_process
#     if meep_process is None:
#         try:
#             import psutil
#             meep_process = psutil.Process(os.getpid())
#         except:
#             meep_process = ''
#             warn('failed to initialize psutil module; cpu usage unavailable')
#     if meep_process and hasattr(meep_process,'cpu_percent'):
#         return str(int(meep_process.cpu_percent()))
#     return None

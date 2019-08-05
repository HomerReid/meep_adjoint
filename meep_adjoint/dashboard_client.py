import os
from os.path import dirname, abspath
from os.path import sep as PATHSEP
import socket
import psutil
from psutil import process_iter as procs
import subprocess
import time
from tempfile import gettempdir

import meep as mp

from meep_adjoint.util import init_log, log, warn, get_exception_info

######################################################################
######################################################################
######################################################################
dashboard_socket, dbserver_process = None, None
db_host, db_port = 'localhost', 16761

def nw_timeout():
    return 5 if db_host=='localhost' else 30

def fork_dashboard_server():
    """
    """
    try:
        # refer to our own process info to get python interpreter and server script
        pycmd = psutil.Process(os.getpid()).cmdline()[0]
        pyscript = dirname(abspath(__file__)) + os.path.sep + 'dashboard_server.py'
        argv = [ pycmd, pyscript ]

        # check if server is already running
        for proc, pid in [ (p,p.pid) for p in procs() if len(p.cmdline())>1 ]:
            if proc.cmdline()[0:2] == argv:
                return log('found dashboard server (PID {}), not relaunching'.format(pid))

        # launch new server if not
        global dbserver_process
        stdout, stderr = subprocess.DEVNULL, subprocess.STDOUT
        #stdout = open('{}{}{}'.format(gettempdir(),PATHSEP,'fork_dbserver.out'),'a')
        dbserver_process = subprocess.Popen(argv,stdout=stdout,stderr=stderr)
        log('launched new dashboard server (PID {})'.format(dbserver_process.pid))
        time.sleep(0.500) # pause to let server complete initialization
    except:
        get_exception_info(msg='failed to launch dashboard server',warning=True)
        dbserver_process = None


def launch_dashboard(protocol='clientserver'):
    """try to connect to dashboard server to launch GUI dashboard"""
    global dashboard_socket, dbserver_process
    if dashboard_socket is not None: # check if already running
        return

    # launch server process as necessary
    if protocol == 'clientserver' and db_host == 'localhost':
        fork_dashboard_server()

    try:
        dashboard_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dashboard_socket.settimeout(nw_timeout())
        log('connecting to dashboard server: {}:{}...'.format(db_host,db_port))
        dashboard_socket.connect( (db_host, db_port) )
        update_dashboard('cpus',str(mp.count_processors()))
    except:
        dashboard_socket=None
        get_exception_info(msg='failed to connect to dashboard server',warning=True)


def close_dashboard():
    update_dashboard('terminate')


def update_dashboard(item, val=''):
    """issue command to GUI window to update value of element 'item' to 'val' """

    global dashboard_socket, dbserver_process
    if not dashboard_socket:
        return

    try:
        dashboard_socket.send(bytes(item + ' {}\n'.format(val),'utf-8'))
        condition = 'terminated by client' if item.lower()=='terminate' else None
    except:
        condition = get_exception_info(msg='error writing to dashboard', warning=True)

    if condition:
        log('closing dashboard: ' + condition)
        dashboard_socket.close()
        if dbserver_process and not dbserver_process.wait(nw_timeout()):
            dbserver_process.kill()
        dashboard_socket, dbserver_process = None, None


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

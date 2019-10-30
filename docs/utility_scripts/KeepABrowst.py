"""
KeepABrowst.py: variation on the theme of sphinx-autobuild.

This is a utility script to assist in writing sphinx documentation
for a python package. It uses the selenium webdriver to open
the latest documentation files in a browser window, then enters
an infinite loop in which we
 --- watch for changes to documentation source files and
     rebuild the documentation tree if necesssary
 --- watch for changes to documentation output files and
     refreshes the browser window as necessary
"""

import os
from os import environ as env
from os.path import expanduser
from bs4 import BeautifulSoup
import requests
import sys
import re
import importlib
import warnings
import inspect
from datetime import datetime as dt2
import io
import traceback
import tempfile
import time
import watchdog

import selenium
from selenium import webdriver

from hrpyutil import backtics, init_log

DIR='/home/homer/work/Simpetus/meep_adjoint/docs'
INITIAL_URL = 'file://' + DIR + '/_build/html/index.html'

INITIAL_NAPTIME=1
NAPTIME_FILE='/tmp/KeepABrowst.naptime'

##################################################
# initial build
##################################################
os.chdir(DIR)
init_log(filename='/tmp/KeepABrowst.log',console=True)
backtics('make clean ',logging=True)
make_output = '\n'.join(backtics('make html',logging=True))
with open('/tmp/sphinx.out','w') as f:
    f.write(make_output)

build_refresh_time = time.time()

##################################################
# initialize / refresh browser
##################################################
try:
    driver.refresh()
except:
    env['GDK_SCALE']='1.0'
#    options = webdriver.ChromeOptions()
#    options.add_argument('--force-device-scale-factor=1')
#    options.add_argument('--high-dpi-support=1')
#    driver = webdriver.Chrome(options)
    driver = webdriver.Chrome()
    driver.get(INITIAL_URL)

browser_refresh_time = time.time()

##################################################
# main loop
##################################################
naptime = INITIAL_NAPTIME

while True:

    ######################################################################
    # this allows the polling interval to be updated while the script is running
    ######################################################################
    if os.path.isfile(NAPTIME_FILE):
        with open(NAPTIME_FILE,'r') as f:
            naptime = float(f.read())
            log('updating naptime to {}'.format(naptime))
        os.remove(NAPTIME_FILE)
    if naptime==0.0:
        break


    time.sleep(naptime)

    ######################################################################
    # check for updated source files and rebuild docs if necessary
    ######################################################################
    WATCHED_FILES = [ r'.*.rst$', r'.*.css$', r'.*.py$' ]
    source_refresh_time, newest_source_file = 0.0, ''
    for root, dirs, files in os.walk(DIR):
        if '_build' in root:
            continue
        for file in files:
            if np.any( [ re.match(pattern, file) for pattern in WATCHED_FILES ]):
                filepath = root + '/' + file
                t = os.path.getmtime(filepath)
                if t > source_refresh_time:
                    source_refresh_time, newest_source_file = t, filepath

    if source_refresh_time > build_refresh_time:
        log('source refresh = {} (newest file {})'.format(source_refresh_time,newest_source_file))
        log(' build refresh = {}'.format(build_refresh_time))
        make_output = '\n'.join(backtics('make html',logging=True))
        with open('/tmp/sphinx.out','w') as f:
            f.write(make_output)
        build_refresh_time = time.time()

    ######################################################################
    # check for updated output files and refresh browser if necessary
    ######################################################################
    current_file = driver.current_url.replace('file://','').split('#')[0]
    file_update_time = os.path.getmtime(current_file)
    refresh = (file_update_time > browser_refresh_time)
    if refresh:
        driver.refresh()
        browser_refresh_time = time.time()

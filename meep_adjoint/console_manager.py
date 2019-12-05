import sys

import re
import meep as mp

from . import log, update_dashboard
from . import get_adjoint_option as adj_opt

CODEWORD = '[meep_adjoint] '

class ConsoleManager(object):

    def __init__(self, console_file=None):
        self.am_master = True if mp.am_master() else False
        if not self.am_master:
            return
        self.fconsole = open(console_file,'w') if console_file else None


    def __enter__(self):
        if not self.am_master:
            return None
        self.stdout, self.stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = self
        return self


    def __exit__(self, type, value, traceback):
        if not self.am_master:
            return
        sys.stdout, sys.stderr = self.stdout, self.stderr
        if self.fconsole:
            self.fconsole.close()

    def flush(self):
        pass


    def write(self, text):
        """Intercept and process text originally intended to be printed on the console.
           (1) Copy the text to the console_file if present.
           (2) Then process line-by-line, identifying lines of interest to parse
               for relevant information and ignoring everything else.
               Currently we recognize two types of text line for parsing:
                   (a)
                   (b)
        """
        if not self.am_master:
            return
        if self.fconsole:
            self.fconsole.write(text)
        for line in [l for l in text.split('\n') if l]:

            # extract info from MEEP output on the progress and efficiency of timestepping
            if line.startswith('on time step'):
                matches  = [ re.search(p,line) for p in [r'time=([.\d]*)', r'([.\d]*) s/step'] ]
                meep_time, meep_rate = [ float(m[1]) if m else None for m in matches ]
                if meep_time is not None and meep_rate is not None:
                    log('parsed meep output: time={}, secs per timestep ={}'.format(meep_time,meep_rate))
                    update_dashboard('progress',int(meep_time))
                    update_dashboard('ms_per_timestep',1.0e3*meep_rate)

            # intercept lines beginning with 'dashboard'
            elif line.lower().startswith('dashboard '):
                update_dashboard( line[10:] )

            # pass through lines that start with the magic prefix
            elif line.startswith(CODEWORD):
                self.stdout.write( line[ len(CODEWORD): ] + '\n' )

_STYLECODES = {
       '0': "\x1b[30m",    '1': "\x1b[31m",
       '2': "\x1b[32m",    '3': "\x1b[33m",
       '4': "\x1b[34m",    '5': "\x1b[35m",
       '6': "\x1b[34m",    '7': "\x1b[35m",
    'on_0': "\x1b[40m", 'on_1': "\x1b[41m",
    'on_2': "\x1b[42m", 'on_3': "\x1b[43m",
    'on_4': "\x1b[44m", 'on_5': "\x1b[45m",
    'on_6': "\x1b[46m", 'on_7': "\x1b[47m",
  'normal': "\x1b[0m"
}

def termsty(s,sty):
    on = _STYLECODES.get(sty,'') if adj_opt('termcolors') else ''
    off = _STYLECODES['normal'] if on else ''
    return on + s + off

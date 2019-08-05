######################################################################
# Q: For context managers in general, how does one decide which
#    initialization/startup code goes in __init__ vs.__enter__?
######################################################################
class ConsoleManager(object):

    def __init__(self, console_file=None):
        import meep as mp
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
                try:
                    tokens = re.sub(r'^.*time=([.\d]*).*([.\d]*) s/step',r'\1 \2',line)
                    meep_time, sec_per_timestep = float(tokens[0]), float(tokens[1])
                    log('parsed meep output: time={}, spt={}'.format(meep_time,sec_per_timestep))
                    update_dashboard('progress',int(meep_time))
                    update_dashboard('ms_per_timestep',1.0e3*sec_per_timestep)
                except:
                    log('failed to parse MEEP info: line={}'.format(line))
            # process dashboard updates like 'Iteration 10'
            elif line.split()[0].lower() in DASHBOARD_ELEMENTS:
                update_dashboard(line)

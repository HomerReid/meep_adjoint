"""General-purpose utilities for meep.adjoint

   This file collects some general-purpose utility functions and classes that are
   used in meep.adjoint but are not specific to adjoint solvers or computational
   electromagnetism.

   The functions/classes included are as follows:

   (1) process_options: creates {option:value} dicts by parsing a
                        hierarchy of config files, environment variables,
                        and command-line options

   (2) math utility routines

"""
from os import environ as env
from os.path import expanduser
import sys
import argparse
import configparser
from collections import namedtuple
from warnings import warn
from datetime import datetime as dt


OptionTemplate = namedtuple('OptionTemplate', 'name default help')
OptionTemplate.__doc__ = 'name, default value, and usage for one configurable option'

class OptionAlmanac(object):
    """Database of option values read from config files, environment, and command-line args.

       On instantiation, this class determines values for each element in a
       list of named options by consulting each of the following sources
       in increasing order of priority:

       (a) The default value given in the initialization template (see below)
       (b) Dict of customized defaults passed to constructor or set_defaults()
       (c) Global config file
       (d) Local config file
       (e) Environment variables
       (f) Command-line arguments. (Processed arguments are removed
           from sys.argv, leaving other arguments unchanged for subsequent
           downstream parsing.)

      After initialization, class instances serve as databases of option values
      that may be queried via the __call__ method, thus:
          my_options = OptionAlmanac(...)
          opt_value  = my_options('option_name')

    Constructor arguments:

        templates (list of OptionTemplate): option definitions

        custom_defaults (dict): optional overrides of default values in templates

        section(str): optional section specification; if present, only matching
                      sections of config files are parsed. If absent, all
                      sections of all files are parsed.

        filename (str): If e.g. filename == 'myconfig.rc', then:
                          1. the global config file is ~/.my_config.rc
                          2. the local config file is ./my_config.rc in the current working directory.
                        If unspecified, no configuration files are processed.

        search_env (bool): Whether or not to look for option settings in
                           environment variables. The default is True, but
                           you may want to set it to False if you have
                           option whose names overlap with standard
                           environment variables, such as 'HOME'

        prepend_section (bool): If True, the section name (plus an underscore) is
                                prepended to the names of options for searching
                                environment variables and command-line arguments.
    """

    def __init__(self, templates, custom_defaults={}, section=None,
                       filename=None, search_env=True, prepend_section=False):
        """harvest option values from config files, environment, and command-line args"""

        # initialize options to their template default values
        self.options  = { t.name: t.default for t in templates }

        # types inferred from defaults, used to type-check subsequent updates
        self.opttypes = { t.name: type(t.default) for t in templates }

        # update 1: caller-specified custom defaults
        self.revise(custom_defaults, 'custom_defaults')

        # updates 2,3: global, local config files
        if filename:
            fglob, floc = expanduser('~/.{}'.format(filename)), filename
            config = configparser.ConfigParser()
            config.read([fglob, floc])
            sections = config.sections()
            if section:
                sections=[s for s in sections if s.lower()==section.lower()]
            for s in sections:
                self.revise(config.items(s), 'config files')

        # update 4: environment variables
        pfx = '{}_'.format(section) if prepend_section and section else ''
        if search_env:
            envopts = { t.name: env[pfx + t.name] for t in templates if (pfx + t.name) in env }
            self.revise(envopts, 'environment variables')

        # update 5: command-line arguments
        parser = argparse.ArgumentParser()
        for n,v,h in [ (t.name, self.options[t.name], t.help) for t in templates ]:
            parser.add_argument('--{}{}'.format(pfx,n),type=type(v),default=v,help=h)
        argopts, leftovers = parser.parse_known_args()
        self.revise(argopts.__dict__.items(), 'command-line arguments')
        self.options['original_cmdline'] = ' '.join(sys.argv)
        sys.argv = [sys.argv[0]] + leftovers


    def revise(self, revisions, context):
        """cautiously apply a proposed set of updated option values

        Args:
            revisions: dict of {key:new_value} records OR list of (key,new_value) pairs
            context:   optional label like 'global config file' or 'command line'
                       for inclusion in error messages to help trace mishaps

        The result is similar to that of self.options.update( {k:v for (k,v) in revisions } ),
        but (a) ignores 'updates' to options that weren't previously configured
            (b) removes non-escaped single and double quotes surrounding strings,
            (c) attempts type conversions as necessary to preserve the type of the
                value associated with each key.

        Returns: none (vals is updated in place)
        """
        revisions = revisions.items() if hasattr(revisions,'items') else revisions
        for (key,newval) in [ (k,uq(v)) for k,v in revisions if k in self.options ]:
            try:
                self.options[key] = (self.opttypes[key])(newval)
            except ValueError:
                msg='option {}: ignoring improper value {} from {} (retaining value {})'
                warn(msg.format(key,newval,context,self.options[key]))


    def merge(self, partner):
        self.options.update(partner.options)


    def __call__(self, name, fallback=None, overrides={}):
        if name in overrides:
            try:
                return (self.opttypes[name])(overrides[name])
            except ValueError:
                warn('option {}: ignoring improper override value {}',name,overrides[name])
        return self.options.get(name,fallback)


def uq(s):
    """compensate for configparser's failure to unquote strings"""
    if s and isinstance(s,str) and s[0]==s[-1] and s[0] in ["'",'"']:
        return s[1:-1]
    return s

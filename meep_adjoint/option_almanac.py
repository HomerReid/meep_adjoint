"""option_almanac.py is a simple module that implements a database storing
   option settings configurable via a precise hierarchy of sources, including
   config files, environment variables, and command-line options
"""
import os
from os import environ as env
from os.path import expanduser
import sys
import argparse
import configparser
from collections import namedtuple
from warnings import warn
from datetime import datetime as dt
from numbers import Number


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
        for opt, opttype, help in [ (t.name, self.opttypes[t.name], t.help) for t in templates ]:
            parser.add_argument('--' + pfx + opt, type=opttype, help=help)
        argopts, leftovers = parser.parse_known_args()
        self.options['original_cmdline'], sys.argv = ' '.join(sys.argv), [sys.argv[0]] + leftovers
        revisions = { k[len(pfx):]:v for k,v in vars(argopts).items() if v is not None }
        self.revise(revisions, 'command-line arguments')


    def revise(self, revisions, context):
        """Cautiously apply a proposed set of candidates for updated option values.
        Args:
            revisions: dict of {key:new_value} records OR list of (key,new_value) pairs
            context:   optional str like 'global config file' or 'command line'
                       for inclusion in error messages to help trace mishaps

            The result is similar to that of self.options.update( {k:v for (k,v) in revisions } ),
            but (a) ignores 'updates' to options that weren't previously configured
                (b) removes non-escaped single and double quotes surrounding strings,
                (c) attempts type conversions as necessary to preserve the type of the
                    value associated with each key.

        Return value: None (the class-internal dict of option settings is updated in-place)
        """
        revisions = revisions.items() if hasattr(revisions,'items') else revisions
        for (name,newval) in [ (k,uq(v)) for k,v in revisions if k in self.options ]:
            newval = self.enforce_type(name, newval)
            if newval is not None:
                self.options[name] = newval


    def update(self, options):
        self.options.update(options)


    def merge(self, partner):
        self.update(partner.options)


    def __call__(self, name, overrides={}):
        """Return the almanac's current value for the option
           with the given name, or None if the almanac has no such option,
           unless overrides has a value of the proper type,
           in which case that wins.
           Note: The first line here sets override to None if
           overrides has no value for name OR has a value
           but of an incompatible type.
        """
        override = self.enforce_type(name, overrides.get(name))
        return self.options.get(name) if override is None else override


    def enforce_type(self, name, value):
        """Typechecking/conversion for option update candidates
        Args:
            name   (str): name of an option
            value    (?): a value somebody has proposed to assign the option
        Returns: value converted to the type of the given option, or None
            if this is not possible. The conversion is attempted by a simple
            typecast unless the return type is boolean, which we process by
            hand as automatic conversion does not work [i.e. bool('False') == True].
        """
        # no conversion necessary?
        if value is None or type(value) == self.opttypes[name]:
            return value

        # handle string/int to boolean conversion by hand
        if self.opttypes[name] == type(True):
            if isinstance(value,str):
                vl, FF, TT = value.lower(), ['false', 'no', '0'], ['true', 'yes', '1']
                return False if vl in FF else True if vl in TT else None
            if isinstance(value,Number):
                return True if value else False
        # otherwise try automatic conversion via typecast
        else:
            try:
                return (self.opttypes[name])(value)
            except ValueError:
                pass

        warn('Option {}: proposed update value ({}) has incompatible type (ignoring)'.format(name,value))
        return None


def uq(s):
    """compensate for configparser's failure to unquote strings"""
    if s and isinstance(s,str) and s[0]==s[-1] and s[0] in ["'",'"']:
        return s[1:-1]
    return s


#########################################################################
# this routine is used to implement autodocumentation of OptionAlmanacs:
# it is invoked during a sphinx build and returns a chunk of text that
# may be  written directly into a .rst file to yield a table with one
# row for each option.
#########################################################################
def document_options(title, templates):
    hdr  = '.. csv-table:: {}\n'.format(title)
    hdr += '   :header: "Option", "Default", "Description"\n\n'
    lines = ['   `{}`, {}, "{}"'.format(t[0],t[1],ddq(t[2])) for t in templates]
    return hdr + '\n'.join(lines)

def ddq(s):
    """double double-quotes 'Say "foo", bar!' --> 'Say ""foo"", bar!'"""
    return s.replace('"','""')

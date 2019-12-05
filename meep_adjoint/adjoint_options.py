""" Handling of adjoint-related configuration options.

    This file exports two routines:
        get_adjoint_option() to lookup the value of an option
        set_default_adjoint_options() to override default option values

    Internally, option settings are maintained by a module-wide instance of
    'OptionAlmanac' (generic class for option handling defined in util.py),
    which is lazily initialized on the first call to get_adjoint_options().

"""

import numpy as np

from .option_almanac import OptionTemplate, OptionAlmanac

_adjoint_options = None
""" module-wide database of adjoint-related options, referenced only in this file"""


def _init_adjoint_options(custom_defaults={}, search_env=True):
    """internal routine for just-in-time options processing"""
    global _adjoint_options
    _adjoint_options = OptionAlmanac(adjoint_option_templates,
                                     custom_defaults=custom_defaults,
                                     filename='meep_adjoint.rc',
                                     search_env=search_env)


######################################################################
######################################################################
######################################################################
def set_adjoint_option_defaults(custom_defaults={}, search_env=True):
    """
    Routine intended to be called by meep_adjoint API scripts to set
    problem-specific option defaults.
    Args:
        custom_defaults: dict of {option:new_default_value} records
        search_env:      True/False to enable/disable scanning environment variables
                         for option settings
    """
    _init_adjoint_options(custom_defaults=custom_defaults, search_env=search_env)


##################################################
##################################################
##################################################
def get_adjoint_option(option, overrides={}):
    """Return currently configured value of option.

    Args:
        option (str): name of option
        overrides (dict): {option:value} records to override current settings

    Returns:
        Value of option if found in database, or None otherwise
    """
    global _adjoint_options
    if _adjoint_options is None:
        _init_adjoint_options()

    return _adjoint_options(option, overrides=overrides)


def set_adjoint_options(options):
    _adjoint_options.update(options)


######################################################################
# The rest of the file just defines the available options.
######################################################################

""" definition of adjoint-related configuration options """
adjoint_option_templates= [

    #--------------------------------------------------
    #- options affecting FDTD geometries/calculations
    #--------------------------------------------------
    OptionTemplate('res',              20.0,   'Yee grid resolution'),
    OptionTemplate('fcen',              0.0,   'source center frequency'),
    OptionTemplate('df',                0.0,   'source frequency width'),
    OptionTemplate('source_component', 'Ez',   'forward source component (str)'),
    OptionTemplate('source_mode',         1,   'forward source eigenmode index'),
    OptionTemplate('nfreq',               1,   'number of DFT frequencies'),
    OptionTemplate('dpml',             -1.0,   'PML width (-1 --> auto-select)'),
    OptionTemplate('dair',             -1.0,   'gap width between material bodies and PMLs (-1 --> auto-select)'),
    OptionTemplate('eps_design',      '1.0',   'function of (x,y,z) giving initial design permittivity'),
    OptionTemplate('dft_reltol',     1.0e-6,   'convergence tolerance for terminating timestepping'),
    OptionTemplate('dft_timeout',      10.0,   'max runtime in units of last_source_time'),
    OptionTemplate('dft_interval',     0.25,   'meep time between DFT convergence checks in units of last_source_time'),
    OptionTemplate('complex_fields',  False,   'use complex fields in forward calculation'),
    OptionTemplate('reuse_simulation',False,   'reuse (do not reallocate) simulation data structure'),

    #--------------------------------------------------
    #- options affecting basis-set expansions
    #--------------------------------------------------
    OptionTemplate('beta_min',        0.0,    'lower bound on basis expansion coefficient'),
    OptionTemplate('beta_max',     np.inf,    'upper bound on basis expansion coefficient'),
    OptionTemplate('element_type',   'CG 1',  'finite-element family and degree'),
    OptionTemplate('element_length',  0.0,    'finite-element discretization length'),

    #--------------------------------------------------
    #- options affecting gradient-descent optimizer
    #--------------------------------------------------
    OptionTemplate('alpha',          1.0,     'initial value of alpha (update relaxation parameter)'),
    OptionTemplate('alpha_min',      1.0e-3,  'minimum value of alpha'),
    OptionTemplate('alpha_max',      10.0,    'maximum value of alpha'),
    OptionTemplate('boldness',       1.25,    'sometimes you just gotta live a little (explain me)'),
    OptionTemplate('timidity',       0.75,    'can\'t be too cautious in this dangerous world (explain me)'),
    OptionTemplate('max_iters',      100,     'max number of optimization iterations'),

    #--------------------------------------------------
    # output files, logging, console, visualization, dashboard
    #--------------------------------------------------
    OptionTemplate('filebase',                '',         'base name of output files'),
    OptionTemplate('silence_meep',           True,        'suppress MEEP console messages when timestepping'),
    OptionTemplate('loglevel',               'info',      "['info'|'debug']"),
    OptionTemplate('visualization',          'auto',      "['on'|'off'|'auto'] to enable/disable/automate graphical visualization"),
    OptionTemplate('termcolors',              True,       "output colorized terminal text"),
    OptionTemplate('dashboard',              'auto',      "['on'|'off'|'auto'] to enable/disable/automate GUI dashboard"),
    OptionTemplate('dashboard_size',         0.5,         'GUI dashboard size relative to screen size'),
    OptionTemplate('dashboard_position',     'top right', 'GUI dashboard position'),
    OptionTemplate('dashboard_font_family',  'Fantasque Sans Mono', 'GUI dashboard font family'),
    OptionTemplate('dashboard_font_scale',   1.0,         'GUI dashboard font scale factor'),
    OptionTemplate('dashboard_on_top',       True,        'GUI dashboard stays on top of other windows'),
    OptionTemplate('dashboard_cpu_interval', 2000,        'GUI dashboard CPU usage update interval (ms)'),
    OptionTemplate('dashboard_host',         'localhost', 'GUI dashboard server hostname'),
    OptionTemplate('dashboard_port',         37673,       'GUI dashboard server port'),
    OptionTemplate('dashboard_loglevel',     'info',      "''info' | 'debug'")
]

""" Handling of visualization-related configuration options.

    This file parallels visualization_options.py: it maintains an internal
    module-wide instance of OptionsSettings that keeps track of
    user-configurable options for visualization functions, and
    exports two routines:
        -- get_visualization_options() to lookup the value of an option
        -- set_default_visualization_options() to override default option values

    However, visualization options are slightly more complicated than visualization
    options in that they make use of a notion of general vs. section-specific
    option settings.
"""

from .util import OptionTemplate, OptionAlmanac


_visualization_sections = {}
""" module-wide dict of { section_name : section_almanac } records,
    where section_name (str) is either 'default' or the name of a
    visualization sector like 'eps' or 'flux_data', and
    section_almanac (OptionAlmanac) is the set of section-specific
    option values.
"""


def _init_visualization_options(custom_defaults={}, search_env=True):
    """internal routine for just-in-time options processing"""

    # start with _visualization_sections containing just a single entry,
    # the almanac for general (section-independent) fallback option values
    general_options = OptionsAlmanac(VISUALIZATION_OPTION_TEMPLATES,
                                     custom_defaults=custom_defaults,
                                     section='default', filename='meep_visualization.rc',
                                     search_env=search_env)

    global _visualization_sections
    _visualization_sections = { 'default' : general_options }

    # now add separate almanacs for each specific section.
    for sect_name, sect_defaults, in SECTION_DEFAULTS.items():
        prefix = '{}_'.format(sect_name)
        section_custom_defaults
        section_defaults.update(
        for full_name, custom_value in custom_defaults.items():
            if full_name.startswith(prefix):
                section_defaults

{full_name.replace(prefix,''):val for full_name, val in custom_defaults.items() if full_name.startswith(prefix)}
        for key in [ k.replace(prefix,''),v in custom_defaults.items() if k.startswith(prefix)
full_name,custom_default in custom_defaults.items():
            if full_name.startswith('{}_'.format(seection)


        for opt,value in [ full_opt.full_name in custom_defaults

        _visualization_sections = { section: section_options(section, custom_defaults,


 , sect_defaults in _visualization_section_defaults.items():
        updated_sect_defaults = { opt: custom_defaults.get(sect + '_' + opt, val)
                                   for opt,val in sect_defaults.items() }
        visualization_sections

    for
    def section_options(section):
        return OptionSettings(visualization_option_templates,
                              custom_defaults=custom_defaults,
                              section=section, filename='meep_visualization.rc',
                              search_env=search_env,
                              prepend_section = (section != 'default') )

    _visualization_options = { s: section_options(s) for s in


######################################################################
# This routine is intended to be called by meep_visualization API scripts.
######################################################################
def set_visualization_option_defaults(custom_defaults={}, search_env=True):
    """
    Args:
        custom_defaults: dict of {option:new_default_value} records
        search_env:      True/False to enable/disable scanning environment variables
                         for option settings
    """
    _init_visualization_options(custom_defaults=custom_defaults, search_env=search_env)


##################################################
##################################################
##################################################
def get_visualization_option(option, section='default', fallback=None, overrides={}):
    """Return currently configured value of option.

    Args:
        option (str):  name of option
        section (str): name of section
        fallback:     what to return if option is not found among current settings
        overrides (dict): {option:value} records to override current settings

    Returns:
        Value of option if found, otherwise fallback.
    """
    global _visualization_sections
    if _visualization_sections == {}:
        _init_visualization_options()

    if not (section in visualization_sections):
        warn('unknown options section {} (skipping)'.format(section))
        return None

    almanac, _overrides = _visualization_sections['default'], overrides,

    if section != 'default':
        # if we're in a specific section, the user-supplied dict of overrides
        # will have the section name prepended to the option names, so we pause
        # to handle that.
        override_value = overrides.get('{}_{}'.format(section,option), None)
        _overrides = { option:override_value } if override_value else {}

    return almanac(option, fallback=fallback, overrides=_overrides)


######################################################################
# The rest of the file just defines the available options.
######################################################################

""" definition of general (section-independent) options """
VISUALIZATION_OPTION_TEMPLATES= [
    OptionTemplate('cmap',         'plasma',        'default colormap'),
    OptionTemplate('alpha',         1.0,            'default transparency'),
    OptionTemplate('fontsize',      25,             'font size for labels and titles'),
    OptionTemplate('method',       'contourf 100',  'contourf NN | imshow |pcolormesh'),
    OptionTemplate('shading',      'gouraud',       'shading style'),
    OptionTemplate('linecolor',    '#ff0000',       'default line color'),
    OptionTemplate('linewidth',    4.0,             'default line width'),
    OptionTemplate('linestyle',    '-',             'default line style'),
    OptionTemplate('fcolor',       '#ffffff',       'default fill color'),
    OptionTemplate('cmin',         np.inf,          'colormap minimum'),
    OptionTemplate('cmax',         np.inf,          'colormap maximum'),
    OptionTemplate('zmin',         0.6,             ''),
    OptionTemplate('zmax',         0.8,             ''),
    OptionTemplate('latex',        True,            'LaTeX text formatting'),
    OptionTemplate('cb_pad',       0.04,            'colorbar padding'),
    OptionTemplate('cb_shrink',    0.60,            'colorbar shrink factor')
 ]

""" definition of general (section-independent) options """

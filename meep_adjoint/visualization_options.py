""" Handling of visualization-related configuration options."""

from .util import OptionTemplate, OptionAlmanac


""" module-wide dict of { section_name : section_almanac } records """
_visualization_sections = {}


RCFILE = 'meep_visualization.rc'

######################################################################
# internal routines
######################################################################
def _init_visualization_options(custom_defaults={}, search_env=True):
    """internal routine for just-in-time options processing"""

    def _sectopts(s): return _init_section_options(s, custom_defaults, search_env)

    global _visualization_sections
    _visualization_sections = { s : _sectopts(s) for s in VISUALIZATION_SECTIONS }


def _init_section_options(section, custom_defaults, search_env):
    custom_section_defaults = dict( VISUALIZATION_SECTIONS.get(section,{}) )
    custom_section_defaults.update(_subdict(custom_defaults,section))
    return OptionsAlmanac(VISUALIZATION_OPTION_TEMPLATES,
                          custom_defaults=custom_section_defaults,
                          section=section, filename=RCFILE, search_env=search_env,
                          prepend_section = (section != 'default'))


def _subdict(fulldict, section, strip=True):
    """returns a dict containing all items in fulldict whose key begins with 'section_'.
       if strip==True, the 'section_' prefix is removed from item keys.
    """
        prefix, n = '{}_'.format(section) , (0 if not strip else len(section) + 1)
        return { k[n:]:v for (k,v) in fulldict.items() if k.startswith(prefix) }




######################################################################
# exported routines
######################################################################
def set_visualization_option_defaults(custom_defaults={}, search_env=True):
    """
    Args:
        custom_defaults: dict of {option:new_default_value} records
        search_env:      True/False to enable/disable scanning environment variables
                         for option settings
    """
    _init_visualization_options(custom_defaults=custom_defaults, search_env=search_env)


def get_visualization_options(options, section='default', overrides={}):
    """Return currently configured values of options.

    Args:
        options (list of str):  names of options
        section (str): name of section
        overrides (dict): {option:value} records to override current settings

    Returns:
        List of option values.
    """
    global _visualization_sections
    if _visualization_sections == {}:
        _init_visualization_options()

    almanac = _visualization_sections.get(section, None)
    if almanac is None:
        warn('unknown options section {} (skipping)'.format(section))
        return None

    _overrides = overrides if section=='default' else _subdict(overrides,section)

    return [ almanac(opt, section, _overrides) for opt in options ]


def get_visualization_option(option, section='default', overrides={}):
    return get_visualization_options([option],section,overrides)[0]


######################################################################
# Definitions of options and section-specific default values
#####################################################################

""" names, default values, descriptions of visualization options """
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


""" sections and section-specific defaults """
VISUALIZATION_SECTIONS = {
#
    'eps': { 'cmap': 'blues', 'linewidth': 0.0 },
#
    'src_region': { 'linewidth': 4.0, 'linecolor': '#0000ff', 'fontsize': 0 }

}

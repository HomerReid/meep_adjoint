. include ../Preamble.rst

######################################################################
Configuration and customization
######################################################################

:py:mod:`meep_adjoint` is highly customizable, offering a large number
of user-configurable options and a convenient hierarchical framework
for setting and updating their values.


======================================================================
What sorts of options are available, and how are they organized?
======================================================================

The full set of configuration options is detailed in the
reference section below, but here are some quick points.


======================================================================
:py:mod:`meep_adjoint` look for option settings, and 
======================================================================

1. Package-level defaults:
Each option

2. Script-level defaults:

3. User-global configuration file:

4. User-local configuration file:

5. Command-line arguments.

6. API function parameters.


********************
General overview
********************

Internally, the module maintains two separate databases of option
settings: one for options that specifically affect the appearance of
visualization plots, and a second for all other options. [This is
done both **(1)** to facilitate a possible future refactoring of the adjoint
and visualization modules into separate standalone packages, and
**(2)** because the visualization module handles option settings in a
slightly more complicated way than does the adjoint module, as
discussed below.] Both databases are instances of the simple
class :py:class:`OptionAlmanac`, which combines the functionality
of the `configparser_` and `argparse_` modules in the python standard
library.


.. _argparse: https://docs.python.org/3/library/argparse.html#module-argparse
.. _configparser: https://docs.python.org/3/library/configparser.html?highlight=configparser#module-configparser


The hierarchy of sources for option settings
==============================================

As noted above, the module consults multiple sources---in a specific
order---for user-specified option settings; any conflicts are adjudicated in favor
of the later-encountered source, i.e. new option settings always overwrite
existing settings [1]_.

.. [1] An exception is the case in which the *type* of an option setting
is incompatible with the type of the existing option value; in this case 
the new setting is ignored with a warning and the previous option value 
retained.

More specifically, the value stored in the
internal database for a given configuration option is initialized
and then updated according to the following sequence:

1. The original default value hard-coded in the `meep_adjoint` source distribution.

2. The updated default value specified by a call to
   `meep_adjoint::set_adjoint_option_defaults()` from a user script.

3. The value specified in the `global configuration file`_, if any.

4. The value specified in the `local configuration file`_, if any.

5. The value of the option as an environment variable, if set.

6. The value of the option as a command-line argument, if specified.

.. _`global configuration file`:

    `local configuration file`_


.. _`local configuration file`:


Global and local configuration files
--------------------------------------------------

The configuration files parsed for adjoint and visualization options are as follows.

    * **Global**:    :file:`~/.meep_adjoint.rc`, :file:`~/.meep_visualization.rc`

    * **Local**:    :file:`./meep_adjoint.rc`, :file:`./meep_visualization.rc`

Note that global files lie in the user's home directory and are "dotfiles", i.e.
have filenames that begin with a period.
Local files lie in the current working directory and have the same filename
as their global counterparts, minus the leading period.


Configuration-related API routines
==============================================


********************
Adjoint options
********************



************************
Visualization options
************************



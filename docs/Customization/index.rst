.. include /Preamble.rst

######################################################################
Configuration and customization
######################################################################

:py:mod:`meep_adjoint` is highly customizable, offering a large number
of user-configurable options and a convenient hierarchical framework
for setting and updating their values.


======================================================================
Setting
======================================================================

The protocol for option-handling 

is designed to allow each option to be specified in 

The option-processing subsystem considers a 
configuration options to be specified in 

option-handling mechanism is to
each configuration
option to be set 

For each configuration option, :py:mod:`meep_adjoint` consults a

an
values to be 
configuration files, environment variables, command-line arguments,
and parameters to API functions.

The protocol for specifying option values is intended to


The full set of configuration options is detailed in the
reference section below, but here are some quick points.

:general options:

  * would look like this. 

        *italic*
        **bold**

  * Howdage foryaf!

        This ``*`` character is not interpreted

  * And the **note** below should be inline.

    .. note:: If asterisks or backquotes appear in running text and could be confused with inline markup delimiters, they have to be escaped with a backslash.

:visualization options:

    Be aware of some restrictions of this markup:

    * it may not be nested,
    * content may not start or end with whitespace: ``* text*`` is wrong,
    * it must be separated from surrounding text by non-word characters. 

    Use a backslash escaped space to work around that:

    * ``this is a *longish* paragraph`` is correct and gives *longish*.
    * ``this is a long*ish* paragraph`` is not interpreted as expected. You 
      should use ``this is a long\ *ish* paragraph`` to obtain long\ *ish* paragraph


.. seealso:: Howdage foryaf.

    This is my "seealso" block, which is wonderfatul.


.. todo:: Remaining stuff todo foryaf.

    This is my "todo" block, which sucks.


Now is the time for all good men to come to the aid of their country.


.. sidebar:: Will I need sidebars?
        :subtitle: The price of fame

    I will here describe the price of fame foryaf.


.. glossary::

    apical
        at the top of the plant.

    howdage
        doomatage 

    `goofy`
        doomatage 


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

.. topic:: My subtopic foryaf

    This is what my subtopic looks like foryaf.


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

--------------------------------------------------
Options affecting :codename:meep geometries
--------------------------------------------------

-res          resolution
-fcen         center frequency

--very-long-option
              The description can also start on the next line.

              The description may contain multiple body elements,
              regardless of where it starts.

-x, -y, -z    Multiple options are an "option group".
-v, --verbose  Commonly-seen: short & long options.
-1 file, --one=file, --two file
              Multiple options with arguments.
/V            DOS/VMS-style options too


**************************************************
Trying csv tables...
**************************************************

.. csv-table:: Frozen Delights!
   :header: "Treat", "Quantity", "Description"
   :widths: 15, 10, 30

   "Albatross", 2.99, "On a stick!"
   "Popcorn", 1.99, "Straight from the oven"



************************
New header
************************


.. centered:: 

    Not sure if this will work.

    If it *did* work, the text will appear here.
    :Whatever: This is handy to create new field.


.. warning:: 

    This is really a very painful process.


.. index:: 

************************
Visualization options
************************



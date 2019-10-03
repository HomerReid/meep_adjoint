***************************************************************************************
Low-level (private) API: Classes and functions intended for use within :obj: `meep_adjoint`
***************************************************************************************

================================================================================
:class:`TimeStepper`: Interface to back-end computational engine
                      codename:`meep` or other FDTD
================================================================================

.. _TheOptimizationProblemClass:

.. autoclass:: OptimizationProblem
   :inherited-members:


==========================================================================================
Package-level functions for accessing configuration options
==========================================================================================

----------------------------------------------------------------------
Adjoint-solver options
----------------------------------------------------------------------

.. autofunction:: meep_adjoint.get_adjoint_option

.. autofunction:: meep_adjoint.set_adjoint_option_defaults

----------------------------------------------------------------------
Visualization options
----------------------------------------------------------------------

.. autofunction:: meep_adjoint.get_visualization_option

.. autofunction:: meep_adjoint.get_visualization_options

.. autofunction:: meep_adjoint.set_visualization_option_defaults

.. autofunction:: meep_adjoint.set_option_defaults

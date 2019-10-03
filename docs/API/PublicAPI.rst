****************************************************************************************
High-level API: Exported classes and functions
****************************************************************************************

.. _TheOptimizationProblemClass:


==========================================================================================
:class:`OptimizationProblem`: Top-level class that drives :obj:`meep_adjoint` sessions
==========================================================================================

.. autoclass:: OptimizationProblem
   :inherited-members:


==========================================================================================
Module-wide routines for accessing configuration options
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

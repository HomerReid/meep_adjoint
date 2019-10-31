***********************************************************************************************
Low-level (private) API: Classes and functions intended for use within :obj:`meep_adjoint`
***********************************************************************************************

============================================================================================================
:class:`TimeStepper`: Interface to computational back-end provided by :codename:`meep` or other FDTD solver
============================================================================================================

.. _TheTimeStepperClass:

.. autoclass:: meep_adjoint.TimeStepper
   :inherited-members:


============================================================================================================
:class:`ObjectiveFunction`: Evaluation of objective-function values and partial derivatives
============================================================================================================

.. _TheObjectiveFunctionClass:

.. autoclass:: meep_adjoint.ObjectiveFunction
   :inherited-members:


============================================================================================================
:class:`DFTCell`: Storage for frequency-domain field components and evaluation of objective quantities
============================================================================================================
.. _TheDFTCellClass:

.. autoclass:: meep_adjoint.DFTCell
   :inherited-members:

============================================================================================================
:class:`Subregion`: Rationalized, unified handling of spatial subregions
============================================================================================================
.. _TheSubregionClass:

.. autoclass:: meep_adjoint.Subregion
   :inherited-members:

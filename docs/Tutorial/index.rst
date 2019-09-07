.. include ../Preamble.rst

********************************************************************************
:py:mod:`meep_adjoint` tutorial
********************************************************************************

Having outlined what |mpadj| is good for and sketched a typical workflow
the :doc:`Overview <Overview/index>`, we now get down to the nitty-gritty:
a blow-by-blow walkthrough of a typical design-automation problem as


======================================================================
The problem: optimal routing of optical power
======================================================================

The geometry we will consider is a four-port optical router, consisting of a
central hub from which emanate waveguides carrying incoming and outgoing optical
signals; our objective will be to optimize the design of the hub region to achieve
optimal routing of input power from one or more given input ports to one or more
desired output ports.

Evidently, different choices of input and output ports define different optimization
problems, and we will discuss how this is reflected by the python scripts we write
to drive the optimization. For most of this tutorial we will consider the specific
problem of routing incoming signals arriving on the **West** port entirely to the
**North** port with (ideally) zero power emission from the **East** or **South**
ports.


==================================================
Creating an :py:class:`OptimizationProblem`
==================================================

The first step in any :py:mod:`meep_adjoint` workflow is to create an
instance of :py:class:"`OptimizationProblem`


==================================================
Creating an :py:class:`OptimizationProblem`
==================================================


.. include ../Postamble.rst

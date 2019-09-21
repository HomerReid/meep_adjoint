.. include ../Preamble.rst

********************************************************************************
:py:mod:`meep_adjoint` tutorial
********************************************************************************

Having outlined on the :doc:`previous page <Overview/index>` some of the
big-picture story---how :py:mod:`meep_adjoint` fits into the larger
design-optimization ecosystem, and what you can expect to put into and 
get out of a typical session---we now delve into the details.
We will present a step-by-step walkthrough of a :py:mod:`meep_adjoint` session
that, starting from scratch, automagically finds intricate and *highly*
non-intuitive device designs whose performance far exceeds anything we
could hope to design by hand.


======================================================================
The problem: optimal routing of optical power
======================================================================

The engineering problem we will be considering is the design of
*interconnect router* devices for optical networks. Our router devices 
are simply 
we 
are just rectangular (2D) or box-shaped (3D()


with four ports



is t

is to 
route optical 

device we will be considering in this example is an optical-networking
*interconnect router*---or, at least, a router is 
it will be after we've taken our crack at
optimizing its design; when we *start* it is simply a rectangular

we will *start*

networking 
router, consisting of a
central hub
from which emanate waveguides carrying incoming and outgoing optical
signals; our objective will be to optimize the design of the hub region to achieve
optimal routing of input power from one or more given input ports to one or more
desired output ports.

Evidently, different choices of input and output ports define different optimization
problems, and we will discuss how this is reflected by the python scripts we write
to drive the optimization. For most of this tutorial we will consider the specific
problem of routing incoming signals arriving on the **West** port entirely to the
**North** port with (ideally) zero power emission from the **East** or **South**
ports.

======================================================================
Phases of a :py:mod:`meep_adjoint` session
======================================================================


==================================================
Phase 1: Creating an :py:class:`OptimizationProblem`
==================================================

The first step in any :py:mod:`meep_adjoint` workflow is to create an
instance of :py:class:`OptimizationProblem`. This class is
analogous to the `Simulation <Simulation_>`_ class in
the core :program:meep python module.

.. _Simulation:  https://meep.readthedocs.io/en/latest

.. code-block:: python
   :linenos:
   :emphasize-lines: 3,5
   :caption: this.py
   :name: this-py

   print 'Explicit is better than implicit.'


And this would be a literal include foryaf:


.. literalinclude:: ../Examples/CrossRouter.py


==================================================
Creating an :py:class:`OptimizationProblem`
==================================================


.. include ../Postamble.rst

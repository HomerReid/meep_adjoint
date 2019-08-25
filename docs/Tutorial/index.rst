********************************************************************************
:py:mod:`meep_adjoint` tutorial
********************************************************************************

Having outlined what `meep_adjoint` is good for and sketched a typical workflow
the :doc:`Overview <Overview/index>`, we now get down to the nitty-gritty:
a blow-by-blow walkthrough of a typical design-automation problem solved by
`meep_adjoint.`


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
to drive the optimization; for most of this tutorial we will consider the specific
problem of routing incoming power arriving on the **West** 


--------------------------------------------------


Initializing an `OptimizationProblem`
==================================================

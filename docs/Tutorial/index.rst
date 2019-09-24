.. include ../Preamble.rst


********************************************************************************
:py:mod:`meep_adjoint` tutorial
********************************************************************************

Having outlined on the :ref:`previous page <TheOverview>` some of the
big-picture story---how :py:mod:`meep_adjoint` fits into the larger
design-optimization ecosystem, and what you can expect to put into and 
get out of a typical session---on this page we get down to details.
We will present a step-by-step walkthrough of a :py:mod:`meep_adjoint` session
that, starting from scratch, automagically finds intricate and *highly*
non-intuitive device designs whose performance far exceeds anything we
could hope to design by hand.


======================================================================
The problem: optimal routing of optical power
======================================================================
The engineering problem we will be considering is the design of
*interconnect router* devices for optical networks. For our purposes,
a router is a hunk of lossless dielectric material, confined within
a rectangular (2D) or box-shaped (3D) region of given fixed dimensions,
from which emanate four stub waveguides (of given fixed sizes and materials)
representing I/O ports, which we label simply **East**, **West**, **North**, and
**South**.

The router will live inside an optical-network switch with
each port connected to a fiber-optic cable carrying incoming and outgoing
signals, and our job is to design the central hub to ensure that signals
arriving on some given set of input ports are routed to some given set
of output ports with optimality according to some given set of 
desiderata. Evidently, different choices of input and output ports
and performance criteria yield different optimization problems, and we will
show how this freedom is reflected in the :mod:`meep_adjoint` API and
our python driver scripts; then, for most this tutorial, we will focus
on two particular design tasks:


    * **Right-angle router:** Steer incoming signals arriving on the **West**
      port through a 90-degree bend to depart via the **North** port.
      Here the design objective is simply to maximize transfer of signal
      power from input to output, minimizing losses due to leakage power
      emissions from the  **South** or **East** ports.


    * **Three-way splitter:** Split an input signal arriving on the **West**
      port into three equal-power output signals departing via the
      **North**, **South,** and **East** ports. For this task
      we will suppose that the design objective is not maximum
      output power, but rather maximal *uniformity* of power
      emissions from the three output ports.


======================================================================
Phases of a :py:mod:`meep_adjoint` session
======================================================================
Like all :mod:`meep_adjoint` sessions,
this walkthrough will proceed in three stages:


1. **Initialization phase:** *Defining the optimization problem*

        The first step is to identify all of the
        :ref:`ingredients needed to define our design-optimization problem <OptProbIngredients>`
        and communicate them to :mod:`meep_adjoint` in the form of
        arguments passed to the :class:`OptimizationProblem` constructor.
        The class instance we get back will furnish the
        portal through which we access :mod:`meep_adjoint` functionality
        and the database that tracks the evolution of our design
        and its performance.


2. **Interactive phase:** *Single-point calculations and visualization*

        Before initiating a lengthy, opaque machine-driven
        design iteration, we will first do some *human*-driven
        poking and prodding to kick the tires of our
        :class:`OptimizationProblem`---both to make sure we defined the
        problem correctly, and also to get a feel for how challenging
        it seems, which will inform our choice of convergence criteria
        and other parameter settings for the automated phase.
        More specifically, in this phase we will invoke
        :mod:`meep_adjoint` API routines to do the following:


            A. update the design function :math:`\epsilon^\text{des}(\mathbf{x})`---that is,
               move to a new point :math:`\boldsymbol{\beta}`
               in design space


            B. numerically evaluate the objective-function value :math:`f^\text{obj}(\boldsymbol{\beta})`
               at the current design point


            C. numerically evaluate the objective-function *gradient* :math:`\boldsymbol{\nabla} f^\text{obj}`
               at the current design point 


            D. produce graphical visualizations of both the device geometry---showing
               the spatially-varying permittivity distribution of the current design---and
               the results of the :codename:`meep` calculations of the previous two
               items, showing the spatial configuration of electromagnetic fields produced
               by the current iteration of the device design.

 
        Because steps B, C, and D here are executed with the device geometry held fixed at the
        design point chosen in step A, we refer to them as *single-point* operations.
        Of course, of all the single-point tests we might run in our interactive investigation,
        perhaps the most useful is

            E. *check* the adjoint calculation of step C above
               by slightly displacing the design point in the direction
               of the gradient reported by :py:mod:`meep_adjoint` and
               confirming that this does, in fact, improve the value
               of the objective function---that is, compute
               :math:`f^\text{obj}\Big(\boldsymbol{\beta} + \alpha\boldsymbol{\nabla} f\Big)`
               (with :math:`\alpha\sim 10^{-2}` a small scalar value)
               and verify that it is an improvement over the result of step B above.


3. **Automated phase:** *Fully machine-driven iterative design optimization*

        Once we've confirmed that our problem setup is correct
        and acquired some feel for how it behaves in practice,
        we'll be ready to hand it off to a numerical optimizer
        and hope for the best. We will discuss 
 



|thickline|




==================================================
Phase 1: Creating an :class:`OptimizationProblem`
==================================================

The first step in every :py:mod:`meep_adjoint` workflow is
to create an instance of :py:class:`OptimizationProblem`.
This class plays for :mod:`meep_adjoint` a role
analogous to the `Simulation <Simulation_>`_ class in
the core :mod:`pymeep` module: it


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


==================================================
Glossary foryaf:
==================================================

.. glossary::

GitHub
    GitHub is a web-based Git repository hosting service. It offers all of the distributed version control and source code management (SCM) functionality of Git as well as adding its own features. It provides access control and several collaboration features such as bug tracking, feature requests, task management, and wikis for every project.


RST
    |RST| is an easy-to-read, what-you-see-is-what-you-get plaintext markup syntax and parser system. It is useful for in-line program documentation (such as Python docstrings), for quickly creating simple web pages, and for standalone documents. |RST| is designed for extensibility for specific application domains. The |RST| parser is a component of Docutils.

Sphinx
    Sphinx is a tool that makes it easy to create intelligent and beautiful documentation. It was originally created for the Python documentation, and it has excellent facilities for the documentation of software projects in a range of languages.

Sublime Text
    Sublime Text is a sophisticated text editor for code, markup and prose. You'll love the slick user interface, extraordinary features and amazing performance.

Substitution
    Substitutions are variables that you can add to text. If the value changes, you change it in one place, and it is updated throughout documentation. See :ref:`Use a Substitution`.




.. |thickline| raw:: html 

   <hr class="thick">


.. include ../Postamble.rst

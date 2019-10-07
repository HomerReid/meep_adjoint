********************************************************************************
Tutorial walkthrough
********************************************************************************

Having outlined on the :ref:`previous page <TheOverview>` some of the
big-picture story---how :obj:`meep_adjoint` fits into the larger
design-optimization ecosystem, and what you can expect to put into and
get out of a typical session---on this page we get down to details.
We will present a step-by-step walkthrough of a :obj:`meep_adjoint` session
that, starting from scratch, automagically finds intricate and *highly*
non-intuitive device designs whose performance far exceeds anything we
could hope to design by hand.


======================================================================
The problem: optimal routing of optical power flows
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
show how this freedom is reflected in the :obj:`meep_adjoint` API and
our python driver scripts. For most this tutorial, we will focus
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


The driver script for this problem is 'Router.py',
which lives in the `examples` subdirectory of the `meep_adjoint`
source distribution.


.. admonition:: |RouterPyTitle|
   :class: code-listing

   .. literalinclude:: /Examples/Router.py
       :linenos:
       :name:    `router-py-listing`
       :class:   `code-listing`


.. |RouterPyTitle| raw:: html

       File: <code xref>examples/Router.py</code>
      <a href="javascript:showhide(document.getElementById('router-py-listing'))">   (Click to show/hide)   </a>



======================================================================
Phases of a :obj:`meep_adjoint` session
======================================================================
This tutorial consists of three parts, corresponding to the three
stages of a typical :obj:`meep_adjoint` session:


    .. glossary::


        :ref:`1. Initialization <Phase1>`: *Defining the problem and initializing the solver*


           The first step is to identify all of the
           :ref:`ingredients needed to define our design-optimization problem <OptProbIngredients>`
           and communicate them to :obj:`meep_adjoint` in the form of
           arguments passed to the :class:`OptimizationProblem` constructor.
           The class instance we get back will furnish the
           portal through which we access :obj:`meep_adjoint` functionality
           and the database that tracks the evolution of our design
           and its performance.

           The initialization phase also typically involves setting appropriate
           customized values for the many :ref:`configuration options </Customization/index>`
           affecting the behavior of :obj:`meep_adjoint`.


           |br|




        :ref:`2. Interactive exploration <Phase2>`: *Single-point calculations and visualization*

           Before initiating a lengthy, opaque machine-driven
           design iteration, we will first do some *human*-driven
           poking and prodding to kick the tires of our
           :class:`OptimizationProblem`---both to make sure we defined the
           problem correctly, and also to get a feel for how challenging
           it seems, which will inform our choice of convergence criteria
           and other parameter settings for the automated phase.
           More specifically, in this phase we will invoke
           :obj:`meep_adjoint` API routines to do the following:


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


           Because steps B, C, and D here are executed with the device design held fixed
           at a single point in design space, we refer to them as static or *single-point*
           operations, to be distinguished from the dynamic multi-point trajectory through
           design space traversed by the automated design optimization of the following stage.

           Of course, of all the single-point tests we might run in our interactive investigation,
           perhaps the most useful is

               E. *check* the adjoint calculation of step C above
                  by slightly displacing the design point in the direction
                  of the gradient reported by :obj:`meep_adjoint` and
                  confirming that this does, in fact, improve the value
                  of the objective function---that is, compute
                  :math:`f^\text{obj}\Big(\boldsymbol{\beta} + \alpha\boldsymbol{\nabla} f\Big)`
                  (with :math:`\alpha\sim 10^{-2}` a small scalar value)
                  and verify that it is an improvement over the result of step B above.


           |br|


        :ref:`3. Automation <Phase3>`: *Machine-driven iterative design optimization*

           Once we've confirmed that our problem setup is correct
           and acquired some feel for how it behaves in practice,
           we'll be ready to hand it off to a numerical optimizer
           and hope for the best. As we will demonstrate, the easiest way
           to proceed here is
           to invoke the simple built-in gradient-descent optimizer
           provided by :obj:`meep_adjoint`---which, we will see, is
           more than adequate to yield excellent results for the
           specific problems addressed in this tutorial---but we will also
           show how, with only slightly more effort, you can
           use your favorite external gradient-based optimization package
           instead.


.. _Phase1:

==================================================
Phase 1: Problem definition and initialization
==================================================

--------------------------------------------------
Creating an :class:`OptimizationProblem`
--------------------------------------------------

The first step in every `meep_adjoint` workflow is
to create an instance of :class:`OptimizationProblem<meep_adjoint.OptimizationProblem>`.
This class plays for :obj:`meep_adjoint` a role
analogous to that of the |simulation| class in the core |pymeep|:
its public methods offer access to the computational
capabilities of the solver, and its internal data fields
keep track of all data and state needed to track the
progress of a computational session.

The :class:`OptimizationProblem<OptimizationProblem>` constructor accepts a
large number of required and optional input arguments, whose setup
will typically occupy a straightforward but somewhat lengthy chunk
of your driver script. You will find documentation for the full set
of arguments in the :ref:`API reference </API/HighLevel>`,
but in most cases you'll probably be able simply to copy the initialization 
code from :mod:`Router.py`
or one of the other :ref:`worked examples <Examples/index>` and modify as appropriate
for your problem. 
Roughly speaking, the inputs needed to instantiate an :class:`OptimizationProblem`
may be grouped into three categories:

    * parameters describing the underlying FDTD simulation geometry

    * parameters describing the objective function and how it is computed

    * parameters describing the design space and the tweakable degrees of freedom

.. topic:: Parameters describing the underlying FDTD simulation geometry:

    :`cell_size`:

        List or `numpy` array of computational cell dimensions,
        identical to the parameter of the same name passed to the
        |simulation| constructor.
        

    :`background_geometry`:
    :`foreground_geometry`:

        List of |MeepGeometricObject| structures describing material
        bodies in the geometry, *not* including the design region,
        for which :mod:`meep_adjoint` automatically creates an
        appropriate object internally. The "background" and "foreground"
        lists contain objects that logically lie "beneath" and "above"
        the design region; internally, these lists are concatenated,
        with the automatically-created design object in between,
        to form the list of objects passed as the `geometry` parameter
        of |simulation|.


    :`sources`:

        List of |MeepSource| structures describing excitation sources,
        passed without modification as the parameter of the same name
        to the |simulation| constructor.[#f1]_


    :`source_region`:

        This is a convenience argument that may be used instead of
        `sources` for problems with only a single excitation source.
        If present, `source_region` should be a :class:`Subregion`
        (or a |MeepVolume|) specifying the spatial extent of
        the source, which :obj:`meep_adjoint` will use together
        with the values of :ref:`configuration options</Customization/index>`[#f2]_
        to construct a single-element list passed as the
        `sources` parameter to the |simulation| constructor.
        

.. topic:: Parameters describing the objective function and how it is computed

    :`objective`:


    :`objective_regions`:

        List of :class:`Subregion` structures


.. topic:: Parameters describing the design space and the tweakable degrees of freedom

        


.. code-block:: python
   :linenos:
   :emphasize-lines: 3,5
   :caption: this.py
   :name: this-py

   print 'Explicit is better than implicit.'


.. _Phase2:

==================================================
Phase 2: Interactive exploration
==================================================


.. _Phase3:

==================================================
Phase 3: Automated optimization
==================================================


.. [#f1] To clarify, these are the sources for the *forward* simulation; sources for the *adjoint* simulation are determined automatically within :obj:`meep_adjoint`.

.. [#f2] More specifically, the following configuration options
         are referenced: `fcen`, `df`, `source_component`, and `source_mode`.

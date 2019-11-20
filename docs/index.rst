.. module:: meep_adjoint

***********************************************************************************
:obj:`meep_adjoint`: A python package for adjoint sensitivity analysis in MEEP
***********************************************************************************
This is the root of the documentation tree for :obj:`meep_adjoint`.
Jump directly to the package-wide :ref:`TableOfContents` below,
or read on for a quick-start summary.

============================
What does this package do?
============================
You'll find a longer answer in the :doc:`Overview <overview/index>`
(and a more succinct one in the :doc:`API Reference <API/HighLevel>`),
but, in a nutshell: It extends the computational capabilities of the
core |meep| solver in a particular way that facilitates interaction
with `numerical optimization algorithms`_, opening the door to
intelligent design tools that automatically design devices to meet
given performance specifications.


.. admonition:: Wait, *what* exactly does the package do again?

        If that was a bit vague, we can be more specific about precisely what
        :obj:`meep_adjoint` does. Consider a typical design problem
        in which we seek to tune a device geometry to optimize some
        performance metric.
        For example, in the :doc:`right-angle router <example_gallery/router>`
        example in the :obj:`meep_adjoint`
        :doc:`example gallery <example_gallery/index>`,
        we are designing a four-waveguide interconnect for an optical network,
        and our goal is to choose the permittivity distribution
        :math:`\epsilon(\mathbf{x})` in the junction region to steer
        incoming optical signals arriving on the **West** port
        around a 90-degree bend to the **North** port, ideally
        with zero leakage power emitted from the **South** and
        **East** ports:


        **Mathematical formulation of design-optimization problems**

        To formulate this problem mathematically so we can
        hand it off to a numerical optimizer, we might begin by
        expressing the unknown design function as an expansion
        in some convenient finite set of basis functions:

        .. math::

            \epsilon(\mathbf x)\approx\sum_{d=1}^D \beta_d b_d(\mathbf x)

        Then each possible design configuration corresponds to a :math:`D`-dimensional vector of
        coefficient values :math:`\boldsymbol{\beta}=\{\beta_1,\cdots,\beta_D\}`, while the metric
        defining the performance of a design---the quantity we are trying to
        optimize---is a (real-valued, scalar) function of a vector-valued argument,
        the *objective function* :math:`f^\text{obj}(\boldsymbol{\beta}).` For the
        right-angle router with fixed input power entering the **West** port,
        we could define our objective to be simply to maximize output power from 
        the **North** port, i.e.


        .. math::


            f^\text{obj}(\boldsymbol{\beta}) = S_\text{North} \tag{1}


        where :math:`S_\text{North}` denotes the outgoing power flux
        (integral of normal Poynting vector) through the **North** flux monitor.
        Alternatively, assuming the input power is delivered in its entirety
        by a single mode---call it mode :math:`m`--- of the **West** waveguide (as 
        would be the case if we excited our FDTD simulations with an |MeepEigenmodeSource|
        tuned to mode :math:`m`),
        we could optimize for maximal output power carried by mode :math:`m` of the
        **North** waveguide, or equivalently for maximal magnitude of the
        forward-traveling b`mode-expansion coefficient`_ 
        evaluated at the **North** flux monitor, in which case we would instead have


        .. math::

            f^\text{obj}(\boldsymbol{\beta}) = |P^m_\text{North}|^2 \tag{2}

        where :py:`P^m_\text{North}` denotes the coefficient
        of the `math`:$m$th forward-traveling waveguide mode at the **North**
        flux monitor. 
        (The use of symbols :math:`S` and :math:`P^m` respectively for Poynting flux
        and forward-traveling mode-expansion coefficient is part of the
        `meep_adjoint` rules for labeling objective quantities.)

        

        **Mathematical formulation of design-optimization problems**
        

        
        For our
        in the router problem
        a real-valued scalar
        device given by a
        and we can picture the process of device optimization
        as a journey through a :math:`D`-dimensional space in
        search of the magical point :math:`\boldsymbol{\beta}_*`
        at which
        single point moving through a
        location. To the performance of a
        location. To the performance of a

        For a

        or equivalently to a :math:`D`-dimensional
        vector :math:`{\boldsymbol{\beta}}`,
        ranges
        values of the :math:`D` coefficients
        evice design is specified by the
        :math:`D`-dimensional vector of numbers
        :math:`\boldsymbol{\beta}`


            \sum_{d=1}^D \beta_d b_d(\mathbf x)


       Then, for given fixed values of the input power, operating
       frequency, and other parameters, the design metric we are trying
       to optimize---that is, our *objective function*
       :math:`f^\text{obj}`---may be thought of as a function of the
       :math:`D`-dimensional vector of expansion coefficients
       :math:`\boldsymbol{\beta}`, i.e.


       .. math::

           f^\text{obj}(\boldsymbol{\beta})
           =\text{power output from \textbf{North} port}
           \equiv S_{\text{North}}


        There's just one problem, which perhaps already
        occurred to you if you have any experience with high-dimensional
        optimization:

        and asks for the optimal

       Then, for given fixed values of the input power, operating
       frequency, and other parameters, the ia the **West** input waveguide port




 ^\text{design}(\mathbf x)\approx
       \sum_{d=1}^D \beta_d b_d(\mathbf x)


       Then, for given fixed values of the input power, operating
       frequency, and other parameters, the ^\text{design}(\mathbf x)\approx
       \sum_{d=1}^D \beta_d b_d(\mathbf x)


       Then, for given fixed values of the input power, operating
       frequency, and other parameters, the ia the **West** input
       waveguide port to the **North** output wav



        Here :math:`\epsilon(x)`

        .. math::
          \epsilon(\mathbf x)=\sum \beta_d b_d(\mathbf x)

        Now suppose some region of the material geometry is free
        to be tweaked

        you're a device designer tasked with maximizing
        some performance metric $f$ expressed as a function of these
        output quantities---for example, we might put
        :math:`f=S_2(\omega_3)` to maximize flux through the 2nda
        flux region at the 3rd frequency, or
        :math:`f = (S_1(\omega_3) - S_2(\omega_3))^2`
        to maximize the *difference* between two fluxes, etc.




.. admonition:: The scope of :program:`meep_adjoint`


         **Q.** Does this mean that the package *only* computes objective-function gradients? That is, it doesn't actually do any optimization?

         **A.** The *primary* mission of :obj:`meep_adjoint` is to compute objective-function gradients. This is the task the package guarantees to execute efficiently and accurately,
                and it's one that's self-contained, unambiguous, and easily *testable.* [#]_

         The larger question of how best to *use* gradient information for
         design automation---which involves questions such as which of the
         `myriad available gradient-based optimization algorithms`_ to use,
         and how to configure its tunable parameters---is officially beyond the
         purview of :obj:`meep_adjoint`, and indeed is much too broad
         a problem to be treated with anything approaching comprehensiveness
         by any single package. We hope :obj:`meep_adjoint` will be
         helpful to :obj:`meep` users as they navigate this
         vast domain.


         **With all of that by way of disclaimer,** however, we note that
         :obj:`meep_adjoint` does ship with one (rather simple-minded)
         implementation of an optimization algorithm---namely, a
         :doc:`basic gradient-descent solver.`
         Per the discussion above, we make
         no claim as to the robustness or efficiency of this solver,
         and we encourage users to consider it a first step in the
         process of optimizing any geometry, to be replaced by more
         sophisticated solvers as necessary; but, having said that,
         we note that the simple built-in optimizer suffices to
         yield good results on all the problems considered in
         the :doc:`example gallery <example_gallery/index>`.


=======================================
What does a typical workflow look like?
=======================================

You'll find a full step-by-step walkthrough in the
:doc:`Tutorial <tutorial/index>` and additional guided case studies
in the :doc:`Example gallery <example_gallery/index>`, but here is a
quick rundown:


1) *Initialization and Problem Definition:*
You begin by creating an instance of :class:`optimization_problem`
This is the top-level python class exported by :obj:`meep_adjoint`,
analogous to the |simulation|
class in the core |pymeep|; it stores all data and state
relevant to the progress of a design optimization, and
you will access most :obj:`meep_adjoint` functionality
via its class methods.

2) *Interactive single-point calculations*  Before
launching a full-blown iterative optimization run that
could run for hours or days, you will probably want
to run some sanity-check calculations involving your
geometry. These include...**(section incomplete)**

3) *Full iterative optimization*: Launch your optimization
run and monitor its progress via graphical or other indicators.


====================================
How is the documentation structured?
====================================

.. _TableOfContents:

===================================
Table of Contents
===================================

.. toctree::
   :maxdepth: 3
   :caption: Documentation Home

   self


.. toctree::
   :maxdepth: 3
   :caption: Overview and Invitation

   Overview <overview/index>
   Tutorial <tutorial/index>
   Example Gallery <example_gallery/index>



.. toctree::
   :maxdepth: 3
   :caption: Reference

   Installation <installation/index>
   Configuration and customization <customization/index>
   General reference <reference/index>
   Visualization Module <visualization/index>
   Test suite <test_suite/index>



.. toctree::
   :maxdepth: 3
   :caption: Implementation notes

   Implementation I: Physics and math  <implementation/MathAndPhysicsOfAdjoints>
   Implementation II: Class hierarchy <implementation/ClassHierarchy>


.. toctree::
   :maxdepth: 3
   :caption: API Reference

    High-level (public) API <API/HighLevel>
    Low-level (internal) API <API/LowLevel>



==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



..######################################################################
..######################################################################
..######################################################################

.. _numerical optimization algorithms: https://en.wikipedia.org/wiki/Category:Optimization_algorithms_and_methods

.. _mode-expansion coefficient: https://meep.readthedocs.io/en/latest/Mode_Decomposition/

.. _myriad available gradient-based optimization algorithms: https://en.wikipedia.org/wiki/Category:Optimization_algorithms_and_methods

.. _Simulation:  https://meep.readthedocs.io/en/latest

.. [#] For example, one obvious test of the correctness
       of :obj:`meep_adjoint` is to estimate objective-function
       derivatives by numerical finite-differencing and compare to
       components of the adjoint-method gradient. This is the basis
       of one of the tests in the :obj:`meep_adjoint` unit-test suite,
       and also of the :doc:`holey waveguide <example_gallery/holey_waveguide>`
       example in the :doc:`example gallery.<example_gallery/index>`


.. |meep| raw:: html

   <a class="codename" href="http://meep.readthedocs.io">meep</a>


.. |mpadj| raw:: html

   <a href="https://homerreid.github.io/meep-adjoint-documentation/index.html"><code xref>meep_adjoint</code></a>

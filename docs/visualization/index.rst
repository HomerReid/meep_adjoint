**********************************************************************
Visualization module 
**********************************************************************

The :mod:`meep_adjoint` package ships with a built-in visualization
module to facilitate graphical inspection of geometries and
computational results in `meep_adjoint` geometries. (A similar
module was later added to core meep.) 

More specifically,
the visualization module knows how to produce three types of plots:

    1. *Geometry plots*,
       showing the material configuration throughout the computational
       cell of the problem, the PML layers, the finite-element mesh
       used to define the basis set (for problems using a 
       :class:`FiniteElementBasis <meep_adjoint.FiniteElementBasis>`),
       and significant subregions such as source regions,
       objective regions, and the design region.

    2. *Forward field plots*, showing the results of forward timestepping
       calculations, particularly the spatial distribution of
       energy fluxes and energy densities used to compute the objective
       function :math:`f^\text{obj}`.

    3. *Adjoint derivative plots*, showing the results of adjoint
       timestepping calculations---specifically, the quantity
       :math:`\frac{\partial f^\text{obj}}{\partial \epsilon(\mathbf x)}`
       as a function of :math:`\mathbf{x}` throughout the design region.

In generating these plots,

    + *executive mode*, in which the user simply invokes the
      `visualize` method of `OptimizationProblem`---with no 
      arguments!---and the visualization module automatically
      chooses not only the best default options for the plot,
      but also *which* of the above three plots to produce,
      based on the current state of 


    + *expert mode*, in which the user configures the parameters
      to `visualize` to control the plot produced and its appearance.

----------------------------------------------------------------------
Visualization in executive mode
----------------------------------------------------------------------

----------------------------------------------------------------------
Visualization in expert mode
----------------------------------------------------------------------


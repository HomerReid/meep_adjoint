"""OptimizationProblem is the top-level class exported by the meep.adjoint module.
"""
import os
import inspect

import meep as mp

from . import (DFTCell, ObjectiveFunction, TimeStepper, ConsoleManager,
               FiniteElementBasis, dft_cell_names, E_CPTS, v3, V3)

from . import visualize_sim

from . import get_adjoint_option as adj_opt
from .adjoint_options import set_adjoint_options

######################################################################
######################################################################
######################################################################
class OptimizationProblem(object):
    """Top-level class in the MEEP adjoint module.

    Intended to be instantiated from user scripts with mandatory constructor
    input arguments specifying the data required to define an adjoint-based
    optimization.

    The class knows how to do one basic thing: Given an input vector
    of design variables, compute the objective function value (forward
    calculation) and optionally its gradient (adjoint calculation).
    This is done by the __call__ method. The actual computations
    are delegated to a hierarchy of lower-level classes, of which
    the uppermost is TimeStepper.
    """

    def __init__(self, objective_regions=[], objective=None,
                       basis=None, design_region=None,
                       cell_size=None, background_geometry=[], foreground_geometry=[],
                       sources=None, source_region=[],
                       extra_quantities=[], extra_regions=[]):
        """
        Parameters:

          objective regions (list of Subregion):
              subregions of the computational cell over which frequency-domain
              fields are tabulated and used to compute objective quantities

          objective (str):
              definition of the quantity to be maximized. This should be
              a mathematical expression in which the names of one or more
              objective quantities appear, and which should evaluate to
              a real number when numerical values are substituted for the
              names of all objective quantities.


          basis (Basis):
          design_region (Subregion):
              (precisely one of these should be non-None) Specification
              of function space for the design permittivity.

              In general, basis will be a caller-created instance of
              some subclass of meep.adjoint.Basis. Then the spatial
              extent of the design region is determined by basis and
              the design_region argument is ignored.

              As an alternative convenience convention, the caller
              may omit basis and set design_region; in this case,
              an appropriate basis for the given design_region is
              automatically created based on the values of various
              module-wide adj_opt such as 'element_type' and
              'element_length'. This convenience convention is
              only available for box-shaped (hyperrectangular)
              design regions.


          cell_size (Vector3)
          background_geometry (list of GeometricObject)
          foreground_geometry (list of GeometricObject)

              Size of computational cell and lists of GeometricObjects
              that {precede,follow} the design object in the overall geometry.


          sources (list of Source)
          source_region (Subregion)
              (Specify either sources OR source_region) Specification
              of forward source distribution, i.e. the source excitation(s) that
              produce the fields from which the objective function is computed.

              In general, sources will be an arbitrary caller-created list of Source
              objects, in which case source_region, source_component are ignored.

              As an alternative convenience convention, the caller may omit
              sources and instead specify source_region; in this case, a
              source distribution over the given region is automatically
              created based on the values of module-wide adj_opt (such
              as fcen, df, source_component, source_mode)


          extra_quantities  (list of str)
          extra_regions (list of Subregion)
              By default, the module will compute only those DFT fields and
              objective quantities needed to evaluate the specified objective
              function. These arguments may be used to specify lists of ancillary
              quantities and/or ancillary DFT cells (where 'ancillary' means
              'not needed to compute the objective function value) to be computed
              and reported/plotted as well.

        """

        #-----------------------------------------------------------------------
        # process convenience arguments:
        #  (a) if no basis was specified, create one using the given design
        #      region plus global option values
        #  (b) if no sources were specified, create one using the given source
        #      region plus global option values
        #-----------------------------------------------------------------------
        self.basis = basis or FiniteElementBasis(region=design_region,
                                                 element_length=adj_opt('element_length'),
                                                 element_type=adj_opt('element_type'))
        design_region = self.basis.domain
        design_region.name = design_region.name or 'design'

        if not sources:
            f, df, m, c = [ adj_opt(s) for s in ['fcen', 'df', 'source_mode', 'source_component'] ]
            envelope    = mp.GaussianSource(f, fwidth=df)
            kws         = { 'center': V3(source_region.center), 'size': V3(source_region.size),
                            'src': envelope} #, 'eig_band': m, 'component': c }
            sources     = [ mp.EigenModeSource(eig_band=m,**kws) if m>0 else mp.Source(component=c, **kws) ]
        rescale_sources(sources)

        #-----------------------------------------------------------------------
        # initialize lower-level helper classes
        #-----------------------------------------------------------------------

        # DFTCells
        dft_cell_names  = []
        objective_cells = [ DFTCell(r) for r in objective_regions ]
        extra_cells     = [ DFTCell(r) for r in extra_regions ]
        design_cell     = DFTCell(design_region, E_CPTS)
        dft_cells       = objective_cells + extra_cells + [design_cell]

        # ObjectiveFunction
        obj_func        = ObjectiveFunction(fstr=objective,
                                            extra_quantities=extra_quantities)

        # initial values of (a) design variables, (b) the spatially-varying
        # permittivity function they define (the 'design function'), (c) the
        # GeometricObject describing a material body with this permittivity
        # (the 'design object'), and (d) mp.Simulation superposing the design
        # object with the rest of the caller's geometry.
        # Note that sources and DFT cells are not added to the Simulation at
        # this stage; this is done later by internal methods of TimeStepper
        # on a just-in-time basis before starting a timestepping run.
        self.beta_vector     = self.basis.project(adj_opt('eps_func'))
        self.design_function = self.basis.parameterized_function(self.beta_vector)
        design_object   = mp.Block(center=V3(design_region.center), size=V3(design_region.size),
                                   epsilon_func = self.design_function.func())
        geometry        = background_geometry + [design_object] + foreground_geometry
        sim             = mp.Simulation(resolution=adj_opt('res'),
                                        boundary_layers=[mp.PML(adj_opt('dpml'))],
                                        cell_size=V3(cell_size), geometry=geometry)

        # TimeStepper
        self.stepper    = TimeStepper(obj_func, dft_cells, self.basis, sim, sources)

        #-----------------------------------------------------------------------
        # if the 'filebase' configuration option wasn't specified, set it
        # to the base filename of the caller's script
        #-----------------------------------------------------------------------
        if not adj_opt('filebase'):
            script = inspect.stack()[1][0].f_code.co_filename or 'meep_adjoint'
            script_base = os.path.basename(script).split('.')[0]
            set_adjoint_options({'filebase': os.path.basename(script_base)})


    #####################################################################
    # The basic task of an OptimizationProblem: Given a vector of design
    # variables, evaluate the objective function value and (optionally) gradient.
    ######################################################################
    def __call__(self, beta_vector=None, need_gradient=False):
        """Evaluate value and (optionally) gradient of objective function.

        Args:
            beta_vector (np.array):
                vector of design variables (or None to retain existing design)
            need_gradient (bool):
                whether or not the forward run to compute the objective-function
                value will be followed by an adjoint run to compute the gradient.

        Returns: 2-tuple (fq, gradf), where

            fq = np.array([f q1 q2 ... qN])
               = values of objective function & objective quantities

            gradf = np.array([df/dbeta_1 ... df/dbeta_D]), i.e. vector of partial
                    f derivatives w.r.t. each design variable (if need_gradient==True),
                  = None (need_gradient==False)
        """
        if beta_vector:
            self.update_design(beta_vector)

        with ConsoleManager() as manager:
            fq    = self.stepper.run('forward')
            gradf = self.stepper.run('adjoint') if need_gradient else None

        return fq, gradf


    #####################################################################
    # ancillary API methods #############################################
    #####################################################################
    def update_design(self, beta_vector):
        """Update the vector of design variables (expansion coefficients)
           that determine the design function.
           Args:
               beta_vector: real-valued numpy array, length self.basis.dim
           Return value:
               None
        """
        self.beta_vector = beta_vector
        self.design_function.set_coefficients(beta_vector)
        self.stepper.state='reset'


    #####################################################################
    #####################################################################
    #####################################################################
    def visualize(self, options={}):
        """Produce a graphical visualization of the geometry and/or fields
           as appropriate based on the current state of progress.
        """
        if self.stepper.state=='reset':
            self.stepper.prepare('forward')

        bs = self.basis
        mesh = bs.fs.mesh() if (hasattr(bs,'fs') and hasattr(bs.fs,'mesh')) else None

        if self.stepper.state.endswith('.prepared'):
            visualize_sim(self.stepper.sim, self.stepper.dft_cells, mesh=mesh, options=options)
        elif self.stepper.state == 'forward.complete':
            visualize_sim(self.stepper.sim, self.stepper.dft_cells, mesh=mesh, options=options)
        #else self.stepper.state == 'forward.complete':


######################################################################
######################################################################
######################################################################
def rescale_sources(sources):
    """Scale the overall amplitude of a spatial source distribution to compensate
       for the frequency dependence of its temporal envelope.

       In a MEEP calculation driven by sources with a pulsed temporal envelope T(t),
       the amplitudes of all frequency-f DFT fields will be proportional to
       T^tilde (f), the Fourier transform of the envelope. Here we divide
       the overall amplitude of the source by T^tilde(f_c) (where f_c = center
       frequency), which exactly cancels the extra scale factor for DFT
       fields at f_c.

       Args:
           sources: list of mp.Sources

       Returns:
           none (the rescaling is done in-place)
    """
    for s in sources:
        envelope, fcen = s.src, s.src.frequency
        if callable(getattr(envelope, "fourier_transform", None)):
            s.amplitude /= envelope.fourier_transform(fcen)

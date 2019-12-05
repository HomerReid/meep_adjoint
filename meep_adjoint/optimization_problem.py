"""OptimizationProblem is the top-level class exported by the meep.adjoint module.
"""
import os
import inspect

import meep as mp

from . import (DFTCell, ObjectiveFunction, TimeStepper, ConsoleManager,
               FiniteElementBasis, rescale_sources, E_CPTS, v3, V3,
               init_log, launch_dashboard, ConsoleManager)

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

    Parameters:
    -----------
    cell_size : array_like
        Dimensions of computational cell

    background_geometry, foreground_geometry : list of meep.GeometricObject
        Size of computational cell and lists of GeometricObjects
        that {precede,follow} the design object in the overall geometry.

    source_region : meep.Subregion
        source region bounding box (to be used in lieu of `sources`)

    sources : list of meep.Source
        (*either* `sources` **or** `source_region` should be non-None)
        Specification of forward source distribution, i.e. the source excitation(s) that
        produce the fields from which the objective function is computed.

        In general, sources will be an arbitrary caller-created list of Source
        objects, in which case source_region, source_component are ignored.

        As an alternative convenience convention, the caller may omit
        sources and instead specify source_region; in this case, a
        source distribution over the given region is automatically
        created based on the values of the module-wide configuration
        options fcen, df, source_component, source_mode.

    objective regions : list of Subregion
        subregions of the computational cell over which frequency-domain
        fields are tabulated and used to compute objective quantities

    design_region : meep_adjoint.Subregion
        design region bounding box (to be used in lieu of `basis`)

    basis : meep_adjoint.Basis
        (*either* `basis` **or** `design_region` should be non-None)
        Specification of function space for the design permittivity.

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

    extra_regions : list of Subregion
        Optional list of additional subregions over which to tabulate frequency-domain
        fields.

    objective_function : str
        definition of the quantity to be maximized. This should be
        a mathematical expression in which the names of one or more
        objective quantities appear, and which should evaluate to
        a real number when numerical values are substituted for the
        names of all objective quantities.

    extra_quantities : list of str
        Optional list of additional objective quantities to be computed and reported
        together with the objective function.
    """
    def __init__(self, cell_size=None, background_geometry=[], foreground_geometry=[],
                       sources=None, source_region=[],
                       objective_regions=[],
                       basis=None, design_region=None,
                       extra_regions=[],
                       objective_function=None,
                       extra_quantities=[]):
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
        obj_func        = ObjectiveFunction(fstr=objective_function,
                                            extra_quantities=extra_quantities)

        # initial values of (a) design variables, (b) the spatially-varying
        # permittivity function they define (the 'design function'), (c) the
        # GeometricObject describing a material body with this permittivity
        # (the 'design object'), and (d) mp.Simulation superposing the design
        # object with the rest of the caller's geometry.
        # Note that sources and DFT cells are not added to the Simulation at
        # this stage; this is done later by internal methods of TimeStepper
        # on a just-in-time basis before starting a timestepping run.
        self.beta_vector     = self.basis.project(adj_opt('eps_design'))
        self.design_function = self.basis.parameterized_function(self.beta_vector)
        design_object   = mp.Block(center=V3(design_region.center), size=V3(design_region.size),
                                   epsilon_func = self.design_function.func())
        geometry        = background_geometry + [design_object] + foreground_geometry
        sim             = mp.Simulation(resolution=adj_opt('res'), cell_size=V3(cell_size),
                                        boundary_layers=[mp.PML(adj_opt('dpml'))],
                                        geometry=geometry)

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

        if mp.am_master():
            init_log(filename=adj_opt('logfile') or adj_opt('filebase') + '.log', usecs=True)

        self.dashboard_state = None


    #####################################################################
    # The basic task of an OptimizationProblem: Given a candidate design
    # function, compute the objective function value and (optionally) gradient.
    ######################################################################
    def __call__(self, beta_vector=None, design=None,
                       need_value=True, need_gradient=True):
        """Evaluate value and/or gradient of objective function.

        Parameters
        ----------
        beta_vector: np.array
                new vector of design variables

        design: function-like
                alternative to beta_vector: function that will be projected
                onto the basis to obtain the new vector of design variables

        need_value: boolean
                if False, the forward run to compute the objective-function
                value will be omitted. This is only useful if the forward run
                has already been done (for the current design function) e.g.
                by a previous call with need_gradient = False.

        need_gradient: boolean
                if False, the adjoint run to compute the objective-function
                gradient will be omitted.


        Returns
        -------
        2-tuple (fq, gradf), where

            fq = np.array([f q1 q2 ... qN])
               = values of objective function & objective quantities

            gradf = np.array([df/dbeta_1 ... df/dbeta_D]), i.e. vector of partial
                    f derivatives w.r.t. each design variable (if need_gradient==True)

            If need_value or need_gradient is False, then fq or gradf in the return
            tuple will be None.
        """
        if beta_vector or design:
            self.update_design(beta_vector=beta_vector, design=design)

        #######################################################################
        # sanity check: if they are asking for an adjoint calculation with no
        #               forward calculation, make sure we previously completed
        #               a forward calculation for the current design function
        #######################################################################
        if need_value == False and self.stepper.state == 'reset':
            warnings.warn('forward run not yet run for this design; ignoring request to omit')
            need_value = True

        if self.dashboard_state is None:
            launch_dashboard(name=adj_opt('filebase'))
            self.dashboard_state = 'launched'

        with ConsoleManager() as cm:
            fq    = self.stepper.run('forward') if need_value else None
            gradf = self.stepper.run('adjoint') if need_gradient else None

        return fq, gradf


    def get_fdf_funcs(self):
        """construct callable functions for objective function value and gradient

        Returns
        -------
        2-tuple (f_func, df_func) of standalone (non-class-method) callables, where
            f_func(beta) = objective function value for design variables beta
           df_func(beta) = objective function gradient for design variables beta
        """

        def _f(x=None):
            (fq, _) = self.__call__(beta_vector = x, need_gradient = False)
            return fq[0]

        def _df(x=None):
            (_, df) = self.__call__(need_value = False)
            return df

        return _f, _df


    #####################################################################
    # ancillary API methods #############################################
    #####################################################################
    def update_design(self, beta_vector=None, design=None):
        """Update the design permittivity function.

           Precisely one of (beta_vector, design) should be specified.

           If beta_vector is specified, it simply replaces the old
           beta_vector wholesale.

           If design is specified, the function it describes is projected
           onto the basis set to yield the new beta_vector.

           In either case, before accepting the new coefficient vector
           we apply a componentwise clipping operation to ensure that
           all coefficients lie in the range [beta_min, beta_max]
           (where beta_{min,max} are configurable options). For
           finite-element bases this simple constraint form suffices to
           ensure physicality of the permittivity, but for other basis
           sets the physicality constraint will be more complicated to
           implement, and we should probably introduce a mechanism for
           building the constraints into the Basis class and subclasses.


        Parameters
        ----------
        beta_vector: np.array
            basis expansion coefficients for new permittivity function

        design: function-like
            new permittivity function
        """
        self.beta_vector = self.basis.project(design) if design else beta_vector
        self.beta_vector.clip(adj_opt('beta_min'), adj_opt('beta_max'))
        self.design_function.set_coefficients(self.beta_vector)
        self.stepper.state='reset'


    #####################################################################
    #####################################################################
    #####################################################################
    def visualize(self, id=None, options={}):
        """Produce a graphical visualization of the geometry and/or fields,
           as appropriately autodetermined based on the current state of
           progress.
        """
        if self.stepper.state=='reset':
            self.stepper.prepare('forward')

        bs = self.basis
        mesh = bs.fs.mesh() if (hasattr(bs,'fs') and hasattr(bs.fs,'mesh')) else None

        fig = plt.figure(num=id) if id else None

        if self.stepper.state.endswith('.prepared'):
            visualize_sim(self.stepper.sim, self.stepper.dft_cells, mesh=mesh, fig=fig, options=options)
        elif self.stepper.state == 'forward.complete':
            visualize_sim(self.stepper.sim, self.stepper.dft_cells, mesh=mesh, fig=fig, options=options)
        #else self.stepper.state == 'adjoint.complete':
        #            visualize_sim(self.stepper.sim, self.stepper.dft_cells, mesh=mesh, fig=fig, options=options)

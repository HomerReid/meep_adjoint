"""OptimizationProblem is the top-level class exported by the meep.adjoint module.
"""
import meep as mp

from . import (DFTCell, ObjectiveFunction, TimeStepper,
               FiniteElementBasis, parameterized_function2, E_CPTS, v3, V3)

######################################################################
######################################################################
######################################################################
class OptimizationProblem(object):
    """Top-level class in the MEEP adjoint module.

    Intended to be instantiated from user scripts with mandatory constructor
    input arguments specifying the data required to define an adjoint-based
    optimization.

    The class knows how to do one basic thing:

        (a) For a given vector of design variables, compute the objective
            function value (forward calculation) and optionally its gradient
            (adjoint calculation). This is done by the __call__ method.
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
              module-wide options such as 'element_type' and
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
              created based on the values of module-wide options (such
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

        from meep_adjoint import options

        #-----------------------------------------------------------------------
        # process convenience arguments:
        #  (a) if no basis was specified, create one using the given design
        #      region plus global option values
        #  (b) if no sources were specified, create one using the given source
        #      region plus global option values
        #-----------------------------------------------------------------------
        if basis is None:
            basis = FiniteElementBasis(region=design_region,
                                       element_length=options('element_length'),
                                       element_type=options('element_type'))
        design_region = basis.domain

        if not sources:
            f, df, m, c = [ options(s) for s in ['fcen', 'df', 'source_mode', 'source_component'] ]
            envelope    = mp.GaussianSource(f, fwidth=df)
            kws         = { 'center': V3(source_region.center), 'size': V3(source_region.size),
                            'src': envelope} #, 'eig_band': m, 'component': c }
            sources     = [ mp.EigenModeSource(eig_band=m,**kws) if m>0 else mp.Source(component=c, **kws) ]
        adjust_sources(sources)

        #-----------------------------------------------------------------------
        #initialize helper classes
        #-----------------------------------------------------------------------

        # DFTCells
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
        # object on the rest of the caller's geometry.
        # Note that sources are not added to the simulation at this stage;
        # that is done on a just-in-time basis by internal methods of TimeStepper.
        beta_vector     = basis.project(options('eps_func'))
#        eps_func        = basis.parameterized_function(beta_vector)
        eps_func, set_coefficients = parameterized_function2(basis,beta_vector)
        design_object   = mp.Block(center=V3(design_region.center), size=V3(design_region.size),
                                   epsilon_func=eps_func)
        geometry        = background_geometry + [design_object] + foreground_geometry
        sim             = mp.Simulation(resolution=options['res'],
                                        boundary_layers=[mp.PML(options['dpml'])],
                                        cell_size=V3(cell_size), geometry=geometry)

        # TimeStepper
        self.stepper    = TimeStepper(obj_func, dft_cells, basis, eps_func, set_coefficients,
                                      sim, fwd_sources=sources)

        # # set up console logging, file output, graphical visualization
        # self.filebase = args.filebase
        # self.stdout = sys.stdout
        # if args.logfile:
        #     options['log_streams'].append(open(args.logfile,'a'))
        # if args.log_to_console:
        #     options['log_streams'].append(self.stdout)
        # if args.verbose:
        #     options['verbosity'] = 'verbose'
        # elif args.concise:
        #     options['verbosity'] = 'concise'
        #
        # # options affecting visualization
        # # options['animate_components'] = args.animate_component
        #   options['animate_interval'] = args.animate_interval
        # if args.label_source_regions:
        #     set_plot_default('fontsize',def_plot_options['fontsize'], 'src')


    #####################################################################
    # Evaluate the objective function value and (optionally) gradient for
    # a given vector of design-variable values.
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

        fq    = self.stepper.run('forward', beta_vector=beta_vector)
        gradf = self.stepper.run('adjoint') if need_gradient else None
        return fq, gradf


######################################################################
######################################################################
######################################################################
def adjust_sources(sources):
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

######################################################################
# Processing of adjoint-related configuration options
######################################################################
from .util import OptionTemplate, OptionSettings

adjoint_option_templates= [

    #--------------------------------------------------
    #- options affecting MEEP calculations
    #--------------------------------------------------
    OptionTemplate('res',            20.0,   'Yee grid resolution'),
    OptionTemplate('fcen',            0.0,   'source center frequency'),
    OptionTemplate('df',              0.0,   'source frequency width'),
    OptionTemplate('source_component',  2,   'forward source component'),
    OptionTemplate('source_mode',       1,   'forward source eigenmode index'),
    OptionTemplate('nfreq',             1,   'number of DFT frequencies'),
    OptionTemplate('dpml',           -1.0,   'PML width (-1 --> auto-select)'),
    OptionTemplate('dair',           -1.0,   'gap width between material bodies and PMLs (-1 --> auto-select)'),
    OptionTemplate('eps_func',      '1.0',   'function of (x,y,z) giving initial design permittivity'),
    OptionTemplate('dft_reltol',   1.0e-6,   'convergence tolerance for terminating timestepping'),
    OptionTemplate('dft_timeout',    10.0,   'max runtime in units of last_source_time'),
    OptionTemplate('dft_interval',   0.25,   'meep time between DFT convergence checks in units of last_source_time'),
    OptionTemplate('complex_fields',False,   'use complex fields in forward calculation'),
    OptionTemplate('verbose',       False,   'produce more verbose output'),
    OptionTemplate('visualize',     False,   'produce graphical output'),

    #--------------------------------------------------
    #- options affecting finite-element basis sets
    #--------------------------------------------------
    OptionTemplate('element_type',   'CG 1',  'finite-element family and degree'),
    OptionTemplate('element_length',  0.0,    'finite-element discretization length'),

    #--------------------------------------------------
    #- options affecting gradient-desscent optimizer
    #--------------------------------------------------
    OptionTemplate('alpha',          1.0,     'initial value of gradient relaxation parameter'),
    OptionTemplate('alpha_min',      1.0e-3,  'minimum value of alpha'),
    OptionTemplate('alpha_max',      10.0,    'maximum value of alpha'),
    OptionTemplate('boldness',       1.25,    'sometimes you just gotta live a little (explain me)'),
    OptionTemplate('timidity',       0.75,    'can\'t be too cautious in this dangerous world (explain me)'),
    OptionTemplate('max_iters',      100,     'max number of optimization iterations'),

    #--------------------------------------------------
    # options affecting outputs
    #--------------------------------------------------
    OptionTemplate('verbose',      'True',    'produce more output'),
    OptionTemplate('visualize',    'True',    'produce visualization graphics'),
    OptionTemplate('silence_meep', 'True',    'suppress MEEP console output')
]


def process_adjoint_options(custom_defaults={}):
    return OptionSettings(adjoint_option_templates,
                          custom_defaults=custom_defaults,
                          filename='meep_adjoint.rc')


# reinstate me!
# OptionTemplate('animate_component', action='append', help='plot time-domain field component')
# OptionTemplate('animate_interval', type=float, default=1.0, help='meep time between animation frames')]

"""
Adjoint-based sensitivity-analysis module for pymeep.
Author: Homer Reid <homer@homerreid.com>
Documentation: https://meep.readthedocs.io/en/latest/Python_Tutorials/AdjointSolver.md
"""
import sys

import meep as mp

######################################################################
######################################################################
######################################################################
from .optimization_problem import OptimizationProblem, process_adjoint_options

from .timestepper import TimeStepper

from .objective import ObjectiveFunction

from .dft_cell import (ORIGIN, XHAT, YHAT, ZHAT, E_CPTS, H_CPTS, EH_CPTS,
                       v3, V3, Subregion, DFTCell, Grid, make_grid)

from .basis import Basis

from .finite_element_basis import (FiniteElementBasis, parameterized_function2)

from .visualization import process_visualization_options

from .util import (OptionSettings, OptionTemplate, log)

######################################################################
# options is a module-wide database of configuration options settings.
# it is initialized on module import, and subsequently re-initialized
# with different default values if somebody calls set_default_options().
######################################################################
def init_options(custom_defaults={}):
    adj_opts = process_adjoint_options(custom_defaults)
    vis_opts = process_visualization_options(custom_defaults)
    return adj_opts.merge(vis_opts)


options = init_options()
"""module-global database of configuration option settings"""


def set_default_options(custom_defaults):
    from meep_adjoint import options
    sys.argv = list(options.argv)
    options = init_options(custom_defaults)

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
from .util import (OptionTemplate, OptionAlmanac)

from .adjoint_options import get_adjoint_option, set_adjoint_option_defaults

from .dft_cell import (ORIGIN, XHAT, YHAT, ZHAT, E_CPTS, H_CPTS, EH_CPTS,
                       v3, V3, Subregion, DFTCell, Grid, make_grid)

from .objective import ObjectiveFunction

from .basis import Basis

from .finite_element_basis import (FiniteElementBasis, parameterized_function2)

from .timestepper import TimeStepper

from .optimization_problem import OptimizationProblem

#from .visualization import visualize_sim

######################################################################
######################################################################
######################################################################
def set_option_defaults(custom_defaults={}, search_env=True):
    set_adjoint_option_defaults(custom_defaults, search_env)
    #set_visualization_option_defaults(custom_defaults, search_env)

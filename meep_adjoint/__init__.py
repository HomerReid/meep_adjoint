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
                       v3, V3, Subregion, DFTCell, Grid, make_grid

from .basis import Basis

from .finite_element_basis import (FiniteElementBasis, parameterized_function2)

from .visualization import process_visualization_options

from .util import (OptionSettings, OptionTemplate, log)

######################################################################
#
######################################################################
options = None
custom_defaults = {}

def set_default_options(new_defaults):
    custom_defaults = dict(new_defaults)

def init_options(custom_defaults={}):
    """ global options processor for meep_adjoint """
    adj_opts = process_adjoint_options(custom_defaults)
    vis_opts = process_visualization_options(custom_defaults)
    return adj_opts.merge(vis_opts)


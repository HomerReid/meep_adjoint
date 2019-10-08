import sys
import os
import argparse

import numpy as np
import meep as mp

import meep_adjoint

from meep_adjoint import get_adjoint_option as adj_opt
from meep_adjoint import get_visualization_option as vis_opt

from meep_adjoint import ( OptimizationProblem, Subregion,
                           ORIGIN, XHAT, YHAT, ZHAT, E_CPTS, H_CPTS, v3, V3)

######################################################################
# override default settings for some meep_adjoint configuration options
######################################################################
meep_adjoint.set_option_defaults( { 'fcen': 0.5, 'df': 0.2,
                                    'dpml': 1.0, 'dair': 0.5,
                                    'eps_func': 6.0,
                                    'flux_region_fontsize': 15,
                                    'latex': True,
                                   })

######################################################################
# subroutine that initializes and returns an OptimizationProblem
# structure for the router geometry
######################################################################
def init_problem():
    """ Initialize four-way router optimization problem.

    Args:
        None (reads command-line options from sys.argv).

    Returns:
        New instance of meep_adjoint.OptimizationProblem()
    """

    ######################################################################
    # process script-specific command-line arguments...
    ######################################################################
    parser = argparse.ArgumentParser()

    # options affecting the geometry of the router
    parser.add_argument('--wh',       type=float, default=1.5,  help='width of horizontal waveguide')
    parser.add_argument('--wv',       type=float, default=1.5,  help='width of vertical waveguide')
    parser.add_argument('--h',        type=float, default=0.0,  help='height of waveguide in z-direction')
    parser.add_argument('--l_stub',   type=float, default=3.0,  help='waveguide input/output stub length')
    parser.add_argument('--l_design', type=float, default=4.0,  help='design region side length')
    parser.add_argument('--eps_wvg',  type=float, default=6.0,  help='waveguide permittivity')

    # basis-set options
    parser.add_argument('--element_length',  type=float,  default=0.25,       help='finite-element length scale')
    parser.add_argument('--element_type',    type=str,    default='Lagrange', help='finite-element type')
    parser.add_argument('--element_order',   type=int,    default=1,          help='finite-element order')

    # configurable weighting prefactors for the north, south, and east power fluxes
    # to allow the objective function to be redefined via command-line options
    parser.add_argument('--n_weight', type=float, default=1.00, help='')
    parser.add_argument('--s_weight', type=float, default=0.00, help='')
    parser.add_argument('--e_weight', type=float, default=0.00, help='')

    args = parser.parse_args()

    ######################################################################
    # ... and fetch values of some meep_adjoint options we will use
    ######################################################################
    fcen = adj_opt('fcen')
    dpml = adj_opt('dpml')
    dair = adj_opt('dair')


    ##################################################
    # set up optimization problem
    ##################################################

    #----------------------------------------
    # computational cell
    #----------------------------------------
    lcen          = 1.0/fcen
    dpml          = 0.5*lcen if dpml==-1.0 else dpml
    design_length = args.l_design
    sx = sy       = dpml + args.l_stub + design_length + args.l_stub + dpml
    sz            = 0.0 if args.h==0.0 else dpml + dair + args.h + dair + dpml
    cell_size     = [sx, sy, sz]

    #----------------------------------------------------------------------
    #- geometric objects (material bodies), not including the design object
    #----------------------------------------------------------------------
    wvg_mat = mp.Medium(epsilon=args.eps_wvg)
    ew_wvg  = mp.Block(center=V3(ORIGIN), material=wvg_mat, size=V3(sx, args.wh, sz) )
    ns_wvg  = mp.Block(center=V3(ORIGIN), material=wvg_mat, size=V3(args.wv, sy, sz) )

    #----------------------------------------------------------------------
    #- objective regions
    #----------------------------------------------------------------------
    d_flux     = 0.5*(design_length + args.l_stub)  # distance from origin to NSEW flux monitors
    gap        = args.l_stub/6.0                    # gap between source region and flux monitor
    d_source   = d_flux + gap                       # distance from origin to source
    d_flx2     = d_flux + 2.0*gap

    n_center   = ORIGIN + d_flux*YHAT
    s_center   = ORIGIN - d_flux*YHAT
    e_center   = ORIGIN + d_flux*XHAT
    w1_center  = ORIGIN - d_flux*XHAT
    w2_center  = w1_center - 2.0*gap*XHAT

    ns_size    = [2.0*args.wh, 0.0, sz]
    ew_size    = [0.0, 2.0*args.wv, sz]

    north      = Subregion(center=n_center, size=ns_size, dir=mp.Y,  name='north')
    south      = Subregion(center=s_center, size=ns_size, dir=mp.Y,  name='south')
    east       = Subregion(center=e_center, size=ew_size, dir=mp.X,  name='east')
    west1      = Subregion(center=w1_center, size=ew_size, dir=mp.X, name='west1')
    west2      = Subregion(center=w2_center, size=ew_size, dir=mp.X, name='west2')

    #----------------------------------------------------------------------
    # objective function and extra objective quantities -------------------
    #----------------------------------------------------------------------
    n_term = '{}*Abs(P1_north)**2'.format(args.n_weight) if args.n_weight else ''
    s_term = '{}*Abs(S1_south)**2'.format(args.s_weight) if args.s_weight else ''
    e_term = '{}*Abs(P1_east)**2'.format(args.e_weight) if args.e_weight else ''

    objective = n_term + s_term + e_term
    extra_quantities = ['S_north', 'S_south', 'S_east', 'S_west1', 'S_west2']

    #----------------------------------------------------------------------
    # source region
    #----------------------------------------------------------------------
    source_center  = ORIGIN - d_source*XHAT
    source_size    = ew_size
    source_region  = Subregion(center=source_center, size=source_size, name=mp.X)

    #----------------------------------------------------------------------
    #- design region, expansion basis
    #----------------------------------------------------------------------
    design_center = ORIGIN
    design_size   = [design_length, design_length, sz]
    design_region = Subregion(name='design', center=design_center, size=design_size)

    #----------------------------------------------------------------------
    #- optional extra regions for visualization
    #----------------------------------------------------------------------
    full_region = Subregion(name='full', center=ORIGIN, size=cell_size)

    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    return OptimizationProblem(
     cell_size=cell_size,
     background_geometry=[ew_wvg, ns_wvg],
     source_region=source_region,
     objective=objective,
     objective_regions=[north, south, east, west1, west2],
     extra_quantities=extra_quantities,
     design_region=design_region,
     extra_regions=[full_region]
    )


######################################################################
######################################################################
######################################################################
if __name__ == '__main__':

    opt_prob = init_problem()

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
    # set custom defaults for meep_adjoint package-wide options, then
    # fetch values for a few such options we will need in this routine
    ######################################################################
    meep_adjoint.set_option_defaults( { 'fcen': 0.5, 'df': 0.2,
                                        'dpml': 1.0, 'dair': 0.5,
                                        'eps_design': 6.0
                                      })
    fcen = adj_opt('fcen')
    dpml = adj_opt('dpml')
    dair = adj_opt('dair')

    ######################################################################
    # process script-specific command-line arguments...
    ######################################################################
    parser = argparse.ArgumentParser()

    # options affecting the geometry of the router
    parser.add_argument('--w_east',   type=float, default=1.5,  help='width of EAST waveguide stub')
    parser.add_argument('--w_west',   type=float, default=1.5,  help='width of WEST waveguide stub')
    parser.add_argument('--w_north',  type=float, default=1.5,  help='width of NORTH waveguide stub')
    parser.add_argument('--w_south',  type=float, default=1.5,  help='width of SOUTH waveguide stub')
    parser.add_argument('--l_stub',   type=float, default=3.0,  help='waveguide stub length')
    parser.add_argument('--l_design', type=float, default=4.0,  help='design region side length')
    parser.add_argument('--h',        type=float, default=0.0,  help='thickness in z-direction')
    parser.add_argument('--eps_wvg',  type=float, default=6.0,  help='waveguide permittivity')

    parser.add_argument('--full_dft', action='store_true', help='tabulate and plot fields over full computational cell')

    # options affecting the type of device to design
    parser.add_argument('--splitter', action='store_true', help='design equal splitter instead of right-angle router')

    args = parser.parse_args()

    w_east   = args.w_east
    w_west   = args.w_west
    w_north  = args.w_north
    w_south  = args.w_south
    l_stub   = args.l_stub
    l_design = args.l_design
    h        = args.h
    eps_wvg  = args.eps_wvg
    splitter = args.splitter

    ##################################################
    # set up optimization problem
    ##################################################

    #----------------------------------------
    # computational cell
    #----------------------------------------
    lcen          = 1.0/fcen
    dpml          = 0.5*lcen if dpml==-1.0 else dpml
    sx = sy       = dpml + l_stub + l_design + l_stub + dpml
    sz            = 0.0 if h==0.0 else (dpml + dair + h + dair + dpml)
    d_flux        = 0.5*(l_design + l_stub)     # distance from origin to NSEW flux monitors
    d_flx2        = d_flux + l_stub/3.0         # distance from origin to west2 flux monitor
    d_source      = d_flux + l_stub/6.0         # distance from origin to source
    cell_size     = [sx, sy, sz]

    #----------------------------------------------------------------------
    #- geometric objects (material bodies), not including the design object
    #----------------------------------------------------------------------
    wvg_mat    = mp.Medium(epsilon=eps_wvg)
    east_wvg   = mp.Block(center=V3(ORIGIN+0.25*sx*XHAT), material=wvg_mat, size=V3(0.5*sx, w_east,  h) )
    west_wvg   = mp.Block(center=V3(ORIGIN-0.25*sx*XHAT), material=wvg_mat, size=V3(0.5*sx, w_west,  h) )
    north_wvg  = mp.Block(center=V3(ORIGIN+0.25*sy*YHAT), material=wvg_mat, size=V3(w_north, 0.5*sy, h) )
    south_wvg  = mp.Block(center=V3(ORIGIN-0.25*sy*YHAT), material=wvg_mat, size=V3(w_south, 0.5*sy, h) )

    background_geometry = [ east_wvg, west_wvg, north_wvg, south_wvg ]

    #----------------------------------------------------------------------
    # source region
    #----------------------------------------------------------------------
    source_center  = ORIGIN - d_source*XHAT
    source_size    = 2.0*w_west*YHAT
    source_region  = Subregion(center=source_center, size=source_size, name=mp.X)

    #----------------------------------------------------------------------
    #- design region
    #----------------------------------------------------------------------
    design_center = ORIGIN
    design_size   = [l_design, l_design, h]
    design_region = Subregion(name='design', center=design_center, size=design_size)

    #----------------------------------------------------------------------
    #- objective regions
    #----------------------------------------------------------------------
    n_center   = ORIGIN + d_flux*YHAT
    s_center   = ORIGIN - d_flux*YHAT
    e_center   = ORIGIN + d_flux*XHAT
    w1_center  = ORIGIN - d_flux*XHAT
    w2_center  = w1_center - (l_stub/3.0)*XHAT

    north      = Subregion(center=n_center,  size=2.0*w_north*XHAT, dir=mp.Y,  name='north')
    south      = Subregion(center=s_center,  size=2.0*w_south*XHAT, dir=mp.Y,  name='south')
    east       = Subregion(center=e_center,  size=2.0*w_east*YHAT,  dir=mp.X,  name='east')
    west1      = Subregion(center=w1_center, size=2.0*w_west*YHAT,  dir=mp.X,  name='west1')
    west2      = Subregion(center=w2_center, size=2.0*w_west*YHAT,  dir=mp.X,  name='west2')

    objective_regions = [north, south, east, west1, west2]

    #----------------------------------------------------------------------
    # objective function and extra objective quantities -------------------
    #----------------------------------------------------------------------
    fobj_router   = '|P1_north|^2'
    fobj_splitter = '( |P1_north| - |P1_east| )^2 + ( |P1_east| - |M1_south| )^2'
    objective_function = fobj_splitter if splitter else fobj_router
    extra_quantities = ['S_north', 'S_south', 'S_east', 'S_west1', 'S_west2']

    #----------------------------------------------------------------------
    #- optional extra regions for visualization
    #----------------------------------------------------------------------
    full_region = Subregion(name='full', center=ORIGIN, size=cell_size)
    extra_regions = [full_region] if args.full_dft else []

    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    return OptimizationProblem(
     cell_size=cell_size,
     background_geometry=background_geometry,
     source_region=source_region,
     objective_regions=objective_regions,
     design_region=design_region,
     extra_regions=extra_regions,
     objective_function=objective_function,
     extra_quantities=extra_quantities
    )


######################################################################
######################################################################
######################################################################
if __name__ == '__main__':

    opt_prob = init_problem()

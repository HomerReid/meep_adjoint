import sys
import os
import argparse
import numpy as np
import meep as mp

from meep_adjoint import ( OptimizationProblem, Subregion,
                           ORIGIN, XHAT, YHAT, ZHAT, E_CPTS, H_CPTS, v3, V3)

from meep_adjoint import set_default_options as set_adjoint_defaults
from meep_adjoint import options as adj_opts


######################################################################
# set some problem-specific default values for adjoint-module options
######################################################################
custom_defaults = { 'fcen': 0.5, 'df': 0.2, 'eps_func' : 3.0,
                    'dpml': 0.5, 'dair': 0.5 }
set_adjoint_defaults(custom_defaults)


##################################################
# parse problem-specific command-line arguments
##################################################
parser = argparse.ArgumentParser()
parser.add_argument('--eps_wvg',        type=float, default=6.0,          help ='waveguide permittivity')
parser.add_argument('--eps_hole',       type=float, default=6.0,          help ='hole permittivity')
parser.add_argument('--w_wvg',          type=float, default=3.0,          help ='waveguide width')
parser.add_argument('--h_wvg',          type=float, default=0.0,          help ='waveguide thickness in Z direction (0==2D geometry)')
parser.add_argument('--r_hole',         type=float, default=0.5,          help ='hole radius')
args=parser.parse_args()


##################################################
# set up problem geometry
##################################################

#----------------------------------------
# size of computational cell
#----------------------------------------
w_wvg      = args.w_wvg
h_wvg      = args.h_wvg
r_hole     = args.r_hole
eps_wvg    = args.eps_wvg
eps_hole   = args.eps_hole
dpml       = adj_opts('dpml')
dair       = adj_opts('dair')
fcen       = adj_opts('fcen')
L          = max(6.0*dpml + 2.0*r_hole,  3.0/fcen)
sx         = dpml + L + dpml
sy         = dpml + dair + w_wvg + dair + dpml
sz         = 0.0 if h_wvg==0.0 else dpml + dair + h_wvg + dair + dpml
cell_size  = v3(sx, sy, sz)

#----------------------------------------------------------------------
#- objective regions and objective_function
#----------------------------------------------------------------------
w_flux = (0.5*dair + w_wvg + 0.5*dair)
h_flux = 0.0 if h_wvg==0.0 else (0.5*dair + h_wvg + 0.5*dair)
flux_size = v3(0, w_flux, h_flux)
x0   = r_hole+dpml     # distance from origin to center of flux cell
east = Subregion(name='east', center=v3(+x0,0,0), size=flux_size, dir=mp.X)
west = Subregion(name='west', center=v3(-x0,0,0), size=flux_size, dir=mp.X)

objective = "Abs(P1_east)**2"
extra_quantities=["S_east", "S_west", "P1_east", "M1_east", "P2_east", "M2_east"]

#----------------------------------------------------------------------
# source region
#----------------------------------------------------------------------
source_center = west.center - dpml*XHAT
source_size   = flux_size
source_region = Subregion(center=source_center, size=source_size)

#----------------------------------------------------------------------
# design region and expansion basis
#----------------------------------------------------------------------
design_center = ORIGIN
design_size   = 2.0*r_hole*(XHAT + YHAT) + args.h_wvg*ZHAT
design_region = Subregion(center=design_center, size=design_size, name='design')

full_region = Subregion(size=cell_size)

wvg = mp.Block(center=V3(ORIGIN), material=mp.Medium(epsilon=eps_wvg), size=V3(sx,w_wvg,h_wvg))

opt_prob = OptimizationProblem(objective_regions=[east,west], objective="S_east",
                               design_region=design_region,
                               cell_size=cell_size, background_geometry=[wvg],
                               source_region=source_region,
                               extra_quantities=extra_quantities, extra_regions=[full_region]
                              )

# #         #----------------------------------------
# #         # finite-element mesh and basis
# #         #----------------------------------------
# #         mesh = annular_cylinder_mesh(outer_radius=args.r_hole, height=args.h_wvg,
# #                                      element_length=args.element_length)
# #         el_type, el_order = None, None
# #         if args.basis_type:
# #             el_type, el_order = args.basis_type.split()[0:2]
# #         basis = FiniteElementBasis(mesh=mesh, element_type=el_type, element_order=int(el_order))
# #
# #         #----------------------------------------
# #         #- source location
# #         #----------------------------------------
# #
# #----------------------------------------------------------------------
# #- objective function and few extra objective quantities
# #----------------------------------------------------------------------
# objective = 'Abs(P1_east)**2'
# extra_quantities = [ 'P1_west', 'P2_east', 'P2_west',
#                      'M1_east', 'M1_west', 'M2_east', 'M2_west',
#                       'S_east',  'S_west', 'UE_design', 'UH_design' ]
#
# problem = adjoint.OptimizationProblem( objective=objective,
#                                        extra_quantities=extra_quantities,
#                                        objective_regions=objective_regions,
#                                        extra_regions=extra_regions,
#                                        basis=basis
#                                      )
#
# #
# #         #----------------------------------------
# #         #- internal storage for variables needed later
# #         #----------------------------------------
# #         self.args            = args
# #         self.dpml            = dpml
# #         self.cell_size       = cell_size
# #         self.basis           = basis
# #         self.design_center   = design_center
# #         self.source_center   = source_center
# #         self.source_size     = source_size
# #
# #         return ProblemData(objective_function, objective_regions,
# #                            design_region, basis,
# #                            extra_regions, extra_quantities)
# #
# #     ##############################################################
# #     ##############################################################
# #     ##############################################################
# #     def create_sim(self, eps_func, vacuum=False):
# #
# #         args = self.args
# #         disc = mp.Cylinder(center=self.design_center, radius=args.r_hole,
# #                            height=self.args.h_wvg, epsilon_func=eps_func)
# #
# #         geometry = [wvg] if vacuum else [wvg, disc]
# #
# #         envelope, amp = mp.GaussianSource(args.fcen,fwidth=args.df), 1.0
# #         if callable(getattr(envelope, "fourier_transform", None)):
# #             amp /= envelope.fourier_transform(args.fcen)
# #         sources=[mp.EigenModeSource(src=envelope, amplitude=amp,
# #                                     center=self.source_center,
# #                                     size=self.source_size,
# #                                     eig_band=self.args.source_mode,
# #                                    )
# #                 ]
# #
# #         sim=mp.Simulation(resolution=args.res,
# #                           cell_size=self.cell_size,
# #                           boundary_layers=[mp.PML(args.dpml)],
# #                           geometry=geometry,
# #                           sources=sources)
# #
# #         if args.complex_fields:
# #             sim.force_complex_fields=True
# #
# #         return sim

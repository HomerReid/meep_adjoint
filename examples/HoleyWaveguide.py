import sys
import os
import argparse
import numpy as np
import meep as mp

import meep_adjoint

from meep_adjoint import ( OptimizationProblem, Subregion,
                           ORIGIN, XHAT, YHAT, ZHAT, E_CPTS, H_CPTS, v3, V3)

from meep_adjoint import set_option_defaults as set_mpadj_defaults
from meep_adjoint import get_adjoint_option as adj_opt


######################################################################
# for some adjoint-related configuration options, the default values
# set by meep_adjoint are not quite right for our particular problem,
# so we override those with problem-specific custom defaults.
# note that these are still just *defaults*, overwritten by values
# in config files, environment variables, or command-line arguments.
######################################################################
custom_defaults = { 'fcen': 0.5, 'df': 0.2, 'eps_func' : 3.0,
                    'dpml': 0.5, 'dair': 0.5 }
set_mpadj_defaults(custom_defaults)


# query meep_adjoint for some option values we will need below
dpml     = adj_opt('dpml')
dair     = adj_opt('dair')
fcen     = adj_opt('fcen')
filebase = adj_opt('filebase')


##################################################
# parse problem-specific command-line arguments
##################################################
parser = argparse.ArgumentParser()
parser.add_argument('--w_wvg',    type=float, default=3.0,    help ='waveguide width')
parser.add_argument('--h_wvg',    type=float, default=0.0,    help ='waveguide Z-thickness (=0 for 2D geometry)')
parser.add_argument('--w_hole',   type=float, default=0.5,    help ='hole width')

parser.add_argument('--eps_wvg',  type=float, default=6.0,    help ='waveguide permittivity')

parser.add_argument('--eps_hole', type=str,   default=None,   help ='hole permittivity value or range (start,stop,num)')
parser.add_argument('--fd_step',  type=float, default=0.01,   help ='relative finite-difference step')
parser.add_argument('--fd_order', type=int,   default=2,      help ='order of finite-difference stencil')

parser.add_argument('--img_file', type=str,   default=None,   help ='filename for saved copy of geometry visualization')

args = parser.parse_args()


######################################################################
# set up optimization problem
######################################################################

#----------------------------------------------------------------------
# size of computational cell
#----------------------------------------------------------------------
w_wvg      = args.w_wvg
h_wvg      = args.h_wvg
w_hole     = args.w_hole
L          = max(6.0*dpml + 2.0*w_hole,  3.0/fcen)
sx         = dpml + L + dpml
sy         = dpml + dair + w_wvg + dair + dpml
sz         = 0.0 if h_wvg==0.0 else dpml + dair + h_wvg + dair + dpml
cell_size  = v3(sx, sy, sz)

#----------------------------------------------------------------------
# geometric objects (material bodies), not including the design object
#----------------------------------------------------------------------
wvg = mp.Block(center=V3(ORIGIN), material=mp.Medium(epsilon=args.eps_wvg), size=V3(sx,w_wvg,h_wvg))

#----------------------------------------------------------------------
#- objective regions, objective quantities, objective function
#----------------------------------------------------------------------
w_flux = (0.5*dair + w_wvg + 0.5*dair)
h_flux = 0.0 if h_wvg==0.0 else (0.5*dair + h_wvg + 0.5*dair)
flux_size = v3(0, w_flux, h_flux)
d_flux = w_hole + dpml     # distance from origin to centers of flux cells
east  = Subregion(name='east', center=v3(+d_flux,0,0), size=flux_size, dir=mp.X)
west  = Subregion(name='west', center=v3(-d_flux,0,0), size=flux_size, dir=mp.X)

objective = 'Abs(P1_east)**2'
extra_quantities=['S_east', 'S_west', 'P1_east', 'M1_east', 'P2_east', 'M2_east']

#----------------------------------------------------------------------
# source region
#----------------------------------------------------------------------
d_source = np.mean([d_flux, 0.5*sx-dpml])  # midway between flux cell and PML edge
source_center = v3(-1.0*d_source, 0, 0)
source_size   = flux_size
source_region = Subregion(center=source_center, size=source_size, dir=mp.X)

#----------------------------------------------------------------------
# design region and expansion basis
#----------------------------------------------------------------------
design_center = ORIGIN
design_size   = 2.0*w_hole*(XHAT + YHAT) + args.h_wvg*ZHAT
design_region = Subregion(name='design', center=design_center, size=design_size)


#----------------------------------------------------------------------
# 'extra' regions not needed for adjoint calculations but added for
# our own purposes---in this case, to produce field visualizations
#----------------------------------------------------------------------
full_region = Subregion(name='full', center=ORIGIN, size=cell_size)


opt_prob = OptimizationProblem(objective_regions=[east,west],
                               objective=objective,
                               design_region=design_region,
                               cell_size=cell_size, background_geometry=[wvg],
                               source_region=source_region,
                               extra_quantities=extra_quantities, extra_regions=[full_region])


######################################################################
# do computations at all eps_hole values in user-specified range
######################################################################

# try to interpret eps_hole argument as a single value or a range
eps_hole_range = []
if args.eps_hole is not None:
    try:
        tokens = args.eps_hole.replace(',',' ').split() + ['', '1']
        eps_hole_range = np.linspace( float(tokens[0]), float(tokens[1] or tokens[0]), int(tokens[2]) )
    except:
        mp.abort('invalid --eps_hole specification {}'.format(args.eps_hole))


# write output-file preamble if necessary
outfile = (filebase + '.out') if filebase and eps_hole_range else None
if outfile and not os.path.isfile(outfile):
    with open(outfile,'w') as f:
        f.write('#1 eps_hole \n')
        f.write('#2 f_objective \n')
        f.write('#3 df/deps (adjoint)\n')
        f.write('#4 df/deps (1st-order FD)\n')
        f.write('#5 df/deps (2nd-order FD)\n')


# main loop
for eps in eps_hole_range:

    # compute objective function value and adjoint-method gradient
    fq0,  gradf = opt_prob(design=eps, need_gradient=True)
    df_adjoint  = np.average(gradf)

    # compute finite-difference derivatives
    df_fd = [0.0, 0.0]
    if args.fd_step > 0.0:
        delta_eps = args.fd_step * eps
        fqp, _    = opt_prob(design=(eps + delta_eps), need_gradient=False)
        df_fd[0]  = ( fqp[0] - fq0[0] ) / delta_eps
        if args.fd_order == 2:
            fqm, _   = opt_prob(design=(eps - delta_eps), need_gradient=False)
            df_fd[1] = ( fqp[0] - fqm[0] ) / (2.0*delta_eps)

    # write output to console and data file
    if outfile:
        with open(outfile,'a') as f:
            f.write('{} {} {} {} {}\n',eps,fq[0],df_adjoint,df_fd[0],df_fd[1])

    sys.stdout.write('\n\n For eps  = {}:\n'.format(eps))
    sys.stdout.write('       f  = {} \n'.format(fq0[0]))
    sys.stdout.write(' df (adj) = {} \n'.format(df_adjoint))
    sys.stdout.write(' df (fd1) = {} \n'.format(df_fd[0]))
    sys.stdout.write(' df (fd2) = {} \n'.format(df_fd[1]))

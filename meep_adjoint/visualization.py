"""
routines for standardized visualization of pymeep geometries and fields
"""

import sys
from os import environ as env
import re
import warnings
from collections import namedtuple

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import ticker
from mpl_toolkits.mplot3d import axes3d
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.collections import PolyCollection, LineCollection
import matplotlib.cm

import meep as mp

from . import get_visualization_option as vis_opt
from . import get_visualization_options as vis_opts

from . import fix_array_metadata, v3

######################################################################
######################################################################
######################################################################
def visualize_sim(sim, dft_cells, mesh=None, fig=None, plot3D=None,
                  src_labels=[], options={}):

    # if plot3D not specified, set it automatically: false
    # if we are plotting only the geometry (at the beginning
    # of a timestepping run), true if we are also plotting
    # fields (at the end of a simulation).
    if plot3D is None:
        plot3D = sim.round_time() > sim.fields.last_source_time()

    plot_geometry(sim, dft_cells, fig=fig, plot3D=plot3D,
                  src_labels=src_labels, options=options)

    ####################################################
    ####################################################
    ####################################################
    if plot3D and sim.round_time() > sim.fields.last_source_time():
        plot_dft_fields(sim, dft_cells, superpose=True, options=options)
        plot_dft_flux(sim, dft_cells, superpose=True, options=options)

    if not plot3D:
        plt.gcf().tight_layout()

    if vis_opt('show', overrides=options):
        if mesh is not None and not plot3D:
            plot_mesh(mesh, options)
        plt.show(block = False)
        plt.draw()


######################################################################
######################################################################
######################################################################
def plot_geometry(sim, dft_cells, fig=None, plot3D=False,
                  src_labels=[], options={}):
    """
    """
    if not mp.am_master():
        return

    fig = fig or plt.gcf()
    fig.clf()

    #################################################
    # plot permittivity
    #################################################
    plot_eps(sim, fig=fig, plot3D=plot3D, options=options)

    ##################################################
    # plot PML regions
    ##################################################
    if sim.boundary_layers and hasattr(sim.boundary_layers[0],'thickness'):
        dpml    = sim.boundary_layers[0].thickness
        sx, sy  = sim.cell_size.x, sim.cell_size.y
        y0, x0  = mp.Vector3(0.0, 0.5*(sy-dpml)), mp.Vector3(0.5*(sx-dpml), 0.0)
        ns, ew  = mp.Vector3(sx-2*dpml, dpml),    mp.Vector3(dpml,sy)
        centers = [ y0, -1*y0, x0, -1*x0 ]   # north, south, east, west
        sizes   = [ ns,    ns, ew,    ew ]
        for c,s in zip(centers,sizes):
            plot_subregion(sim, center=c, size=s, plot3D=plot3D,
                                section='pml', options=options)


    #####################################################################
    ## plot source regions and optionally source amplitudes
    #####################################################################
    def srclabel(s,n):
        return ('eig ' if hasattr(s,'eig_band') else '') + 'src {}'.format(n)
    for n,s in enumerate(sim.sources):
        plot_subregion(sim, center=s.center, size=s.size, plot3D=plot3D,
                       label=srclabel(s,n) if not src_labels else src_labels[ns],
                       section='src_region', options=options)

    #if src_options['zrel_min']!=src_options['zrel_max']:
    #    visualize_source_distribution(sim, superpose=plot3D, options=src_options)

    #####################################################################
    # plot DFT cell regions, with labels for flux cells.
    #####################################################################
    for n, c in enumerate(dft_cells):
        section = c.celltype + '_region'
        label = None if plot3D else c.name.strip('_flux')
        plot_subregion(sim, vol=c.region, plot3D=plot3D, label=label, section=section, options=options)



#####################################################################
# visualize epsilon distribution.
#####################################################################
def plot_eps(sim, fig=None, plot3D=False, options={}):
    """Produce graphical visualization of material geometry.
       Args:
             fig: existing matplotlib figure to overwrite
                  (otherwise a new fig() is created)
          plot3D: True to plot in 3D axis system (typically used
                  for geometry--field superposition plots)
         options: dict of visualization option overrides

       Return value: None
    """

    #--------------------------------------------------
    #- fetch values of relevant options ---------------
    #--------------------------------------------------
    keys = ['cmap', 'alpha', 'shading', 'interp',
            'method', 'contours', 'cb_shrink', 'cb_pad',
            'cmin', 'cmax', 'zmin', 'zmax',
            'fontsize', 'latex', 'linewidth', 'linecolor']
    vals = vis_opts(keys, section='eps', overrides=options)
    cmap, alpha, shading, interp          = vals[0:4]
    method, contours, cb_shrink, cb_pad   = vals[4:8]
    cmin, cmax, zbar_min, zbar_max        = vals[8:12]
    fontsize, latex, linewidth, linecolor = vals[12:16]


    #--------------------------------------------------
    #- fetch epsilon array and clip values if requested
    #--------------------------------------------------
    (x,y,z,w) = sim.get_array_metadata()
    eps = np.transpose(sim.get_epsilon())
    vmin = cmin if np.isfinite(cmin) else np.min(eps)
    vmax = cmax if np.isfinite(cmax) else np.max(eps)
    if np.isfinite(cmin) or np.isfinite(cmax):
       eps = np.clip(eps,vmin,vmax)

    #--------------------------------------------------
    #- create 2D or 3D plot ---------------------------
    #--------------------------------------------------
    ax = fig.gca(projection='3d') if plot3D else fig.gca()
    if not plot3D:
       ax.set_aspect('equal')
       plt.tight_layout()
       cb = None
    if plot3D:
       X, Y = np.meshgrid(x, y)
       zmin, zmax = 0.0, max(sim.cell_size.x, sim.cell_size.y)
       z0   = 0.0
       img  = ax.contourf(X, Y, eps, contours, zdir='z', offset=z0,
                          vmin=vmin, vmax=vmax, cmap=cmap, alpha=alpha)
       ax.set_zlim3d(zmin, zmax)
       ax.set_zticks([])
       cb = fig.colorbar(img, shrink=cb_shrink, pad=cb_pad)
    elif method=='imshow':
       img = plt.imshow(np.transpose(eps), extent=(min(x), max(x), min(y), max(y)),
                        cmap=cmap, interpolation=interp, alpha=alpha)
    elif method=='pcolormesh':
       img = plt.pcolormesh(x, y, np.transpose(eps), cmap=cmap, shading=shading,
                            edgecolors=linecolor, linewidth=linewidth, alpha=alpha)
    else:
       X, Y = np.meshgrid(x, y)
       img  = ax.contourf(X, Y, eps, contours, vmin=vmin, vmax=vmax,
                          cmap=cmap, alpha=alpha)

    #--------------------------------------------------
    #- label axes and colorbars
    #--------------------------------------------------
    plt.rc('text', usetex=latex)
    xstr, ystr, estr = [r'$x$', r'$y$', r'$\epsilon$'] if latex else ['x', 'y' ,'epsilon']
    ax.set_xlabel(xstr, fontsize=fontsize, labelpad=0.50*fontsize)
    ax.set_ylabel(ystr, fontsize=fontsize, labelpad=fontsize, rotation=0)
    ax.tick_params(axis='both', labelsize=0.75*fontsize)
    cb = cb or fig.colorbar(img)
    cb.ax.set_xlabel(estr,fontsize=1.5*fontsize,rotation=0,labelpad=0.5*fontsize)
    cb.ax.tick_params(labelsize=0.75*fontsize)
    cb.locator = ticker.MaxNLocator(nbins=5)
    cb.update_ticks()


######################################################################
# plot_subregion() adds polygons representing a subregion of a meep
# computational cell to the current 2D or 3D plot, with an optional
# text label. section is a string like 'eps', 'pml', 'src_region',
# 'src_data', 'flux_region', 'flux_data', 'field_region', 'field_data'
# etc. indicating the significance of the region within the meep geometry.
#####################################################################
def plot_subregion(sim, vol=None, center=None, size=None,
                   plot3D=False, label=None, section=None, options=None):
    """
    Add polygons representing subregions of meep geometries
    to the current 2D or 3D geometry visualization.
    """

    #---------------------------------------------------------------
    #- fetch values of relevant options for the specified section
    #--------------------------------------------------------------
    keys = ['linecolor', 'linewidth', 'linestyle', 'fillcolor',
            'alpha', 'fontsize', 'zmin', 'latex']
    vals = vis_opts(keys, section=section, overrides=options)
    linecolor, linewidth, linestyle, fillcolor = vals[0:4]
    alpha, fontsize, zbar, latex = vals[4:8]

    fig = plt.gcf()
    ax = fig.gca(projection='3d') if plot3D else fig.gca()

    #--------------------------------------------------------------
    # unpack subregion geometry
    #--------------------------------------------------------------
    if vol:
       center, size = vol.center, vol.size
    v0 = np.array([center[0], center[1]])
    dx,dy=np.array([0.5*size[0],0.0]), np.array([0.0,0.5*size[1]])
    if plot3D:
        zmin, zmax = ax.get_zlim3d()
        z0 = 0.0

    #--------------------------------------------------------------
    # add polygon(s) to the plot to represent the volume
    #--------------------------------------------------------------
    def add_to_plot(c):
        ax.add_collection3d(c,zs=z0,zdir='z') if plot3D else ax.add_collection(c)

    if size[0]==0.0 or size[1]==0.0:
       #========================================
       # region has zero thickness: plot as line
       #========================================
        polygon = [ v0+dx+dy, v0-dx-dy ]
        add_to_plot( LineCollection( [polygon], colors=linecolor,
                                     linewidths=linewidth, linestyles=linestyle))
    else:
       #========================================
       # plot as polygon, with separate passes
       # for the perimeter and the interior
       #========================================
        if fillcolor: # first copy: faces, no edges
            polygon = np.array([v0+dx+dy, v0-dx+dy, v0-dx-dy, v0+dx-dy])
            pc=PolyCollection( [polygon], linewidths=0.0)
            pc.set_color(fillcolor)
            pc.set_alpha(alpha)
            add_to_plot(pc)
        if linewidth>0.0: # second copy: edges, no faces
            closed_polygon = np.array([v0+dx+dy, v0-dx+dy, v0-dx-dy, v0+dx-dy, v0+dx+dy])
            lc=LineCollection([closed_polygon])
            lc.set_linestyle(linestyle)
            lc.set_linewidth(linewidth)
            lc.set_edgecolor(linecolor)
            add_to_plot(lc)

    #####################################################################
    if label and fontsize>0:
        plt.rc('text', usetex=latex)
        if latex:
            label = label.replace('_','\_')
        x0, y0, r, h, v = np.mean(ax.get_xlim()),np.mean(ax.get_ylim()), 0, 'center', 'center'
        if size[1]==0.0:
            v = 'bottom' if center[1]>y0 else 'top'
        elif size[0]==0.0:
            r, h = (270,'left') if center[0]>x0 else (90,'right')
        if plot3D:
            ax.text(center[0], center[1], z0, label, rotation=r, fontsize=fontsize,
                    color=linecolor, horizontalalignment=h, verticalalignment=v)
        else:
            ax.text(center[0], center[1], label, rotation=r,  fontsize=fontsize,
                    color=linecolor, horizontalalignment=h, verticalalignment=v)


#################################################
#################################################
#################################################
def plot_mesh(mesh, options):
    """Invoke FENICS/dolfin plotting routine to plot FEM mesh"""

    keys = ['linecolor', 'linewidth']
    lc, lw = vis_opts(keys, section='mesh', overrides=options)
    show = vis_opts(keys, section='mesh', overrides=options)
    if lw==0.0:
        return
    try:
        import dolfin as df
        df.plot(mesh, color=lc, linewidth=lw)
    except ImportError:
        warnings.warn('failed to import dolfin module; omitting FEM mesh plot')


#################################################
# Plot one or more curves,
#################################################
def plot_data_curves(sim, center=None, size=None, superpose=True,
                     data=None, labels=None, dmin=None, dmax=None,
                     section='', options={}):

    sx, sy = size[0:2]
    if sx>0 and sy>0:
        msg="plot_data_curves: expected zero-width region, got {}x{} (skipping)"
        warnings.warn(msg.format(sx,sy),RuntimeWarning)
        return
    if np.ndim(data[0])!=1:
        msg="plot_data_curves: expected 1D data arrays, got {} (skipping)"
        warnings.warn(msg.format(np.shape(data[0])),RuntimeWarning)
        return

    keys = ['linewidth', 'linecolor', 'linestyle', 'zmin', 'zmax']
    vals = vis_opts(keys, section=section, overrides=options)
    [lw, lc, ls, zbar_min, zbar_max] = vals
    draw_baseline = (lw>0.0)

    # construct horizontal axis
    ii = 1 if sx==0 else 0
    hstart, hend = (center-0.5*size)[0:2], (center+0.5*size)[0:2]
    hmin, hmax = hstart[ii], hend[ii]
    haxis = np.linspace(hmin, hmax, len(data[0]))

    # if we are superposing the curves onto a simulation-geometry
    # visualization plot, construct the appropriate mapping that
    # squeezes the full vertical extent of the curve into the
    # z-axis interval [zmin, zmax]
    if superpose:
        ax = plt.gcf().gca(projection='3d')
        (zfloor,zceil) = ax.get_zlim()
        zmin = zfloor + zbar_min*(zceil-zfloor)
        zmax = zfloor + zbar_max*(zceil-zfloor)
        z0, dz = 0.5*(zmax+zmin), (zmax-zmin)
        dmin = dmin if dmin else np.min(data)
        dmax = dmax if dmax else np.max(data)
        d0, dd = 0.5*(dmax+dmin), (dmax-dmin)
        zs = center[1-ii]
        zdir='x' if sx==0 else 'y'
        if draw_baseline:
            lines=LineCollection([[hstart,hend]], colors='#000000',
                                 linewidths=1.0, linestyles='--')
            ax.add_collection3d(lines, zs=z0, zdir='z')

    kwargs = {'color':lc, 'linewidth':lw, 'linestyle':ls}
    for n in range(len(data)):
        kwargs['label'] = None if not labels else labels[n]
        if superpose:
            ax.plot(haxis,z0+(data[n]-d0)*dz/dd, zs=zs, zdir=zdir, **kwargs)
        else:
            plt.plot(haxis,data[n],**kwargs)


#################################################
#################################################
#################################################
# def visualize_source_distribution(sim, superpose=True):

#     if not mp.am_master():
#         return
# # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#     global options
# # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#     for ns,s in enumerate(sim.sources):
#         sc,ss=s.center,s.size
#         J2=sum([abs2(sim.get_source_slice(c,center=sc,size=ss)) for c in Exyz])
# #       M2=sum([abs2(sim.get_source_slice(c,center=sc,size=ss)) for c in Hxyz])
#         if superpose==False:
#             if ns==0:
#                 plt.ion()
#                 plt.figure()
#                 plt.title('Source regions')
#             plt.fig().subplot(len(sim.sources),1,ns+1)
#             plt.fig().title('Currents in source region {}'.format(ns))
# #        plot_data_curves(sim,superpose,[J2,M2],labels=['||J||','||M||'],
# #                         styles=['bo-','rs-'],center=sc,size=ssu
#         plot_data_curves(sim,center=sc,size=ss, superpose=superpose,
#                          data=[J2], labels=['J'], options=options)


#################################################
#################################################
#################################################
def plot_dft_flux(sim, dft_cells, superpose=True, nf=0, options={}):

    if not mp.am_master():
        return

    method = vis_opt('method',section='flux_data',overrides=options)
    if method.lower() in ['omit','none']:
        return

    # first pass to get arrays of poynting flux strength for all cells
    flux_cells, flux_arrays = [c for c in dft_cells if c.celltype=='flux'], []
    for cell in flux_cells:
        w, EH = cell.grid.weights, cell.get_EH_slices(nf=nf)
        flux_arrays.append( 0.25*np.real(w*(np.conj(EH[0])*EH[3] - np.conj(EH[1])*EH[2])) )

    # second pass to plot
    for n, cell in enumerate(flux_cells):    # second pass to plot
        if superpose==False:
            if n==0:
                plt.figure()
                plt.title('Poynting flux')
            plt.subplot(len(flux_cells),1,n)
            plt.gca().set_title('Flux cell {}'.format(n))
        cn, sz = cell.region.center, cell.region.size
        max_flux=np.amax([np.amax(fa) for fa in flux_arrays])
        plot_data_curves(sim, center=cell.region.center, size=cell.region.size,
                         data=[flux_arrays[n]], superpose=superpose,
                         labels=['flux through cell {}'.format(n)],
                         dmin=-max_flux, dmax=max_flux,
                         section='flux_data', options=options)

###############################################
################################################
################################################
def fc_name(c,which):
    name=mp.component_name(c)
    return name if which=='scattered' else str(name[0].upper())+str(name[1])

def abs2(z):
    """squared magnitude of complex number"""
    return np.real(np.conj(z)*z)


def field_func_array(fexpr,x,y,z,w,cEH,EH):
    if fexpr=='re(Ex)':
        return np.real(EH[0])
    if fexpr=='im(Ex)':
        return np.imag(EH[0])
    if fexpr=='re(Ey)':
        return np.real(EH[1])
    if fexpr=='im(Ey)':
        return np.imag(EH[1])
    if fexpr=='re(Ez)':
        return np.real(EH[2])
    if fexpr=='im(Ez)':
        return np.imag(EH[2])
    if fexpr=='re(Hx)':
        return np.real(EH[3])
    if fexpr=='im(Hx)':
        return np.imag(EH[3])
    if fexpr=='re(Hy)':
        return np.real(EH[4])
    if fexpr=='im(Hy)':
        return np.imag(EH[4])
    if fexpr=='re(Hz)':
        return np.real(EH[5])
    if fexpr=='im(Hz)':
        return np.imag(EH[5])
    if fexpr=='abs2(H)':
        return abs2(EH[3]) + abs2(EH[4]) + abs2(EH[5])
    if True: # fexpr=='abs2(E)':
        return abs2(EH[0]) + abs2(EH[1]) + abs2(EH[2])

# ####################################################################
# this routine is intended as a helper function called by
# visualize_dft_fields, not directly by user
# ####################################################################
# def plot_dft_fields(sim, field_cells=[], field_funcs=None,
#                          ff_arrays=None, options=None, nf=0):
#
#     options       = options if options else def_field_options
#     cmap          = options['cmap']
#     edgecolors    = options['line_color']
#     linewidth     = options['line_width']
#     alpha         = options['alpha']
#     fontsize      = options['fontsize']
#     plot_method   = options['plot_method']
#     num_contours  = options['num_contours']
#     shading       = 'gouraud' if linewidth==0.0 else 'none'
#     interpolation = 'gaussian' if linewidth==0.0 else 'none'
#
#     for ncell, cell in enumerate(field_cells):
#         (x,y,z,w,cEH,EH)=unpack_dft_cell(sim,cell,nf=nf)
#         X, Y = np.meshgrid(x, y)
#         if ff_arrays is None:
#             plt.figure()
#             plt.suptitle('DFT cell {}'.format(ncell+1))
#
#         if field_funcs==None:
#             ops=['Re', 'Im', 'abs']
#             field_funcs=[texify(op+'('+mp.component_name(c)+')') for c in cEH for op in ops]
#             rows,cols=len(cEH),len(ops)
#         else:
#             rows,cols=1,len(field_funcs)
#
#         def op(F,index):
#             return np.real(F) if op=='Re' else np.imag(F) if op=='Im' else np.abs(F)
#
#         for row in range(rows):
#             for col in range(cols):
#                 nplot = row*cols + col
#                 data = ff_arrays[nplot] if ff_arrays else op(EH[row],ops[col])
#                 plt.subplot(rows, cols, nplot+1)
#                 ax=plt.gca()
#                 ax.set_title(field_funcs[nplot])
#                 ax.set_xlabel(r'$x$', fontsize=fontsize, labelpad=0.5*fontsize)
#                 ax.set_ylabel(r'$y$', fontsize=fontsize, labelpad=fontsize, rotation=0)
#                 ax.tick_params(axis='both', labelsize=0.75*fontsize)
#                 ax.set_aspect('equal')
#                 plt.tight_layout()
#                 if plot_method=='imshow':
#                     img = plt.imshow(np.transpose(data), extent=(min(x), max(x), min(y), max(y)),
#                                      cmap=cmap, interpolation=interpolation, alpha=alpha)
#                 elif plot_method=='pcolormesh':
#                     img = plt.pcolormesh(x,y,np.transpose(data), cmap=cmap, shading=shading,
#                                          edgecolors=edgecolors, linewidth=linewidth, alpha=alpha)
#                 else:
#                     img = ax.contourf(X,Y,np.transpose(data),num_contours, cmap=cmap,alpha=alpha)
#                 #cb=plt.colorbar(img,shrink=options['colorbar_shrink'], pad=options['colorbar_pad'])
#                 cb=happy_cb(img,ax)
#                 #cb.ax.set_xlabel(ff,fontsize=1.5*fontsize,rotation=0,labelpad=0.5*fontsize)
#                 cb.locator = ticker.MaxNLocator(nbins=5)
#                 cb.update_ticks()
#
#     plt.tight_layout()
#     plt.show(False)
#     plt.draw()
#     return 0
#

#####################################################################
#####################################################################
#####################################################################
##################################################
def happy_cb(img, axes):
    """nice colorbars for subplots, from https://joseph-long.com/writing/colorbars"""
    divider = make_axes_locatable(axes)
    cax = divider.append_axes("left", size="5%", pad=0.05)
    return axes.figure.colorbar(img, cax=cax)

#################################################
#################################################
#################################################
def plot_dft_fields(sim, dft_cells, superpose=True, field_funcs=None,
                    ff_arrays=None, nf=0, options={}):

    if not mp.am_master():
        return

    field_cells=[c for c in dft_cells if c.celltype=='fields']
    full_cells=[c for c in field_cells if np.all(c.region.size==sim.cell_size) ]
    field_cells=full_cells if full_cells else field_cells

    if len(field_cells)==0:
        return

    if superpose and not isinstance(plt.gcf().gca(),axes3d.Axes3D):
        warnings.warn("plot_dft_fields: non-3D plot, can't superpose.")
        superpose=False

    if not superpose:
        return
#        return plot_dft_fields(sim, field_cells, field_funcs, ff_arrays, options, nf=nf)

    # the remainder of this routine is for the superposition case
    keys = ['cmap', 'alpha', 'contours', 'fontsize', 'zmin', 'zmax',
            'cb_pad', 'cb_shrink', 'latex', 'method']
    vals = vis_opts(keys, section='fields_data', overrides=options)
    cmap, alpha, num_contours, fontsize   = vals[0:4]
    zrel_min, zrel_max, cb_pad, cb_shrink = vals[4:8]
    latex, method                         = vals[8:10]

    if method.lower() in ['omit','none']:
        return

    if field_funcs is None:
        field_funcs = ['abs2(E)']
    nz = len(field_funcs)
    zrels=[0.5*(zrel_min+zrel_max)] if nz==1 else np.linspace(zrel_min,zrel_max,nz)

    for n, cell in enumerate(field_cells):
        x, y, z, w = cell.grid.xtics, cell.grid.ytics, cell.grid.ztics, cell.grid.weights
        cEH, EH = cell.components, cell.get_EH_slices(nf=nf)
        X, Y = np.meshgrid(x, y)
        fig = plt.gcf()
        ax  = fig.gca(projection='3d')
        (zmin,zmax)=ax.get_zlim()
        for n,(ff,zrel) in enumerate(zip(field_funcs,zrels)):
            data = ff_arrays[n] if ff_arrays else field_func_array(ff,x,y,z,w,cEH,EH)
            z0   = zmin + zrel*(zmax-zmin)
            img  = ax.contourf(X, Y, np.transpose(data), num_contours,
                               cmap=cmap, alpha=alpha, zdir='z', offset=z0)
            colorbar_cannibalize=True
            if colorbar_cannibalize:
                cax=fig.axes[-1]
                cb=plt.colorbar(img, cax=cax)
            else:
                cb=plt.colorbar(img, shrink=cb_shrink, pad=cb_pad, panchor=(0.0,0.5))
            #cb.set_label(ff,fontsize=1.0*fontsize,rotation=0,labelpad=0.5*fontsize)
            label = ff if not latex else texify(ff)
            cb.ax.set_xlabel(label,fontsize=fontsize,rotation=0,labelpad=0.75*fontsize)
            cb.ax.tick_params(labelsize=0.75*fontsize)
            cb.locator = ticker.MaxNLocator(nbins=5)
            cb.update_ticks()
            cb.draw_all()


##################################################
#################################################
#################################################
def texify(expr):
    """Return expr modified to play well with latex formatting."""

    expr.replace('_',r'\_')
    expr=re.sub(r'([eEhH])([xyz])',r'\1_\2',expr)
    expr=re.sub(r'e_','E_',expr)
    expr=re.sub(r'H_','H_',expr)
    expr=re.sub(r'abs\((.*)\)',r'|\1|',expr)
    expr=re.sub(r'abs2\((.*)\)',r'|\1|^2',expr)
    loglike=['Re','Im']
    for s in loglike:
        expr=re.sub(s,'\textrm{'+s+'}',expr)
    return r'$'+expr+'$'

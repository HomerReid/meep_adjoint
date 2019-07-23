""" this file is mostly convenience wrappers around various objects in core pymeep

    v3, V3 convert between mp.Vector3 and simple lists or np.arrays of coordinates

    Grid repackages 'array metadata' with some convenient redundancy

    Subregion replaces the 6 separate pymeep data structures used
    to describe grid subregions ('FluxRegion', 'FieldsRegion', etc.)

    DFTCell similarly replaces the 5 separate data structures used
    to describe sets of frequency-domain field components.
"""

import numpy as np
import meep as mp
import warnings
from collections import namedtuple

from . import get_adjoint_option as adj_opt

######################################################################
# general-purpose constants and utility routines
######################################################################
ORIGIN           = np.zeros(3)
XHAT, YHAT, ZHAT = [ np.array(a) for a in [[1.,0,0], [0,1.,0], [0,0,1.]] ]
E_CPTS           = [mp.Ex, mp.Ey, mp.Ez]
H_CPTS           = [mp.Hx, mp.Hy, mp.Hz]
EH_CPTS          = E_CPTS + H_CPTS
EH_TRANSVERSE    = [ [mp.Ey, mp.Ez, mp.Hy, mp.Hz],
                     [mp.Ez, mp.Ex, mp.Hz, mp.Hx],
                     [mp.Ex, mp.Ey, mp.Hx, mp.Hy] ]


def V3(a1=0.0, a2=0.0, a3=0.0):
    v=v3(a1,a2,a3)
    return mp.Vector3(v[0],v[1],v[2])


def v3(a1=0.0, a2=0.0, a3=0.0):
    if type(a1) in [list, np.array, np.ndarray]:
        return np.array([float(x) for x in (list(a1)+[0,0])[0:3] ])
    if isinstance(a1,mp.Vector3):
        return a1.__array__()
    return np.array([a1,a2,a3])



######################################################################
# fix a bug in libmeep
######################################################################
def fix_array_metadata(xyzw, center, size):
    for d in range(0,3):
        if self.region.size[d]==0.0 and xyzw[d][0]!=self.region.center[d]:
            warnings.warn('correcting for bug in get_array_metadata: {}={}-->{}'.format('xyz'[d],xyzw[d][0],self.region.center[d]))
            xyzw[d]=np.array( [ self.region.center[d] ])
        else:
            xyzw[d]=np.array(xyzw[d])


######################################################################
# 'Grid' is a convenience extension of 'array metadata'
######################################################################
Grid = namedtuple('Grid', ['xtics', 'ytics', 'ztics', 'points', 'weights', 'shape'])

def make_grid(size, center=np.zeros(3), dims=None, length=None):
    nd = len(np.flatnonzero(size))
    center, size = np.array(center)[0:nd], np.array(size)[0:nd]
    if length is not None:
        dims = [max(1,int(np.ceil(s/length))) for s in size]
    if dims is None:
        dims = [(10 if s>0 else 1) for s in size]
    pmin, pmax = center-0.5*size, center+0.5*size
    tics = [np.linspace(a, b, n) for (a, b, n) in zip(pmin, pmax, dims)]
    if len(tics)==2:
        tics.append([0])
    points = [np.array([x, y, z]) for x in tics[0] for y in tics[1] for z in tics[2] ]
    vol, ntot = np.prod([s for s in size if s>0]), np.prod(dims)
    weights = (vol/ntot) * np.ones(ntot)
    shape = [len(t) for t in tics if len(t)>1]
    return Grid(tics[0], tics[1], tics[2], points, weights, shape)


def xyzw2grid(xyzw):
    return Grid( xyzw[0],
                 xyzw[1],
                 xyzw[2],
                [mp.Vector3(x,y,z) for x in xyzw[0] for y in xyzw[1] for z in xyzw[2]],
                 xyzw[3].flatten(),
                 xyzw[3].shape
               )


class Subregion(object):
    """ Specification of grid subregion

        A Subregion is a finite hyperrectangular spatial region contained
        within the meep computational cell.
        A subregion may be of codimension 1 (i.e. it is a line in 2D
        or a plane in 3D), in which case it has a normal direction.
        Codim-1 subregions are used to define eigenmode sources and
        to evaluate Poynting fluxes and eigenmode expansion coefficients.

        Alternatively, the subregion may be of codimension 0, i.e.
        it is a full rectangle (2D) or box (3D), or of dimemsion 0, i.e.
        a point.
    """
    def __init__(self, xmin=None, xmax=None, center=ORIGIN, size=None,
                       normal=None, dir=None, name=None):
        if (xmin is not None) and (xmax is not None):
            (self.xmin, self.xmax)   = (v3(xmin), v3(xmax))
            (self.center, self.size) = (0.5*(self.xmax+self.xmin)), ((self.xmax-self.xmin))
        elif size is not None:
           (self.center, self.size) = (v3(center), v3(size))
           self.xmin, self.xmax   = [self.center + sgn*self.size  for sgn in [-1,1] ]
        self.normal, self.name = (dir if normal is None else normal), name

dft_cell_names=[]

class DFTCell(object):
    """ Simpler data structure for frequency-domain fields in MEEP

        The instantiating data of a DFTCell are a grid subregion, a set of
        field components, and a list of frequencies. These metadata fields
        remain constant throughout the lifetime of a DFTCell.
        In addition to the metadata, instances of DFTCell allocate
        internal arrays of DFT registers in which the specified components of the
        frequency-domain fields at the specified grid points and frequencies
        are accumulated over the course of a MEEP timestepping run. These
        registers are reset to zero at the beginning of the next timestepping
        run, but in the meantime you can use the ``save_fields`` method
        to save an internally cached snapshot of the fields computed on a
        given timestepping run.

        Note: for now, all arrays are stored in memory. For large calculations with
        many DFT frequencies this may become impractical. TODO: disk caching.

        The internally-stored frequency-domain fields at a single frequency
        may be fetched via the get_EH_slice (single component) or
        get_EH_slices (all components) methods. By default these routines
        return slices of the currently active fields (i.e. the fields computed
        on the most recent timestepping run), but they accept an optional
        parameter specifying the label of a data set stored by a call to
        ``save_fields`` after a previous timestepping run.

        For convenience, DFTCell also offers a get_eigenmode_slices() method that
        computes and returns eigenfield profiles in the same format as DFT fields.

        DFTCells also know how to crunch their internally-stored field-component
        data to compute various physical quantities of interest, such as
        Poynting fluxes and field energies. We consider this the primary
        functionality exported by DFTCell, and thus implement it as the
        __call__ method of the class.

        DFTCell replaces the DftFlux, DftFields, DftNear2Far, DftForce, DftLdos,
        and DftObj structures in core pymeep.
    """

    ######################################################################
    ######################################################################
    ######################################################################
    def __init__(self, region, components=None, fcen=None, df=None, nfreq=None):

        self.region     = region
        self.normal     = region.normal
        self.celltype   = 'flux' if self.normal is not None else 'fields'
        self.components = components or (EH_TRANSVERSE[self.normal] if self.normal is not None else EH_CPTS)
        self.fcen       = adj_opt('fcen') if fcen is None else fcen
        self.df         = adj_opt('df') if df is None else df
        self.nfreq      = adj_opt('nfreq') if nfreq is None else nfreq
        self.freqs      = [self.fcen] if self.nfreq==1 else np.linspace(self.fcen-0.5*self.df, self.fcen+0.5*self.df, self.nfreq)

        self.sim        = None  # mp.simulation for current simulation
        self.dft_obj    = None  # meep DFT object for current simulation

        self.EH_cache   = {}    # cache of frequency-domain field data computed in previous simulations
        self.eigencache = {}    # cache of eigenmode field data to avoid redundant recalculations

        global dft_cell_names

        if region.name is not None:
            self.name = '{}_{}'.format(region.name, self.celltype)
        else:
            self.name = '{}_{}'.format(self.celltype, len(dft_cell_names))

        dft_cell_names.append(self.name)

        # Although the subgrid covered by the cell is independent of any
        # mp.simulation, at present we can't compute subgrid metadata
        # without first instantiating a mp.Simulation, so we have to
        # wait to initialize the 'grid' field of DFTCell. TODO make the
        # grid metadata calculation independent of any mp.Simulation or meep::fields
        # object; it only depends on the resolution and extents of the Yee grid
        # and thus logically belongs in `vec.cpp` or another code module that
        # exists independently of fields, structures, etc.
        self.grid = None

    ######################################################################
    # 'register' the cell with a MEEP timestepping simulation to request
    # computation of frequency-domain fields
    ######################################################################
    def register(self, sim):
        self.sim = sim
        if self.celltype == 'flux':
            flux_region  = mp.FluxRegion(V3(self.region.center),V3(self.region.size),direction=self.normal)
            self.dft_obj = sim.add_flux(self.fcen,self.df,self.nfreq,flux_region)
        else:
            self.dft_obj = sim.add_dft_fields(self.components, self.freqs[0], self.freqs[-1], self.nfreq, center=V3(self.region.center), size=V3(self.region.size))

        # take this opportunity to initialize simulation-dependent fields
        if self.grid is None:
            xyzw=sim.get_array_metadata(center=V3(self.region.center), size=V3(self.region.size), collapse=True, snap=True)
            fix_array_metadata(xyzw, center, size)
            self.grid = xyzw2grid(xyzw)

    ######################################################################
    # Compute an array of frequency-domain field amplitudes, i.e. a
    # frequency-domain array slice, for a single field component at a
    # single frequency in the current simulation. This is like
    # mp.get_dft_array(), but 'zero-padded:' when the low-level DFT object
    # does not have data for the requested component (perhaps because it vanishes
    # identically by symmetry), this routine returns an array of the expected
    # dimensions with all zero entries, instead of a rank-0 array that prints
    # out as a single preposterously large or small floating-point number,
    # which is the not-very-user-friendly behavior of mp.get_dft_array().
    ######################################################################
    def get_EH_slice(self, c, nf=0):
        EH = self.sim.get_dft_array(self.dft_obj, c, nf)
        return EH if np.ndim(EH)>0 else 0.0j*np.zeros(self.grid.shape)

    ######################################################################
    # Return a 1D array (list) of arrays of frequency-domain field amplitudes,
    # one for each component in this DFTCell, at a single frequency in a
    # single MEEP simulation. The simulation in question may be the present,
    # ongoing simulation (if label==None), in which case the array slices are
    # read directly from the currently active meep DFT object; or it may be a
    # previous simulation (identified by label) for which
    # DFTCell::save_fields(label) was called at the end of timestepping.
    ######################################################################
    def get_EH_slices(self, label=None, nf=0):
        if label is None:
            return [ self.get_EH_slice(c, nf=nf) for c in self.components ]
        elif label in self.EH_cache:
            return self.EH_cache[label][nf]
        raise ValueError("DFTCell {} has no saved data for label '{}'".format(self.name, label))


    ######################################################################
    # substract incident from total fields to yield scattered fields
    ######################################################################
    def subtract_incident_fields(self, EHT, nf=0):
        EHI = self.get_EH_slices(label='incident', nf=nf)
        for nc, c in enumerate(self.components):
            EHT[nc] -= EHI[nc]


    ####################################################################
    # This routine tells the DFTCell to create and save an archive of
    # the frequency-domain array slices for the present simulation---i.e.
    # to copy the frequency-domain field data out of the sim.dft_obj
    # structure and into an appropriate data buffer in the DFTCell,
    # before the sim.dft_obj data vanish when sim is reset for the next run.
    # This routine should be called after timestepping is complete. The
    # given label is used to identify the stored data for future retrieval.
    ######################################################################
    def save_fields(self, label):
        self.EH_cache[label] = [self.get_EH_slices(nf=nf) for nf in range(len(self.freqs))]


    ######################################################################
    # Return a 1D array (list) of arrays of field amplitudes for all
    # tangential E,H components at a single frequency---just like
    # get_EH_slices()---except that the sliced E and H fields are the
    # fields of eigenmode #mode.
    ######################################################################
    def get_eigenmode_slices(self, mode, nf=0):

        # look for data in cache
        tag='M{}.F{}'.format(mode,nf)
        if self.eigencache and tag in self.eigencache:
            return self.eigencache[tag]

        # data not in cache; compute eigenmode and populate slice arrays
        freq, dir, k0 = self.freqs[nf], self.normal, mp.Vector3()
        vol = mp.Volume(V3(self.region.center),V3(self.region.size))
        eigenmode = self.sim.get_eigenmode(freq, dir, vol, mode, k0)

        def get_eigenslice(eigenmode, grid, c):
            return np.reshape( [eigenmode.amplitude(p,c) for p in grid.points], grid.shape )

        eh_slices=[get_eigenslice(eigenmode,self.grid,c) for c in self.components]

        # store in cache before returning
        if self.eigencache is not None:
            self.eigencache[tag]=eh_slices

        return eh_slices


    ######################################################################
    # compute an objective quantity, i.e. an eigenmode
    # coefficient or a scattered or total power.
    ######################################################################
    def __call__(self, qcode, mode=0, nf=0):
        """ Compute and return the value of an objective quantity.
            Args:
                qcode: string identifying the quantity ('S' for flux, etc.)
                mode:  eigenmode index, only needed for some quantities
                nf:    frequency index
        """
        w  = np.reshape(self.grid.weights,self.grid.shape)
        EH = self.get_EH_slices(nf=nf)
        quantity=qcode.upper()
        if qcode.islower():
             self.subtract_incident_fields(EH,nf)
        if quantity=='S':
            return np.real(np.sum(w*( np.conj(EH[0])*EH[3] - np.conj(EH[1])*EH[2]) ))
        if quantity.upper() in 'PM':
            eh = self.get_eigenmode_slices(mode, nf)  # EHList of eigenmode fields
            eH = np.sum( w*(np.conj(eh[0])*EH[3] - np.conj(eh[1])*EH[2]) )
            hE = np.sum( w*(np.conj(eh[3])*EH[0] - np.conj(eh[2])*EH[1]) )
            sign=1.0 if qcode=='P' else -1.0
            return (eH + sign*hE)/4.0
        if quantity in ['UE','UH','UT']:
           q=0.0
           if quantity in ['UE', 'UT']:
               eps = self.sim.get_dft_array(self.dft_obj, mp.Dielectric, nf)
               E2  = np.sum( [np.conj(EH[nc])*EH[nc] for nc,c in enumerate(self.components) if c in E_CPTS], axis=0 )
               q  += 0.5*np.sum(w*eps*E2)
           if quantity in ['UH', 'UT']:
               mu  = self.sim.get_dft_array(self.dft_obj, mp.Permeability, nf)
               H2  = np.sum( [np.conj(EH[nc])*EH[nc] for nc,c in enumerate(self.components) if c in H_CPTS], axis=0 )
               q  += 0.5*np.sum(w*mu*H2)
           return q
        else: # TODO: support other types of objectives quantities?
            ValueError('DFTCell {}: unsupported quantity type {}'.format(self.name,qcode))

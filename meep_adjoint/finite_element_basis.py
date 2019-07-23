######################################################################
# FiniteElementBasis.py
######################################################################
import sys
import re
from numbers import Number

import numpy as np

import meep as mp

from . import Basis, v3, V3


######################################################################
# try to load dolfin (FENICS) module, but hold off on complaining if
# unsuccessful until someone actually tries to do something that requires it
######################################################################
try:
    import dolfin as df
    from dolfin import dx      # because it's confusing to write df.dx
except ImportError:
    pass


#----------------------------------------------------------------------
#----------------------------------------------------------------------
# FiniteElementBasis class
#----------------------------------------------------------------------
#----------------------------------------------------------------------
class FiniteElementBasis(Basis):
    """
    FiniteElementBasis describes a basis of 2D or 3D finite-element functions
    over a rectangle, parallelepiped, or more complicated mesh, implemented
    using the FENICS finite-element package.

    Raises: ImportError if dolfin module not found
    """

    ############################################################
    ############################################################
    ############################################################
    def __init__(self, mesh=None, mesh_file=None,
                       region=None, size=None, center=np.zeros(3),
                       nseg=None, element_length=None,
                       element_type='Lagrange 1', offset=1.0):
        """Finite-element basis with given support and resolution.

           Args:

               mesh(dolfin.Mesh):
               mesh_file(str):

                   Explicit specification of finite-element mesh as a
                   dolfin.Mesh object or a dolfin-format mesh file.

               region (Subregion) __OR__ size, center (v3):
               nseg (list of int) __OR__ element_length(float)
                   If mesh and mesh_file are both absent, the mesh is taken
                   to be a rectangular or cubic lattice over the box-shaped
                   domain given by region (if present) or (size,center).

                   If nseg is specified, nseg[d] is the number of segments
                   into which the dth linear dimension of the region is discretized.

                   Otherwise, element_length (scalar,float) specifies
                   a target discretization lengthscale. If element_length is None,
                   it is taken from options['element_length']

               element_type(str):
                   The type of finite-element basis function defined on the mesh,
                   expressed as a compound string of the form 'family degree'
                   for functions of finite-element family *family* and
                   nonnegative-integer degree *degree*. For example,
                   'Lagrange 1' and 'Lagrange 2' correspond to the usual
                   linear and quadratic functions supported on triangles/tetrahedra.

                   For more information on finite-element types, consult e.g.

                   1. The FENICS documentation:
                      https://fenicsproject.org/docs/dolfin/1.5.0/python/programmers-reference/mesh/index.html

                   2. The "Periodic Table of Finite Elements:"
                      http://femtable.org/
        """

        if 'dolfin' not in sys.modules:
            msg='failed to load dolfin (FENICS) module, needed for FiniteElementBasis'
            raise ImportError(msg)

        if mesh_file is not None:
            mesh = df.Mesh(mesh_file)

        if mesh is not None: # get bounding box from mesh coordinates
            pmin, pmax = [ op(mesh.coordinates(),0) for op in [np.amin, np.amax] ]
            (center, size) = (0.5*(pmax+pmin), (pmax-pmin))
        else:
            (center,size) = (v3(region.center), v3(region.size)) if region else (v3(center),v3(size))
            if not element_length:
                element_length=np.amax(size)/10.0
            nn = nseg if nseg else [ int(np.ceil(s/element_length)) for s in size ]
            nd = 3 if (len(nn)==3 and nn[2]>0) else 2
            pmin, pmax = [ df.Point(center + pm*size) for pm in [-0.5,0.5] ]
            if nd==2:
                mesh = df.RectangleMesh(pmin,pmax,nn[0],nn[1],diagonal='left')
            else:
                mesh = df.BoxMesh(pmin,pmax,nn[0],nn[1],nn[2])

        family, degree = element_type.split()[0:2]
        self.fs  = df.FunctionSpace(mesh,family,int(degree))
        super().__init__(self.fs.dim(), size=size, center=center, offset=offset )


    def project(self, g, grid=None):
        """
        Given an arbitrary function g(x), invoke the performance-optimized routines
        in FENICS to compute the projection g^p(x) == \sum_n g^p_n b_n(x).

        Parameters:
            g, grid: function specification as in make_dolfin_callable
        Return value:
            Projection coefficients as numpy array of dimension self.dim
        """
        g = make_dolfin_callable(g, grid=grid, fs=self.fs, offset=-1.0*self.offset)
        return df.project(g, self.fs).vector().vec().array


    def parameterized_function(self, beta_vector):
        """
        Construct and return a callable, updatable element of the function space.

        Args:
            beta_vector (np.array of dimension self.dim and datatype float):
                expansion coefficients

        Returns:
            a class `func` with the following properties: After the statement
                func = basis.parameterized_function(beta_vector)
            we have:
            1. func is a callable scalar function of one spatial variable:
               func(p) = f_0 + \sum_n beta_n * b_n(p)
            2. func has a set_coefficients method that updates an internal cache, i.e.
                func.set_coefficients(new_beta_vector)
        """
        class _ParameterizedFunction(object):
            def __init__(self, basis, beta_vector):
                (self.offset, self.f) = (basis.offset, df.Function(basis.fs))
                self.f.set_allow_extrapolation(True)
                self.set_coefficients(beta_vector)
            def set_coefficients(self, beta_vector):
                self.f.vector().set_local(beta_vector)
            def __call__(self, p):
                return self.offset + self.f(df.Point(v3(p)))
            def func(self):
                def _f(p):
                    return self(p)
                return _f

        return _ParameterizedFunction(self, beta_vector)


    ############################################################
    # the self-contained implementations above suffice to handle
    # everything needed for mp.adjoint, so the remaining
    # class methods are actually not needed and will never be
    # invoked for mp.adjoint calculations, but we provide
    # implementations just for reference.
    ############################################################
    def get_bvector(self, p):
        # get mesh cell containing p
        p, fs       = v3(p), self.fs
        dm, el, msh = fs.dofmap(), fs.element(), fs.mesh()
        cidx        = msh.bounding_box_tree().compute_first_entity_collision(df.Point(p))
        cell        = df.Cell(msh,cidx)
        cdofs, cdir = cell.get_vertex_coordinates(), cell.orientation()

        # get global indices and values (at p) of this cell's basis functions
        indices, values = dm.cell_dofs(cidx), el.evaluate_basis_all(p,cdofs,cdir)

        bvec = np.zeros(self.dim)
        bvec[indices]=values
        return bvec


    # optimized dolfin/FENICS assembly of Gram matrix
    def gram_matrix(self,grid=None):
        u,v = df.TrialFunction(self.fs), df.TestFunction(self.fs)
        return df.assemble(u*v*dx).array()


    # optimized dolfin/FENICS assembly of inner-product vector
    def inner_product(self, g, grid=None):
        g = make_dolfin_callable(g, grid=grid, fs=self.fs, offset=-1.0*self.offset)
        v = df.TestFunction(self.fs)
        return df.assemble( g*v*dx ).get_local()

# --------------------------------------------------------------------
# --------------------------------------------------------------------
# --------------------------------------------------------------------
def parameterized_function2(basis, beta_vector):

       ###################################################
       #
       ###################################################
       offset, f = basis.offset, df.Function(basis.fs)
       f.set_allow_extrapolation(True)
       f.vector().set_local(beta_vector)

       def _set_coefficients(beta_vector):
           f.vector().set_local(beta_vector)

       def _eval_f(p):
           return offset + f(df.Point(v3(p)))

       return _eval_f, _set_coefficients


#----------------------------------------------------------------------
# the next few routines/classes are general-purpose FENICS helper
# functions used by class methods in FiniteElementBasis
#----------------------------------------------------------------------
def make_dolfin_callable(g, grid=None, fs=None, offset=0.0):
    """
    given a basis of expansion functions (or a 'function space' in FENICS
    parlance), a common task is to compute the projection onto the basis
    of some arbitrary given input function g(x), which may be specified
    in various different ways. FENICS implements optimized routines for
    this procedure, the use of which requires that the input function be
    packaged in the form of dolfin entities like 'Expression' or 'Function'
    or 'Constant'. This is a switchboard routine that hands off to
    one of the helper routines/classes below to effect this packaging
    for various types of python function specification.

    Parameters:
        g: target function specification, which may be any of the following:
            (a) callable python function of a 2D or 3D array variable
            (b) string describing a mathematical expression of x,y,z
            (c) constant
            (d) numpy array of function samples on the regular grid 'grid'

        grid: Grid on which target function was sampled for case (d) above

        fs:   Function space, needed only for case (b) above, and then
              only to ensure sufficiently a high-degree representation

        offset: constant offset added to value of caller's g function

    Return value:
        dolfin/FENICS callable function that may be passed as e.g.
        the 'v' parameter to dolfin.fem.projection.project()
    """

    if callable(g):
        return ExpressionFromPyFunc(g, offset=offset)
    elif isinstance(g, str):
        return ExpressionFromString(g, fs, offset=offset)
    elif isinstance(g, np.ndarray):
        return FunctionFromSamples(g, grid, offset=offset)
    elif isinstance(g, Number):
        return df.Constant(g+offset)
    raise ValueError('invalid function specification in make_dolfin_callable')


def ExpressionFromPyFunc(g_func, offset=0.0):
    """
    Construct a callable dolfin.Expression from a callable python function.
    Inputs: g_func: python function of a single 2D or 3D coordinate array variable p
    Returns: dolfin Expression (callable function of 2D or 3D coordinate array)
    """
    # g_func should be a python function that inputs a single variable p
    # (a list or np.array giving the coordinates of the evaluation point)
    # and returns g(p).
    class MyExpression(df.UserExpression):
        def eval(self, values, x):
            values[0] = g_func(x) + offset
    return MyExpression()


def ExpressionFromString(g_str, fs, offset=0.0):
    """
    Construct a callable dolfin.Expression from a string describing a function.
    Inputs: g_str (str): mathematical expression involving x, y, z
            fs (df.FunctionSpace): FunctionSpace, needed only to set degree of expression
    Returns: dolfin Expression (callable function of 2D or 3D coordinate array)
    """
    for n, c in enumerate(['x', 'y', 'z']):   # rename variables: x,y,z --> x[0,1,2]
        ptrn  = r'([^a-zA-Z_]?){}([^a-zA-Z0-9_]?)'.format(c)
        subs  = r'\1x[{}]\2'.format(n)
        g_str = re.sub(ptrn,subs,g_str)
    g_str += ('' if offset==0.0 else ' + {}'.format(offset))
    return df.Expression(g_str, degree=fs.ufl_element().degree() + 2 )


def FunctionFromSamples(g_samples, grid, offset=0.0):
    """
    Given an array of function samples at the points of a grid, construct
    a callable dolfin function by interpolation.
    Inputs:  g_samples (np.array): 2D or 3D array of function samples
             grid (Grid):          grid of Points at which function was sampled
    Returns: Callable dolfin function of 2D or 3D coordinate array p
    """
    n, nd      = np.shape(g_samples), len(np.shape(g_samples))
    x, y, z    = grid.xtics, grid.ytics, grid.ztics
    vmin, vmax = [x[0], y[0], z[0]], [x[-1], y[-1], z[-1]]
    pmin, pmax = df.Point(vmin[0:nd]), df.Point(vmax[0:nd])
    if nd==2:
        mesh = df.RectangleMesh(pmin, pmax, n[0], n[1])
    else:
        mesh = df.BoxMesh(pmin, pmax, n[0], n[1], n[2])
    grid_space = df.FunctionSpace(mesh,'Lagrange',1)
    g = df.Function(grid_space)
    v = g.vector()
    delta=[ t[2]-t[1] if len(t)>1 else 1.0 for t in [x,y,z] ]
    for i,p in enumerate(grid_space.tabulate_dof_coordinates()):
        n = [ int(round((p[d]-pmin[d])/delta[d])) for d in range(nd) ]
        v[i] = g_samples[tuple(n)] + offset
    g.set_allow_extrapolation(True)
    return g

#----------------------------------------------------------------------
#----------------------------------------------------------------------
# end of FiniteElementBasis class
#----------------------------------------------------------------------
#----------------------------------------------------------------------


#----------------------------------------------------------------------
#----------------------------------------------------------------------
# This is a poor man's version of FiniteElementBasis that enables 2D
# adjoint modeling when the dolfin / FENICS module is not available.
# Equivalent to FiniteElementBasis for element_type='Lagrange' and
# element_order=1.
#
# How it works: The sides of an (lx x ly) rectangle are subdivided into
# num_elements[0] x num_elements[1] segments (or into segments of
# length element_size). To each node in the resulting (NX+1)*(NY+1)
# grid of nodes we assign a single basis function. The basis function
# associated with node #n is only supported on those triangles
# having node #n as a vertex; it takes the value 1 at node #n and
# falls linearly to zero at the neighboring nodes. Indexing: The
# node with grid coordinates (nx,ny) (0 \le ni \le N_i) is assigned '
# index nx*(NY+1) + ny, following the conventional MEEP scheme for grid indexing.
#----------------------------------------------------------------------
#----------------------------------------------------------------------
#
# class SimpleFiniteElementBasis(Basis):
#
#     def __init__(self, size=np.zeros(3), center=np.zeros(3),
#                        dims=None, element_length=0.25, offset=1.0):
#         if len(size)>2 and size[2]>0.0:
#             mp.abort('SimpleFiniteElementBasis not implemented for 3D problems')
#         self.center = center
#         self.size   = [size[0], size[1]]
#         self.dims   = dims if dims is not None else [int(np.ceil(s/element_length)) for s in self.size]
#         self.delta  = [s/(1.0*dim) for s,dim in zip(self.size,self.dims)]
#         super().__init__( (self.dims[0]+1)*(self.dims[1]+1), offset=offset )
#
#     def in_grid(self, n, ofs=[0,0]):
#         return np.all([nn+oo in range(0,dim+1) for(nn,oo,dim) in zip(n,ofs,self.dims)])
#
#     # scalar index of basis function associated with node n + optional offset
#     def bindex(self, n, ofs=[0,0]):
#         return -1 if not self.in_grid(n,ofs) else (n[0]+ofs[0])*(self.dims[1]+1) + (n[1]+ofs[1])
#
#     ##############################################################
#     # on input, p[0,1] are the x,y coordinates of an evaluation
#     # point in the grid. The return value is a list of
#     # (bindex,bvalue) pairs giving the index and value of all
#     # basis functions supported at p.
#     ##############################################################
#     def contributors(self, p):
#         p            = p - self.center
#         pshift       = [ pp + 0.5*ll for pp,ll in zip(p,self.size) ]
#         node         = [ int(np.floor(pp/dd)) for pp,dd in zip(pshift,self.delta) ]
#         xi           = [ (pp-nn*dd)/(1.0*dd) for (pp,nn,dd) in zip(pshift,node,self.delta) ]
#         xisum, lower = xi[0]+xi[1], xi[0] <= (1.0-xi[1])
#         indices      = [self.bindex(node,ofs) for ofs in [(1,0), (0,1), (0,0) if lower else (1,1)]]
#         vals         = [xi[0], xi[1], 1.0-xisum] if lower else [1.0-xi[1],1.0-xi[0],xisum-1.0]
#         return [ (i,v) for i,v in zip(indices,vals) if i!= -1 ]
#
#     def get_bvector(self, p):
#         bvec = np.zeros(self.dim)
#         for idx, val in self.contributors(p):
#             bvec[idx]=val
#         return bvec
#
#     def gram_matrix(self, grid=None):
#         diag,off_diag=np.array([1.0/2.0,1.0/12.0]) * (self.delta[0]*self.delta[1])
#         gm = diag*np.identity(self.dim)
#         offsets=[(dx,dy) for dx in [-1,0,1] for dy in [-1,0,1] if dx!=dy ]
#         for (i,n) in enumerate([(nx,ny) for nx in range(0,self.dims[0]+1) for ny in range(0,self.dims[1]+1)]):
#             for j in [ self.bindex(n,ofs) for ofs in offsets if self.in_grid(n,ofs) ]:
#                 gm[i,j]=gm[j,i]=(diag if i==j else off_diag)
#         return gm
#
#     def inner_product(self,g,grid=None):
#         if grid is None:
#             grid=make_grid(self.size,center=self.center,dims=self.dims)
#         return super().inner_product(g,grid=grid)
#

"""Definition of the Basis abstract base class.

   A Basis is a finite-dimensional space of scalar functions defined on
   a finite spatial region (the *domain*).

**Instance Data**

   An instance of Basis is defined by the following data:
       (1) a domain V,
       (2) a set of D scalar basis functions {b_n(x)}, n=0,1,...,D-1, defined in V.

   Once item (2) is specified, individual elements f(x) in the space f(x) are
   identified by a D-dimensional vector of expansion coefficients
   {\beta_n} according to f(x) = \sum \beta_n b_n(x).

**Exported Methods**

   An instance of Basis exports methods implementing the following two operations:

       (1) *Projection*: Given an arbitrary scalar function g(x) on V,
           return the coefficients {g_n} of the element in the space
           lying closest to g(x).

       (2) *Function instance*: Given a set of expansion coefficients {beta_n}
           return a callable func that inputs a spatial variable x and
           outputs func(x) = \sum beta_n b_n(x).

**Exported Methods**
"""

from numbers import Number
import sys
from sympy import lambdify, Symbol
import re
import numpy as np
import meep as mp

from . import v3, V3, Subregion

class GridFunc(object):
    """Given a grid of spatial points {x_n} and a scalar function of a
       single spatial variable f(x) (whose specification may take any
       of several possible forms), return a scalar function of a
       single integer GridFunc(n) defined by GridFunc(n) == f(x_n).

    Args:
        f:    specification of function f(x)
        grid: grid of points {x_n} for integers n=0,1,...,

    Return value:
        GridFunc (callable) satisfying GridFunc(n)==f(x_n).
    """
#######################################################################

    def __init__(self,f,grid):
        self.p=grid.points
        self.fm=self.fv=self.ff=None
        if isinstance(f,np.ndarray) and f.shape==grid.shape:
            self.fm = f.flatten()
        elif isinstance(f,Number):
            self.fv = f
        elif callable(f):
            self.ff = lambda n: f(self.p[n])
        elif isinstance(f,str):
            ffunc=lambdify( [Symbol(v) for v in 'xyz'],f)
            self.ff = lambda n:ffunc(self.p[n][0],self.p[n][1],self.p[n][2])
        else:
            raise ValueError("GridFunc: failed to construct function")

    def __call__(self, n):
        return self.fm[n] if self.fm is not None else self.fv if self.fv is not None else self.ff(n)


######################################################################
# invoke python's 'abstract base class' formalism in a version-agnostic way
######################################################################
from abc import ABCMeta, abstractmethod
ABC = ABCMeta('ABC', (object,), {'__slots__': ()}) # compatible with Python 2 and 3

#----------------------------------------------------------------------
#----------------------------------------------------------------------
# Basis is the abstract base class from which classes describing specific
# basis sets should inherit.
#----------------------------------------------------------------------
#----------------------------------------------------------------------
class Basis(ABC):
    """
    Abstract base class to be subclassed by specific implementations.

    **Overview**

    This class abstracts the notion of a space of scalar functions f(x),
    defined for points x throughout some fixed region of space, with
    functions in the space parameterized by a finite-dimensional vector
    of real-valued coefficients.

    **The data of a Basis**

    A Basis is specified by the following data:
        1. The domain: A subregion :math:`Gamma` of a 2D or 3D computational cell,
           which may or may not be rectangular
        2. A fixed set of real-valued scalar functions $b_n(x)$ defined for x in \Gamma
        3. A real-valued constant *offset* f_0.

    Then a general function in the space takes the form
    :math:`f(x) = f_0 + \sum \beta_n b_n(x)`

    (The constant offset $f_0$ is of course not strictly necessary, but is
    convenient when describing spatially-varying lossless dielectric functions:
    defining $\epsilon(x)\equiv 1 + \sum\beta_n b_n(x)$, the physicality
    constraint on $\epsilon$ corresponds to the condition that the parameterized
    part $\sum \beta_n b_n(x)$ be everywhere nonnegative. If the basis functions
    $b_n(x)$ are themselves nonnegative, the condition becomes simply
    $$\beta_n \ge 0, \forall n$$
    which is easy to impose in numerical-optimization algorithms.)

    **Core functionality**

    For the purposes of the MEEP adjoint module, the two essential mathematical
    operations provided by a Basis are:

        1. parameterized function: Given a vector of expansion coefficients {beta_n},
           construct and return a callable scalar function of a single spatial variable,
           f(p)==\sum beta_n b_n(p).

        2. projection: Given an arbitrary scalar function g(p) defined on \Gamma,
           compute the expansion coefficients {g_n} of the projection
           g^{(proj)}(p) = \sum g^{(proj)}_n b_n(p), i.e. the element in the function space
           that most closely approximates g(p).

        These two functional procedures are exported in the form of the
        `parameterized_function` and `project` methods of `Basis.`

    ** Pure virtual methods and class-method overrides **

    Although the `Basis` parent class is an *abstract* base class, in fact it has only
    one pure-virtual method: `get_bvector(x),` which returns the full vector of
    basis-function values at a given point $x\in \Gamma$. For all other methods,
    including `project`, the `Basis` parent class provides default implementations
    that access the details of specific bases only via calls to `get_bvector`.
    Needless to say, these default implementations are not optimized for
    performance, but their existence makes it easy to experiment with custom-designed
    function spaces---for quick-and-dirty testing of a new basis, you need only
    implement a subclass with the single overridden routine `get_bvector`, relying
    on the default implementations of all other methods.
    Of course, once you have determined that your new basis is useful, you will
    want to implement performance-optimized versions of `project` and other
    routines that exploit the particular structure of your basis for maximum
    efficiency.

    **Default implementations of class methods**

    Given an arbitrary function $g(x)$, the default implementation of `project`
    computes the projection cofficients $\{g_n^{proj}\}$ by solving the linear system
    $$ \sum M_{mn} g^{(proj)}_n = g_m$$
    or
    $$ \mathbf{M} \mathbf{g}^{(proj)} = \mathbf g$$
    $\mathbf{M}$ is the Gram matrix of basis-function inner products
    and the RHS vector $\mathbf{g}$ describes inner products of $g(\mathbf{x})$
    with the basis set:
    $$ M_{mn}=\int_{\Gamma} b_m(\mathbf{x}) b_n(\mathbf{x}) d\mathbf{x},
       \qquad
       g_{m}=\int_{\Gamma} b_m(\mathbf{x}) g(\mathbf{x}) d\mathbf{x}....
    $$
    In the default implementations, the integrals here are evaluated by numerical
    cubature, i.e.
    $$ \int_\Gamma \psi(\mathbf{x})d\mathbf{x} \approx \sum_p w_p \psi(\mathbf{x}_p)$$
    where $\{\mathbf{x}_p, w_p\}$ are the points and weights of a caller-provided
    cubature rule for approximating integrals over $\Gamma.$
    (If $\Gamma$ is a rectangular 2D or 3D subregion of a MEEP geometry,
     the points and weights in the cubature rule are just the data returned by
     `mp.sim.get_array_metadata()`.)
    The evaluation of these numerical cubatures is the task of the base-class
    helper methods `gram_matrix` and `inner_product`. If your basis
    has special structure that allows efficient calculation of these integrals,
    you may provide

    However, as noted above, in fact the only class methods needed for MEEP adjoint
    calculations are `parameterized_function()` and `project().` If you can
    furnish efficient overriding implementations of these routines directly
    then you need not bother overriding `gram_matrix` or `inner_product`. For
    an example of such a situation, see the implementation of `FiniteElementBasis.
    """


    def __init__(self, dim, region=None, size=None, center=v3(), offset=0.0):
        self.dim, self.offset = dim, offset
        self.region = region if region else Subregion(center=center,size=size)

    @property
    def dimension(self):
        return self.dim

    @property
    def domain(self):
        return self.region

    @property
    def names(self):
        return [ 'b{}'.format(n) for n in range(self.dim) ]

    ######################################################################
    # get full vector of basis-function values at a single evaluation point
    #  (pure virtual method, must be overriden by subclasses)
    ######################################################################
    @abstractmethod
    def get_bvector(self, p):
        raise NotImplementedError("derived class must implement get_bvector()")

    ######################################################################
    # basis expansion coefficients of an arbitrary function g
    ######################################################################
    def project(self,g,grid=None):
        rhs = self.inner_product(g,grid=grid)
        gm  = self.gram_matrix(grid=grid)
        return np.linalg.solve(gm,rhs)

    # ... and the function defined by those coefficients
    def projection(self,g,grid=None):
        coefficients = self.project(g,grid=grid)
        return self.parameterized_function(coefficients)

    ######################################################################
    ######################################################################
    ######################################################################
    def parameterized_function(self, beta_vector):
        """
        Construct and return a callable, updatable element of the function space.

        After the line
            func = basis.parameterized_function(beta_vector)
        we have:
        1. func is a callable scalar function of one spatial variable:
            func(p) = f_0 + \sum_n beta_n * b_n(p)
        2. func has a set_coefficients method for updating the expansion coefficients
            func.set_coefficients(new_beta_vector)
        """
        class _ParameterizedFunction(object):
            def __init__(self, basis, beta_vector):
                (self.f0, self.b, self.beta) = (basis.offset, basis.get_bvector, beta_vector)
            def set_coefficients(self, beta_vector):
                self.beta = beta_vector
            def __call__(self, p):
                return self.f0 + np.dot( self.beta, self.b(p) )

        return _ParameterizedFunction(self, beta_vector)

    #######################################################################
    # inner products of basis functions with an arbitrary function g
    ######################################################################
    def inner_product(self, g, grid=None):
        if grid is None:
            raise ValueError('Basis.inner_product: integration grid must be specified')
        gn, g_dot_b = GridFunc(g, grid), 0.0*gn(0)*np.zeros(self.dim)
        for n, (p,w) in enumerate(zip(grid.points,grid.weights)):
            g_dot_b += w * ( gn(n)-self.offset ) * self.get_bvector(p)
        return g_dot_b

    ##########################################################
    # basis_function overlap matrix, gm_{ij} = <b_i | b_j>.
    ##########################################################
    def gram_matrix(self,grid=None):
        def bxb(p):
            return np.outer(self.get_bvector(p),self.get_bvector(p))
        return np.sum([w*bxb(p) for p,w in zip(grid.points,grid.weights)], axis=0)

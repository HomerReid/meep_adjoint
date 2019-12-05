"""Handling of objective functions and objective quantities."""

import sys
import os
import re
from collections import namedtuple
from datetime import datetime as dt2
import sympy
import numpy as np

import meep as mp

QRule = namedtuple('QRule', 'code mode ncell')

from . import dft_cell_names


def make_qrule(qname):
    """
    Decode objective-quantity name to yield rule for computing it.

    A "qrule" is a recipe for computing a single objective quantity,
    comprised of three elements: a code string identifying the physical
    quantity (i.e. 'S' for poynting flux, 'UE' for electric-field energy,
    etc), the integer index of the DFTCell whose fields are used to
    compute the quantity, and an optional mode index for objective
    quantities that involve eigenmodes.

    qrules are constructed from the string names of
    objective variables like 'P2_3' or 'M1_north' or 's_0'.

    Parameters
    ----------
    qname : str
        Name of objective quantity

    Returns
    -------
    qrule : QRule
        Rule for computing the quantity.

    """
    tokens = re.sub(r'([A-Za-z]+)([\d]*)_([\w]+)', r'\1 \2 \3',qname).split()
    if len(tokens)==3:
        code, mode, cellstr = tokens
        mode = int(mode)
    elif len(tokens)==2:
        code, mode, cellstr = tokens[0], 0, tokens[1]
    else:
        raise ValueError('syntax error in quantity name ' + qname)
    if cellstr.isdigit():
        ncell = int(cellstr)
    elif cellstr + '_flux' in dft_cell_names:
        ncell = dft_cell_names.index(cellstr+'_flux')
    elif cellstr + '_fields' in dft_cell_names:
        ncell = dft_cell_names.index(cellstr+'_fields')
    else:
        ncell = -1
    if ncell < 0 or ncell > len(dft_cell_names):
        raise ValueError('quantity {}: non-existent DFT cell {}'.format(qname,cellstr))
    return QRule(code, mode, ncell)



# class ObjectiveQuantity(object):
#
#     def __init__(self, qname):
#         tokens = re.sub(r'([A-Za-z]+)([\d]*)_([\w]+)',r'\1 \2 \3',qname).split()
#         if len(tokens) not in [2,3]:
#             raise ValueError('quantity {}: syntax error{}'.format(qname))
#         self.code = tokens[0]
#         try:
#             self.mode = 0 if len(tokens)==2 else int(tokens[1])
#         except:
#             raise ValueError('quantity {}: invalid mode {}'.format(qname,tokens[1]))
#         self.cell = DFTCell.get_cell_by_name(tokens[-1])
#         if self.cell is None:
#             raise ValueError('quantity {}: non-existent DFT cell {}'.format(qname,tokens[-1]))
#
#
#     def __call__(self, nf=0):
#         return self.cell(self.code,mode=self.mode, nf=nf)

class ObjectiveFunction(object):
    """
    Multivariate scalar-valued function defined by string expression.

    An `ObjectiveFunction` is a scalar function
    :math:`f^{obj}({q_n})`
    of :math:`N` scalar variables :math:`\{ q_0, q_1, ..., q_{N-1}\}`,
    where the :math:`{q_n}` are complex-valued in general and
    :math:`f^{obj}` may be real- or complex-valued
    (only the real part is referenced for optimization purposes).

    An instance of `ObjectiveFunction` is specified by a
    character string (the `fstr` input to the constructor)
    that, upon parsing by `sympy.sympify`, is identified as
    a mathematical expression depending on :math:`N` unknown
    variables (which we call "objective quantities").
    The strings identified by `sympy` as the names of the
    variables should obey `meep_adjoint` naming conventions for
    objective quantities (in particular, they should
    be parsable by `make_qrule` to yield a valid `qrule`).


    Parameters
    ----------
        fstr : str
            Mathematical expression defining objective function.

        extra_quantities: list of str, optional
            Optional list of additional objective quantities to be computed
            and returned each time the objective function is evaluated.

    Class instances store the following data:

        :`fexpr` (`sympy` expression):

            `sympy` expression returned by `sympy.sympify(fstr)`

        :`qsyms` (list of `sympy.Symbol`):

            The variable (unknown) quantities on which the
            objective function depends, as identified by
            `sympy` upon parsing `fstr`.

        :`qnames` (list of `str`):

            names of objective quantities

        :`qrules` (list of `QRule`):

            rules specifying how the
            objective quantities are to be computed
            from FDTD data (specifically, from frequency-
            domain field data stored in DFTCells)

        :`qvals` (array-like):
            cache storing most recently computed values of objective quantities


        :`riqsyms`, `riqvals`:

            as qsyms and qvalues, but with each complex-valued
            'q' quantity split up into real-valued 'r' and 'i'
            components. We do this to facilitate symbolic
            differentiation of non-analytic functions of objective
            quantities such as :math:`|q_i|^2`---which, incidentally,
            would be written within `fstr` like this: 'Abs(q_i)**2'
    """
    def __init__(self, fstr='S_0', extra_quantities=[]):

        def _parse_absval_bars(s):
            """preprocess sympy input to replace '|...|' with 'Abs(...)' """
            return re.sub(r'[|]([^|]*)[|]',r'Abs(\1)',s)

        # try to parse the function string to yield a sympy expression
        try:
            fexpr = sympy.sympify( _parse_absval_bars(fstr) )
        except:
            raise ValueError("failed to parse function {}".format(fstr))

        # qnames = names of all objective quantities (i.e. all symbols
        #          identified by sympy as quantities on which fexpr depends)
        self.qnames = sorted(list(set([str(s) for s in fexpr.free_symbols] + extra_quantities ) ))
        self.qsyms  = [ sympy.Symbol(q) for q in self.qnames ]

        # qrules = computation rules for all objective quantities
        self.qrules = [ make_qrule(qn) for qn in self.qnames ]

        # qvals = cached values of objective quantities
        self.qvals = 0.0j*np.zeros(len(self.qnames))

        # for each (generally complex-valued) objective quantity,
        # we now introduce two real-valued symbols for the real and
        # imaginary parts, stored in riqsymbols. q2ri is a dict of
        # sympy substitutions q -> qr + I*qi that we use below to
        # recast fexpr as a function of the ri quantities. riqvals
        # is a dict of numerical values of the ri quantities used
        # later to evaluate f and its partial derivatives.
        self.riqsymbols, self.riqvals, q2ri = [], {}, {}
        for nq,(qn,qs) in enumerate(zip(self.qnames,self.qsyms)):
            rqn, iqn = 'r'+qn, 'i'+qn
            rqs, iqs = sympy.symbols( [rqn, iqn], real=True)
            q2ri[qs] = rqs + iqs*sympy.I
            self.riqvals[rqn] = self.riqvals[iqn]=0.0
            self.riqsymbols += [rqs, iqs]

        self.fexpr = fexpr.subs(q2ri)

        # expressions for partial derivatives, dfexpr[q] = \partial f / \partial q_n
        self.dfexpr=[]
        for nq in range(len(self.qnames)):
            df_drqn = sympy.diff(self.fexpr,self.riqsymbols[2*nq+0])
            df_diqn = sympy.diff(self.fexpr,self.riqsymbols[2*nq+1])
            self.dfexpr.append( df_drqn - sympy.I*df_diqn )


    def __call__(self, DFTCells, nf=0):
        """Compute objective quantities and objective function.

        Uses the given list of DFTCells to determine numerical
        values for all objective quantities :math:`q_n`, then
        uses these to evaluate the objective function :math:`f`.

        Parameters
        ----------
        DFTCells : list of :class:`dft_cell <meep_adjoint.dft_cell>`
            List that should contain at least all DFT cells for which
            objective quantities are defined.
        nf : int, optional
             Frequency index, by default 0

        Returns
        -------
        Array-like
            Array containing objective-function value followed by
            values of all objective quantities:[ f q0 q1 ...q_{N-1} ]
        """

        # fetch updated values for all objective quantities
        for nq, qr in enumerate(self.qrules):
            self.qvals[nq] = DFTCells[qr.ncell](qr.code,qr.mode,nf)
            self.riqvals[self.riqsymbols[2*nq+0]]=np.real(self.qvals[nq])
            self.riqvals[self.riqsymbols[2*nq+1]]=np.imag(self.qvals[nq])

        # plug in objective-quantity values to get value of objective function
        fval=self.fexpr.evalf(subs=self.riqvals)
        fval=complex(fval) if fval.is_complex else float(fval)

        return np.array( [np.real(fval)] + list(self.qvals) )


    def get_dfdq(self):
        """Compute first partial derivatives of objective function.

        Compute the partial derivatives :math:`\partial f / \partial q_n`
        using values of :math:`\{q_n\}` cached on most recent invocation
        of `__call__` (which must have been invoked at least once before
        this function can be called).

        Returns
        -------
        array-like
            Array whose *n*th entry is :math:`\partial f/\partial q_n`.
        """
        return np.array( [ df.evalf(subs=self.riqvals) for df in self.dfexpr ] )

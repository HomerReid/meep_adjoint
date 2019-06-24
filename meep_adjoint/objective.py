"""handling of objective functions and objective quantitieshj
"""

import sys
import os
import re
from collections import namedtuple
from datetime import datetime as dt2
import sympy
import numpy as np

import meep as mp


QRule = namedtuple('QRule', 'code mode ncell')


def make_qrule(qname):
    """Decode objective-quantity name to yield rule for computing it.

       A 'qrule' is a recipe for computing a single objective quantity,
       comprised of three elements: a code string identifying the physical
       quantity (i.e. 'S' for poynting flux, 'UE' for electric-field energy,
       etc), the integer index of the DFTCell whose fields are used to
       compute the quantity, and an optional mode index for objective
       quantities that involve eigenmodes.

       qrules are constructed from the string names of
       objective variables like 'P2_3' or 'M1_north' or 's_0'.

    """
    from meep.adjoint import dft_cell_names
    tokens = re.sub(r'([A-Za-z]+)([\d]*)_([\w]+)',r'\1 \2 \3',qname).split()
    if len(tokens)==3:
        code, mode, cellstr = tokens
        mode = int(mode)
    elif len(tokens)==2:
        code, mode, cellstr = tokens[0], 0, tokens[1]
    else:
        raise ValueError('syntax error in quantity name ' + qname)
    if cellstr.isdigit():
        ncell = int(cellstr)
    elif cellstr+'_flux' in dft_cell_names:
        ncell = dft_cell_names.index(cellstr+'_flux')
    elif cellstr+'_fields' in dft_cell_names:
        ncell = dft_cell_names.index(cellstr+'_fields')
    else:
        ncell = -1
    if ncell < 0 or ncell > len(dft_cell_names):
        raise ValueError('quantity {}: non-existent DFT cell {}'.format(qname,cellstr))
    return QRule(code, mode, ncell)



class ObjectiveFunction(object):
    """Multivariate scalar-valued function defined by string expression.

        An ObjectiveFunction is a scalar function :math:`f({q_n})`
        of :math:`N` scalar variables :math:`\{ q_0, q_1, ..., q_{N-1}\}`,
        where the :math:`{q_n}` are complex-valued in general and
        f may be real- or complex-valued.

        An instance of ObjectiveFunction is specified by a
        character string (the fstr input to the constructor)
        that, upon parsing by sympy.sympify, is identified as
        a mathematical expression depending on :math:`N` unknown
        variables (which we call "objective quantities").
        The strings identified by numpy as the names of the variables
        should obey meep_adjoint syntax rules for the naming
        of objective quantities (in particular, they should
        be parsable by `make_qrule` to yield a valid qrule).

        Class instances store the following data:

        fexpr: sympy expression constructed from fstr

        qsyms: list of sympy.Symbols identified by sympy
               as the objective quantities, i.e. the inputs
               on which f depends

        qnames: list of strs giving the names of the objective
                quantitiesrs giving the names of the objective

        qrules: list of 'qrule' objects specifying how the
                objective quantities are to be computed
                from MEEP data (specifically, from frequency-
                domain field data stored in DFTCells)

        qvals: numpy array storing most recent updates of
               objective-quantity values

        riqsyms, riqvals: the same data content as
              qsyms and qvalues, but with each complex-valued
              'q' quantity split up into real-valued 'r' and 'i'
              components. We do this to facilitate symbolic
              differentiation of non-analytic functions
              of the objective quantities such as :math:`|q_i|^2`
              ---which, incidentally, would be written within fstr
                like this: 'Abs(q_i)**2'
    """

    def __init__(self, fstr='S_0', extra_quantities=[]):
        """
        Try to create a sympy expression from the given string and determine
        names for all input variables (objective quantities) needed to
        evaluate it.
        """

        # try to parse the function string to yield a sympy expression
        try:
            fexpr = sympy.sympify(fstr)
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
        """Compute objective quantities and the objective function.
           Uses the given list of DFTCells to determine numerical
           values for all objective quantities :math:`q_n`, then
           uses these to evaluate the objective function :math:`f`.
           The return value is an array of length (N+1), whose entries
           are [ f q0 q1 ...q_{N-1} ]
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
        """return vector of partial derivatives \partial f / \partial q
           using the values of the {q_n} that were cached on the
           most recent invokation of __call__
        """
        return np.array( [ df.evalf(subs=self.riqvals) for df in self.dfexpr ] )

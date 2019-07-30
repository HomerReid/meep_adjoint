""" TimeStepper.py: MEEP timestepping for forward and adjoint runs

  TimeStepper is a class that knows how to run a time-domain MEEP
  calculation to accumulate frequency-domain (DFT) field components
  in objective regions, from which may be computed the values of
  objective quantities, from which may be computed the objective
  function.

  TimeStepper monitors the convergence of DFT components and
  the associated objective quantities, and continues timestepping
  until the relevant output quantities have stopped changing.

  More specifically, it knows about two different types of
  timestepping runs: (1) forward runs, in which the sources are
  pre-specified by the caller and the outputs are objective
  quantities and the objective function, and (2) adjoint runs,
  for which TimeStepper itself determines the source
  distribution (see place_adjoint_sources below) and the
  output is the gradient df/dEps (more specifically, its
  projection onto the design basis).
"""

from enum import Enum

import numpy as np
import meep as mp

from datetime import datetime as dt2

from . import (ObjectiveFunction, Basis, v3, V3, E_CPTS)
from . import get_adjoint_option as adj_opt

class TimeStepper(object):

    #########################################################
    #########################################################
    #########################################################
    def __init__(self, obj_func, dft_cells, basis, sim, fwd_sources):
        """
        Args:
            obj_func  (ObjectiveFunction)
            dft_cells (list of DFTCell)
            basis     (subclass of Basis)
            sim       (mp.Simulation object)
            fwd_sources (list of mp.Source or mp.EigenModeSource):
        """

        self.obj_func    = obj_func
        self.dft_cells   = dft_cells
        self.design_cell = dft_cells[-1]
        self.basis       = basis
        self.sim         = sim
        self.fwd_sources = fwd_sources
        self.dfdEps      = None
        self.state       = 'reset'


    def __update__(self, job):
        """Recompute output quantities using most recent values
           of frequency-domain fields.
           This is an internal helper method for run() that computes
           the objective function value (forward run) or gradient (adjoint run)
           using the latest values of the frequency-domain fields
           stored in the DFT cells. During timestepping it is called
           every check_interval units of MEEP time once the excitation
           sources have died down.
           Args:
               job = 'forward' or 'adjoint'
           Return values:
               If job=='forward':
                   numpy array of length N+1 storing values of the objective
                   function and the N objective quantities [F, Q0, Q1, ... QN]
                   as returned by ObjectiveFunction.__call__
               If job=='adjoint':
                   numpy array of length basis.dim storing components of
                   the objective-function gradient
        """
        if job=='forward':
            retvals = self.obj_func(self.dft_cells)
            log('   ** {:10s}={:.5f}  ** '.format('t',self.sim.round_time()))
            for n,v in zip(['f'] + self.obj_func.qnames, retvals):
                log('   ** {:10s}={:+.5e}    '.format(n,v))
        else: # job=='adjoint'
            EH_fwd = self.design_cell.get_EH_slices(label='forward')
            EH_adj = self.design_cell.get_EH_slices()
            self.dfdEps = np.zeros(self.design_cell.grid.shape)
            for n in [ n for (n,c) in enumerate(self.design_cell.components) if c in E_CPTS]:
                self.dfdEps += np.real( EH_fwd[n]*EH_adj[n] )
            retvals = self.basis.project(self.dfdEps, grid=self.design_cell.grid)
        return retvals


    #########################################################
    # main timestepper routine that keeps going until the
    # relevant output quantity has converged
    #########################################################
    def run(self, job):
        """Execute the full MEEP timestepping run for a forward
           or adjoint calculation and return the results.
        """

        self.prepare(job)

        last_source_time = self.fwd_sources[0].src.swigobj.last_time()
        max_time         = adj_opt('dft_timeout')*last_source_time
        check_interval   = adj_opt('dft_interval')*last_source_time
        reltol           = adj_opt('dft_reltol')

        # configure real-time animations of evolving time-domain fields
        step_funcs = []
#        clist = adjoint_adj_opt('animate_components')
#        if clist is not None:
#            ivl=adjoint_adj_opt('animate_interval')
#            ivl=0.5
#            step_funcs = [ AFEClient(self.sim, clist, interval=ivl) ]

        # start by timestepping without interruption until the sources are extinguished
        log("Beginning {} timestepping run...".format(job))
        self.sim.run(*step_funcs, until=last_source_time)
        vals = self.__update__(job)

        # now continue timestepping with intermittent convergence checks until
        # we converge or timeout
        max_rel_delta = 1.0e9;
        while max_rel_delta>reltol and self.sim.round_time() < max_time:
            check_time = self.sim.round_time() + check_interval
            self.sim.run(*step_funcs, until = min(check_time, max_time))
            last_vals, vals = vals, self.__update__(job)
            rel_delta = np.array( [rel_diff(v,lv) for v,lv in zip(vals,last_vals)] )
            max_rel_delta = np.amax(rel_delta)
            log('   ** t={} MRD={} ** '.format(self.sim.round_time(), max_rel_delta))

        # for forward runs we save the converged DFT fields for later use
        if job=='forward':
            [ cell.save_fields('forward') for cell in self.dft_cells ]
        self.state = job + '.complete'
        return vals


    ##############################################################
    ##############################################################
    ##############################################################
    def prepare(self, job='forward'):
        """Prepare simulation for timestepping by adding sources and DFT cells.

        Parameters:
          job (str): The type of timestepping run to prepare:
             1. If job=='forward', prepare forward run to compute objective function value.
             2. If job=='adjoint', prepare adjoint run to compute objective function gradient.
             3. If job is the name of an objective quantity, prepare adjoint run to compute
                the gradient of that quantity.

        Return value: None
        """
        target_state = job + '.prepared'
        if self.state == target_state: return

        # get lists of sources and DFT cells to register
        if job=='forward':
            sources = self.fwd_sources
            cells   = self.dft_cells  # all cells needed for forward calculations
            cmplx   = adj_opt('complex_fields')
        elif job=='adjoint' or job in self.obj_func.qnames:
            sources = self.get_adjoint_sources ( qname = job )
            cells   = [self.design_cell]  # only design cell needed for adjoint calculations
            cmplx   = True
        else:
            raise ValueError('unknown job {} in TimeStepper.prepare'.format(job))

        # place sources, register cells, initialize fields
        self.sim.reset_meep()
        self.sim.change_sources(sources)
        self.force_complex_fields = cmplx
        self.sim.init_sim()
        for cell in cells:
            cell.register(self.sim)
        self.state = target_state


    ##############################################################
    ##############################################################
    ##############################################################
    def get_adjoint_sources(self, qname=None):
        """
        Return a list of mp.Source structures describing the distribution of sources
        appropriate for adjoint-method evaluation of the objective-function gradient
        df/deps.

        The optional parameter qname may be set to the name of an objective quantity Q,
        in which case we instead compute dQ/deps.
        """
        ######################################################################
        # extract the temporal envelope of the forward sources and use it to
        # set the overall amplitude prefactor for the adjoint sources
        ######################################################################
        envelope = self.fwd_sources[0].src
        freq     = envelope.frequency
        omega    = 2.0*np.pi*freq
        factor   = 2.0j*omega
        if callable(getattr(envelope, "fourier_transform", None)):
            factor /= envelope.fourier_transform(freq)

        ######################################################################
        # make a list of (qrule, qweight) pairs for all objective quantities
        # that contribute with nonzero weight to the derivative in question
        ######################################################################
        if qname is None or qname=='adjoint':
            dfdq   = self.obj_func.get_dfdq()
            iwlist = [ (i,w) for i,w in enumerate(dfdq) if w is not 0.0 ]
        elif qname in self.obj_func.qnames:
            iwlist = [ (self.obj_func.qnames.index(qname), 1.0) ]
        else:
            warnings.warn('unknown objective quantity {} in get_adjoint_sources (skipping)'.format(qname))
            return []
        rwlist = [ (self.obj_func.qrules[i], w) for (i,w) in iwlist ]

        ######################################################################
        # loop over all contributing objective quantities
        ######################################################################
        sources = []
        for (qrule, qweight) in rwlist:
            code, mode, cell = qrule.code, qrule.mode, self.dft_cells[qrule.ncell]
            EH = cell.get_eigenmode_slices(mode) if mode>0 else cell.get_EH_slices('forward')
            shape = [ len(tics) for tics in [cell.grid.xtics, cell.grid.ytics, cell.grid.ztics] ]

            if code in 'PM':
                sign  =  1.0 if code=='P' else -1.0
                signs = [ +1.0, -1.0, +1.0*sign, -1.0*sign ]
                sources += [ mp.Source(envelope, cell.components[3-nc],
                                       V3(cell.region.center), V3(cell.region.size),
                                       amplitude=signs[nc]*factor*qweight,
                                       amp_data=np.reshape(np.conj(EH[nc]),shape)
                                      ) for nc in range(len(cell.components))
                           ]
        return sources




def rel_diff(a,b):
    """ returns value in range [0,2] quantifying error relative to magnitude"""
    diff, scale = np.abs(a-b), np.amax([np.abs(a),np.abs(b)])
    return 2. if np.isinf(scale) else 0. if scale==0. else diff/scale


######################################################################
######################################################################
######################################################################
def log(msg):
    if not mp.am_master() or np.all([adj_opt(s) is None for s in ['filebase','logfile']]):
        return
    logfile = adj_opt('logfile') or (adj_opt('filebase') + '.log' )
    with open(logfile,'a') as f:
        f.write("{} {}\n".format(dt2.now().strftime('%T '),msg))

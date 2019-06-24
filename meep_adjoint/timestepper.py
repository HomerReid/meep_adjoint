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
  in which we place the sources ourselves (see
  place_adjoint_sources below) and the output is the gradient
  df/dEps (more specifically, its projection onto the design basis).
"""

import numpy as np
import meep as mp

from . import (ObjectiveFunction, Basis, log, v3, V3, E_CPTS)

class TimeStepper(object):

    #########################################################
    #########################################################
    #########################################################
    def __init__(self, obj_func, dft_cells, basis, eps_func, set_coefficients,
                       sim, fwd_sources):
        """
        Args:
            obj_func  (ObjectiveFunction)
            dft_cells (list of DFTCell)
            basis     (subclass of Basis)
            eps_func  (
            sim       (mp.Simulation object)
            fwd_sources (list of mp.Source or mp.EigenModeSource):
        """

        self.obj_func    = obj_func
        self.dft_cells   = dft_cells
        self.design_cell = dft_cells[-1]
        self.basis       = basis
        self.eps_func    = eps_func
        self.set_coefficients = set_coefficients
        self.sim         = sim
        self.fwd_sources = fwd_sources
        self.dfdEps      = None


    def __update__(self, job):
        """
        internal helper method for step_until_converged that (re)computes the
        objective function value (forward run) or gradient (adjoint run)
        using the latest values of the frequency-domain fields, and also updates
        visualization plots if necessary. during timestepping this routine is
        called every check_interval units of meep time.
        """
        if job=='forward':
            retvals = self.obj_func(self.dft_cells)
            log('   ** {:10s}={:.5f}  ** '.format('t',self.sim.round_time()))
            for n,v in zip(['f'] + self.obj_func.qnames, retvals):
                log('   ** {:10s}={:+.5e}    '.format(n,v))
        else: # job=='adjoint'
            EH_fwd = self.design_cell.get_EH_slices(label='forward')
            EH_adj = self.design_cell.get_EH_slices()
            ncs = [n for (n,c) in enumerate(self.design_cell.components) if c in E_CPTS]
            self.dfdEps = np.real(np.sum( [ EH_fwd[nc]*EH_adj[nc] for nc in ncs ] ) )
            retvals = self.basis.project(self.dfdEps, grid=self.design_cell.grid)
#        if self.visualizer:
#            self.visualizer.update(self.sim,job,self.dfdEps)
        return retvals


    #########################################################
    # main timestepper routine that keeps going until the
    # relevant output quantity has converged
    #########################################################
    def step_until_converged(self, job):

        """Execute a MEEP timestepping run to compute frequency-domain fields and quantities."""

        from meep.adjoint import options
        last_source_time = self.fwd_sources[0].src.swigobj.last_time()
        max_time         = options['dft_timeout']*last_source_time
        check_interval   = options['dft_interval']*last_source_time
        reltol           = options['dft_reltol']

        # configure real-time animations of evolving time-domain fields
        step_funcs = []
#        clist = adjoint_options['animate_components']
#        if clist is not None:
#            ivl=adjoint_options['animate_interval']
#            ivl=0.5
#            step_funcs = [ AFEClient(self.sim, clist, interval=ivl) ]

        # start by timestepping without interruption until the sources are extinguished
        log("Beginning {} timestepping run...".format(job))
        self.sim.run(*step_funcs, until=last_source_time)
        last_vals = self.__update__(job)

        # now continue timestepping with intermittent convergence checks until
        # we converge or timeout
        while True:
            until = self.sim.round_time() + check_interval
            self.sim.run(*step_funcs, until = min(until, max_time))
            vals = self.__update__(job)
            rel_delta = np.array( [rel_diff(v,lv) for v,lv in zip(vals,last_vals)] )
            max_rel_delta, last_vals  = np.amax(rel_delta), vals
            log('   ** t={} MRD={} ** '.format(self.sim.round_time(), max_rel_delta))
            if max_rel_delta<reltol or self.sim.round_time()>=max_time:
                return vals


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


    def prepare(self, job='forward', beta_vector=None):
        """Prepare the simulation for a timestepping run.

        (a) If new design-variable values were given, update the design permittivity.
        (b) Add sources and DFT cells as appropriate for the type of run requested.
        (c) Update geometry visualization as necessary.

        Parameters:
          job (str): The type of timestepping run to prepare:
             1. If job=='forward', prepare forward run to compute objective function value.
             2. If job=='adjoint', prepare adjoint run to compute objective function gradient.
             3. If job is the name of an objective quantity, prepare adjoint run to compute
                the gradient of that quantity.

          beta_vector (np.array): new design variables or 'None' to leave design unchanged

        Return value: None
        """
        from meep.adjoint import options
        # update design permittivity as necessary
        if beta_vector is not None:
#            self.eps_func.set_coefficients(beta_vector)
            self.set_coefficients(beta_vector)

        # get lists of sources and DFT cells to register
        if job=='forward':
            sources = self.fwd_sources
            cells   = self.dft_cells  # all cells needed for forward calculations
            cmplx   = options['complex_fields']
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

        # update visualization
#        if self.visualizer and beta_vector is not None:
#            self.visualizer.update(self.sim, 'geometry')


    def run(self, job='forward', beta_vector=None):
        self.prepare(job, beta_vector=beta_vector)
        retval=self.step_until_converged(job)
        if job=='forward':
            [ cell.save_fields('forward') for cell in self.dft_cells ]
        return retval



def rel_diff(a,b):
    """ returns value in range [0,2] quantifying error relative to magnitude"""
    diff, scale = np.abs(a-b), np.amax([np.abs(a),np.abs(b)])
    return 2. if np.isinf(scale) else 0. if scale==0. else diff/scale

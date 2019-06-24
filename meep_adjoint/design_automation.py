    ######################################################################
    # an OptState stores the current state of an optimization problem.
    ######################################################################
    OptState = namedtuple('OptState', 'n alpha beta fq gradf dfdEps')

    ######################################################################
    # write a status update ##############################################
    ######################################################################
    def log_state(self, state, sub_state=None):

        ts=dt2.now().strftime('%T')
        with open(self.iterfile,'a') as iterfile:
            for f in [self.stdout, iterfile]:
                if sub_state:     # minor iteration
                    f.write('{}:  Subiter {:5d}.{:5d}: '.format(ts,state.n,sub_state.n))
                    f.write('f={:+.12e}, alpha={:8f}\n'.format(sub_state.fq[0],sub_state.alpha))
                else:   #  major iteration
                    self.annals.append(state)
                    dfdEps_avg=np.sum(self.design_cell.grid.weights * state.dfdEps.flatten())
                    msg='\n\n{}: Iter {:5d}: f={:+.12e}   alpha={:.8f}   avg(dfdEps)={:+.8e}\n'
                    f.write(msg.format(ts,state.n,state.fq[0],state.alpha,np.real(dfdEps_avg)))
                    if f==iterfile:
                        np.savez('iter{}.npz'.format(state.n),state.beta,state.dfdEps)
                        [f.write('  #{:5d} {} = {:+.12e}\n'.format(state.n,nn,qq)) for nn,qq in zip(self.obj_func.qnames[1:], state.fq[1:]) ]
                    f.write('\n\n')
                    f.flush()


    ######################################################################
    ######################################################################
    ######################################################################
    def line_search(self,state):

        self.log_state(state)
        beta, dbeta = state.beta, self.basis.project(np.real(state.dfdEps))
        alpha, iter, subiter = state.alpha, state.n, 0
        while alpha>self.args.min_alpha:

            beta  = [ max(0.0, b + alpha*db) for b,db in zip(state.beta, dbeta) ]
            fq, _ = self.eval_objective(beta, need_gradient=False)

            sub_state = self.OptState(subiter, alpha, beta, fq, 0, 0)
            self.log_state(state,sub_state)

            if fq[0] > state.fq[0]:    # found a new optimum, declare victory and a new iteration
                gradf = self.stepper.adjoint_run()
                alpha = min(alpha*self.args.boldness,self.args.max_alpha)
                return self.OptState(iter+1, alpha, beta, fq, gradf, self.stepper.dfdEps)

            cease_file = '/tmp/terminate.{}'.format(os.getpid())
            if os.path.isfile(cease_file):  # premature termination requested by user
                os.remove(cease_file)
                return None

            alpha*=self.args.timidity

        return None   # unable to improve objective by proceeding any distance in given direction

    ######################################################################
    ######################################################################
    ######################################################################
    def optimize(self):

        ss = int( dt2.now().strftime("%s") ) - 1556107700
        self.iterfile = '{}.{}.iters'.format(self.filebase,ss)
        with open(self.iterfile,'w') as f:
            f.write('#{} ran'.format(self.__class__.__name__))
            f.write(dt2.now().strftime(' %D::%T\n'))
            f.write('# with args {}\n\n'.format(self.cmdline))
        self.annals=[]

        ######################################################################
        # initialize TimeStepper and get objective function value and gradient
        # at the initial design point
        ######################################################################
        alpha     = self.args.alpha
        beta      = self.beta_vector
        fq, gradf = self.eval_objective(beta, need_gradient=True)
        dfdEps    = self.stepper.dfdEps
        state     = self.OptState(1, alpha, beta, fq, gradf, dfdEps)

        ######################################################################
        # main iteration
        ######################################################################
        while state and state.n<self.args.max_iters:
            state = self.line_search(state)

        return self.annals


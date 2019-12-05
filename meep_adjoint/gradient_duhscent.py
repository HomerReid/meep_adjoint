"""Bare-bones gradient-descent optimizer.
"""
import os
from os.path import isfile
import numpy as np
from numpy import clip, amax


_DEFAULTS = { 'alpha_min': 1.0e-3,
              'alpha_max': 10.0,
                   'xmin': 0.0,
                   'xmax': None,
               'timidity': 0.75,
               'boldness': 1.25,
                   'hook': None,
              'max_iters': 100,
               'stopfile': 'gradient_duhscent.stopfile'
            }


def line_search(f_func, x0, f0, alpha, dir, options={}):
    """one-dimensional line search

    Given the coordinates of a D-dimensional point x0 and a D-dimensional
    vector dir, we attempt to find a value of the (scalar) quantity alpha
    such that f(x0 + alpha*dir) > f(x0). We return as soon as we find such
    a point.

    Parameters
    ----------
    f_func: callable
        python function that inputs x (a D-dimensional array of coordinates)
        and returns a real-valued scalar f(x)

    x0: array-like
        coordinates of starting point

    f0: float
        function value at starting point, f(x0)

    alpha: type
        initial value of relaxation parameter alpha

    dir: array-like
        array of vector components defining search direction
        (not assumed to be normalized to 1 or anything else)

    options: dict
        optional overrides of default option values.


    Returns
    -------
    a four-tuple (x, f, alpha, status), where
        x (array-like): final point
        f (float)     : f(x)
        alpha (float) : updated value of relaxation parameter
        result (str)  : string description of the result of the line search,
                        as follows:

                           'success': successfully found a better point on the line

                        the remaining possibilities indicate premature termination
                        without a successful conclusion to the line search
                           'alpha':   alpha shrunk to its minimum allowed value
                           'iters':   maximum number of iterations reached
                           'user':    user requested that we terminate the
                                      iteration early


    """
    opts = { k:options.get(k,v) for k,v in _DEFAULTS.items() }
    for iters in range(1, 1 + opts['max_iters']):

        # move a distance alpha along the line from x0
        x = clip(x0 + alpha*dir, opts['xmin'], opts['xmax'])
        f = f_func(x)
        if opts['hook']:
            opts['hook']('minor',x,f,alpha,iters)

        # assess termination criteria
        result =      'success' if f>f0                         \
                 else 'alpha'   if alpha <= opts['min_alpha']   \
                 else 'iters'   if iters == opts['max_iters']   \
                 else 'user'    if isfile(opts['stopfile'])     \
                 else None
        if result:
            # if the line search terminated on the first iteration,
            # alpha was perhaps too small, so pump it up for next time
            alpha = (alpha*opts['boldness'] if iters==1 else alpha)
            return x, f, alpha, result

        # alpha was too big; reduce for next iteration
        alpha = amax(alpha*opts['timidity'], opts['min_alpha'])


######################################################################
######################################################################
######################################################################
def gradient_duhscent(f_func, df_func, x0, options={}):
    """simple gradient-descent optimizer

    Parameters
    ----------
    f_func: callable
        function that computes objective function value
        inputs x (D-dimensional coordinate array) and outputs f(x) (real scalar float)

    df_func: callable
        function that computes objective function gradient
        inputs x (D-dimensional coordinate array) and outputs df (D-dimensional vector)

    x0: array-like, dimension D
        initial point

    options: optional dict of overrides of default option values

    Returns
    -------
    4-tuple (x*, f*, df*, result), where
        x* (array-like):   coordinates of optimum point
        f* (scalar float): objective-function value at optimum
       df* (array-like):   objective-function gradient at optimum
       result (str):       reason why the iteration terminated:
                             'line_search': line search failed to improve our current
                                            best point
                             'iters':       we executed the maximum allowed number of iterations
    """
    opts = { k:options.get(k, v) for k,v in _DEFAULTS.items() }
    x, alpha = x0, opts['alpha0']
    for iters in range(0, opts['max_iters']):
        f, df = f_func(x), df_func(x)
        x, f, alpha, status = line_search(f_func, x, f, alpha, df, options=options)
        if status is not 'success':
            break
    return x, f, df

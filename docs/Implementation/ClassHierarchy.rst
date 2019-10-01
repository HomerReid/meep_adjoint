.. include:: /Preamble.rst

********************************************************************************
Overview of the :mod:`meep_adjoint` class hierarchy
********************************************************************************

As noted in the :doc:tutorial,
The :class:`OptimizationProblem` class exported by :mod:`meep_adjoint`
is the top-level entity in a hierarchy of classes that collectively
implement most of the mechanics of the adjoint solver.
Before delving into the :doc:`detailed API reference <OptimizationProblem>`,
on the following pages, we pause here to introduce the various classes
in the hierarchy and sketch how they work together to implement 
the adjoint solver.

------------------------------------------------------------
The class hierarchy in a nutshell
------------------------------------------------------------
In rough order from highest-level to lowest-level, the
classes in the hierarchy are:

    1. :class:`OptimizationProblem`
        |
        | Top-level class. Describes design-optimization problem.
        | 
        |

    2.
        |
        | Top-level class describing a design-optimization problem.
        | Stores all data and state 
        |

    3. ``ObjectiveFunction``: 
        |
        | Top-level class describing a design-optimization problem.
        | Stores all data and state 
        |

    4. ``DFTCell``:




.. admonition:: Design rationale

        The definitions and interactions of the classes are guided
        by a Unix-like logical aesthetic in which we aim for each
        class to do one thing and do it well; thus, each class
        has one overarching answer to the question
        *what does this entity know how to do?*, and (where appropriate)
        we take the class method implementing this basic operation
        as the ``__call__`` magic method of the class, 
        yielding a syntax that emphasizes the logical structure
        (see examples below).



In what follows we introduce the members of the class hierarchy
by describing the core competency of each, together with its
instantiating data (the info required to identify a unique
instance, passed as input parameters to the constructor)
and any state data it may accumulate over its lifetime.

/*

..
..     Given a vector of design-variable values :math:`\mathbf{c}`,
..     an instance of ``OptimizationProblem`` knows how to evaluate 
..     the objective-function value :math:`f(\mathbf{c})` and
..     gradient :math:`\nabla_{\mathbf{c}} f\equiv \{\frac{\partial f}{\partial c_d}\}`
..

*/



.. sidebar:: OptimizationProblem
    :class: fullbar


    .. glossary::


    Fundamental operation:
       Given a new vector of design variables :math:`\mathbf{c}`,
       compute the objective function value $f(\mathbf{c})$ and
       (optionally) the gradient :math:`\nabla f\equiv \{\frac{\partial f}{\partial c_d}\}`.


   Defining data: 
       The full complement of data items needed to specify an optimization
       problem



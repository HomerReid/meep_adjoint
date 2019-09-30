.. include:: ../Preamble.rst
.. ##################################################

********************************************************************************
Implementation notes I: The math and physics behind :py:mod:`meep_adjoint`
********************************************************************************
 
These notes are intended as something of a
companion to the rest of the :py:mod:`meep_adjoint` documentation,
and particularly as a complement and sequel to the
:doc:`Overview <../Overview/index>`; whereas the goal of
that content is to document the user interface and
explain how to use the solver for practical problems,
our focus here will be what's going on beneath the hood---how
the solver actually *works.*

Actually, as will be clear to anyone who has ever reviewed the
fundamentals of `adjoint sensitivity analysis`_,
the conceptual basis of the method and the derivation of its key
formulas are almost trivially straightforward, with the only
potential source of difficulty being how to massage the mechanics 
of the procedure into a form that comports with
:codename:`meep` conventions.


--------------------------------------------------------------------------------
Toy problem
--------------------------------------------------------------------------------

Ultimately we want to use adjoint methods to differentiate
complicated objective functions---involving quantities such as
Poynting fluxes and mode-expansion coefficients---with respect
to various different types of parameters describing material geometries.
However, before tackling the problem in that full generality,
it's useful to build up to it by starting with a simple toy problem
and adding complications one at a time. Thus we consider a
simple waveguide geometry, excited by a point source at
:math:`\mathbf{x}^\text{src}` and define our objective function to be
simply the frequency-domain electric-field amplitude at
a point :math:`\mathbf{x}^\text{obj}`; we will compute the derivative
of this objective function with respect to the permittivity
:math:`\epsilon^\text{des}`
in a small "design region" :math:`\mathcal{V}^\text{des}`
centered at a third point :math:`\mathbf{x}^\text{des}`.

.. image:: AdjointToyGeometry1.png

==================================================
Permittivity derivative by finite-differencing
==================================================

An obvious brute-force way to get at this is simply
to do two :codename:`meep` 
calculations, with :math:`\epsilon^\text{des}`
augmented by a small finite amount :math:`\Delta\epsilon` on the
second run, then compute the difference between the frequency-domain
electric fields at :math:`\mathbf{x}^\text{obj}` and divide
by :math:`\Delta\epsilon` to estimate the derivative.
The following two figures illustrate results obtained by 
executing such a strategy; the upper plot shows the spatial
distribution of **E**-field strength for the unperturbed geometry,
while the lower plot shows the *difference* between the field 
strengths in the perturbed and unperturbed cases:

.. math::

    \widetilde{E_{z0}}(\omega_0, \mathbf{x}) \text{(unperturbed)}:


.. image:: AdjointToyEz0.png


.. math::

    \Delta {\widetilde E_z}(\omega_0, \mathbf{x}) \text{(perturbed-unperturbed)}:


.. image:: AdjointToydEz_FD.png


(Here and below we use the tilde sign (:math:`\sim`) to indicate frequency-domain
fields and sources.)



==================================================
Permittivity derivative from effective sources
==================================================

One way to think about the effect of a localized permittivity
bump goes like this: Increasing the permittivity in some localized
region of a material body corresponds to increasing the
polarizability in that region---that is, the ease with which
positive and negative charges in the material, ordinarily bound
so tightly together that they neutralize each other as sources,
can be induced by applied electric fields to separate ("polarize"),
whereupon they cease to cancel each other and act as effective
sources contributing to electromagnetic fields.
Of course, if there were no electric field in the material,
then we could increase its polarizability as much as we pleased
without producing any sources---zero times a bigger
coefficient being still zero---but here there *is* a nonzero
electric field throughout our geometry, due to the point source
in the unperturbed problem, which means that the effect of bumping the
permittivity of the design region may be approximated by
adding new *sources* in that region, with strength
proportional to :math:`\Delta\epsilon` and to the unperturbed electric field.
More specifically, in a frequency-domain problem involving time-harmonic
fields and sources with angular frequency :math:`\omega` (time dependence
:math:`\propto e^{-i\omega t}`), the following perturbations are
equivalent:


.. math::

    \left(\begin{array}{c}
    \text{a permittivity shift of } \Delta\epsilon \\
    \text{over a small region } \mathcal{V} \text{ in which} \\
    \text{the electric field is } \widetilde{\mathbf{E}}
    \end{array}\right)
    \Longleftrightarrow
     \left(\begin{array}{c}
      \text{a localized electric current } \\
      \text{flowing in }\mathcal{V} \text{ with amplitude } \\
      \Delta\widetilde{\mathbf J}=-i\omega\Delta\epsilon \widetilde{\mathbf{E}}
     \end{array}\right)


|br|



.. image:: AdjointToyGeometry2.png

Superposing this effective source with the original point source
at :math:`\mathbf{x}^\text{src}` yields a source configuration that,
acting on the *unperturbed* geometry, produces the same fields
as the point source alone acting on the *perturbed* geometry.

Alternatively, by exploiting the linearity of Maxwell's equations
(and assuming we have linear media!) we could just as easily
remove the original point source and compute the fields of
:math:`\widetilde{\Delta \mathbf{J}}` *alone*, which, upon dividing through by
:math:`\Delta\epsilon`, give just the derivatives of field components
with respect to :math:`\epsilon`. In other words,

.. math::
    :nowrap:

    \[\frac{\partial \widetilde{\mathbf E} (\mathbf x^\text{obj}) } {\partial \epsilon^\text{des}}
    \equiv
    \left(\begin{array}{cc}
    \text{electric field at }\mathbf{x}^\text{obj} \text{ due to }\\
    \text{current at }\mathbf{x}^\text{des}\text{ with amplitude}\\
    \widetilde{\Delta \mathbf J}=-i\omega\widetilde{\mathbf{E}}(\mathbf{x}^\text{obj})
    \end{array}\right)
    \]
  

Analogous reasoning yields a prescription for magnetic-field derivatives:


.. math::
    :nowrap:

    \[\frac{\partial\widetilde{\mathbf{H}}(\mathbf x^\text{obj})}{\partial \epsilon^\text{des}}
    \equiv
    \left(
    \begin{array}{cc}
    \text{magnetic field at }\mathbf{x}^\text{obj} \text{ due to }\\
    \text{current at }\mathbf{x}^\text{des}\text{ with amplitude}\\
    \widetilde{\Delta \mathbf J}=-i\omega\widetilde{\mathbf{E}}(\mathbf{x}^\text{obj})
    \end{array}
    \right)\]


========================================================================================================
Digression: Configuring time-domain sources for desired frequency-domain fields in :codename:`meep`
========================================================================================================

In frequency-domain electromagnetism we usually consider 
a time-harmonic source distribution of the form


.. math::

    \mathbf{J}^\text{monochromatic}(t,\mathbf{x})\equiv \widetilde{\mathbf{J}}(\mathbf x)e^{-i\omega t}


and we ask for the time-harmonic electric field distribution
radiated by this distribution:

.. math::

    \mathbf{E}^\text{monochromatic}(t,\mathbf{x})\equiv\widetilde{\mathbf{E}}(\mathbf x)e^{-i\omega t}


where :math:`\sim` indicates frequency-domain amplitudes. A typical frequency-domain solver might input
:math:`\widetilde{\mathbf J}(\mathbf x)` and output :math:`\widetilde{\mathbf E}(\mathbf x)`:

.. math:: 

    \widetilde{\mathbf J}(\mathbf x)
    \quad \Longrightarrow \quad
    \begin{array}{|c|}\hline\\
    \text{    frequency-domain solver    }\\
    \\\hline\end{array}
    \quad \Longrightarrow \quad
    \widetilde{\mathbf E}(\mathbf x)


On the other hand, when using :codename:`meep` to compute
the fields produced by a given spatial source distribution,
we typically construct a time-domain source of the form
:math:`\mathbf{J}^\text{meep}(t,\mathbf{x})=G(t)\widetilde{\mathbf{J}}(\mathbf x)`
where :math:`G(t)` is a Gaussian temporal envelope.
More specifically, for a |GaussianSource| with
center frequency :math:`\omega_0=2\pi f_0`,
frequency width :math:`\Delta \omega =2\pi \Delta f`, and
peak time :math:`t_0`, we have


.. math:: 

    G(t) = e^{-i\omega_0(t-t_0) - \frac{1}{2}[\Delta f(t-t_0)]^2}.


The Fourier transform of this is


.. math::

   \widetilde G(\omega) \equiv \frac{1}{\sqrt{2\pi}}
   \int e^{i\omega t}G(t)\,dt =
   \frac{1}{\Delta f}
   e^{i\omega t_0 -\frac{(\omega-\omega_0)^2}{2\Delta f^2}}.


So the :codename:`meep` version of the above input/output diagram looks like

.. math:: 

    G(t)\widetilde{\mathbf J}(\mathbf x)
    \quad \Longrightarrow \quad
    \begin{array}{|c|}\hline\\
    \text{ MEEP }\\
    \text{    (timestepping + DFT)    } \\
    \\\hline\end{array}
    \quad \Longrightarrow \quad
    \widetilde{G}(\omega)\widetilde{\mathbf E}(\mathbf x)


The upshot is that the frequency-domain fields obtained from a
:codename:`meep` timestepping run with a Gaussian source
come out multiplied by a factor of :math:`\widetilde{G}(\omega)` that should
be divided out to yield the desired frequency-domain quantities.

--------------------------------------------------------------------------------
Invoking reciprocity
--------------------------------------------------------------------------------

It is convenient to describe the process described above
in the language of frequency-domain Green's functions, which
express the fields radiated by monochromatic source distributions
as spatial convolutions:

.. math::

    \widetilde{E_i}(\omega, \mathbf{x}^\text{dest}) =
    \int
    \mathcal{G}^\text{EE}_{ij}(\omega, \mathbf{x}^\text{dest}, \mathbf{x}^\text{src}) 
    \widetilde{J_j}(\omega, \mathbf{x}^\text{src})
   \,d\mathbf{x}^\text{src}


with :math:`\boldsymbol{\mathcal{G}}^\text{EE}` the
electric-electric dyadic Green's function of the material geometry
(giving the electric field produced by a unit-strength electric 
current).  In this language, the effective-source representation
of the permittivity derivative reads


.. math::


    \frac{\partial \widetilde{E}_i(\mathbf{x}^\text{obj})}{\partial \epsilon^\text{des}}
    =
    \int \mathcal{G}^\text{EE}_{ij}(\mathbf{x}^\text{obj}, \mathbf{x}^\text{des})
    \left[-i\omega \widetilde{E}_j(\mathbf{x}^\text{des})\right]
    \,d\mathbf{x}^\text{des}


It is convenient to think of the RHS here as a double convolution
of two vector-valued functions with the :math:`\boldsymbol{\mathcal{G}}^\text{EE}` kernel:


.. math::

    \frac{\partial \widetilde{E}_i(\mathbf{x}^\text{obj})}{\partial \epsilon^\text{des}}
    =
    \left[ \vphantom{\widetilde{\mathbf E}^\text{des}} \,\, \boldsymbol{\delta}_i^\text{obj}\,\,\right]
    \star \boldsymbol{\mathcal{G}}^\text{EE} \star
    \left[-i\omega \widetilde{\mathbf E}^\text{des}\right]


or


.. math::

    \newcommand{\VMV}[3]{ \Big\langle #1 \Big| #2 \Big| #3 \Big\rangle}
    \frac{\partial \widetilde E_i(\mathbf{x}^\text{obj})}{\partial \epsilon^\text{des}}
   =-i\omega\VMV{ \boldsymbol{\delta}_i^\text{obj} }
                { \boldsymbol{\mathcal{G}}^\text{EE}}
                { \widetilde{\mathbf E}^\text{des}}


where :math:`\star` denotes convolution,
:math:`\boldsymbol{\delta}_i^\text{obj}` is short for
:math:`\delta_{ij} \delta(\mathbf{x}-\mathbf{x}^\text{obj}),`
and the bra-ket notation describes a machine that inputs two
vector-valued functions :math:`\mathbf{f},\mathbf{g}` and a kernel :math:`\mathcal{K}`
and outputs a scalar quantity:


.. math::

    \VMV{\mathbf f}{\boldsymbol{\mathcal{K}}}{\mathbf g}
    \equiv \sum_{ij} \iint f_i(\mathbf{x})
    \mathcal{K}_{ij}(\mathbf{x},\mathbf{x}^\prime)
    g_j(\mathbf{x}^\prime) \,d\mathbf{x} \,d\mathbf{x}^\prime


(Note that this is not a Hermitian inner product, i.e. the first
factor is not conjugated.)

For the magnetic-field derivative we have similarly

.. math::

    \newcommand{\pard}[2]{\frac{\partial #1}{\partial #2}}
    \pard{\widetilde{H}_i(\mathbf{x}^\text{obj})}{\epsilon^\text{des}}
    =-i\omega\VMV{ \boldsymbol{\delta}_i^\text{obj}}
                { \boldsymbol{\mathcal G}^\text{ME}}
                { \widetilde{\mathbf E}^\text{des}}


where :math:`\boldsymbol{\mathcal{G}}^\text{ME}` is the magnetic-electric
Green's function, giving the magnetic field produced 
by an electric current.

Computationally, inner products like
:math:`\VMV{\mathbf f}{\boldsymbol{\mathcal{G}}^\text{EE}}{\mathbf g}` 
for arbitrary functions :math:`\mathbf{f}(\mathbf x), \mathbf{g}(\mathbf x)`
may be evaluated in :codename:`meep`
as follows:

1. Create an electric current source with
   spatially-varying amplitude :math:`\mathbf{g}(\mathbf x)`
   and Gaussian temporal envelope :math:`G(t)`.

2. Timestep and DFT to compute the frequency-domain electric field
   :math:`\widetilde{\mathbf E}(\omega; \mathbf{x})` produced by this source.

3. Compute the inner product
   :math:`[\widetilde{G}(\omega)]^{-1} \int \mathbf{f}\cdot \widetilde{\mathbf E}\,dV.`
   (The normalization prefactor was discussed above.)

The virtue of writing things this way is that it allows the physical
property of reciprocity to be expressed as the mathematical property
that the aforementioned inner-product machine is insensitive to the
order of its arguments, i.e. we can flip the :math:`\mathbf f` and :math:`\mathbf g` 
inputs and still get the same scalar output:


.. math::

    \VMV{\mathbf f}{\boldsymbol{\mathcal{K}}}{\mathbf g} = \VMV{\mathbf g}{\boldsymbol{\mathcal{K}}}{\mathbf f}
    \quad\text{ for }\quad \boldsymbol{\mathcal{K}}= \boldsymbol{\mathcal{G}}^\text{EE}, \boldsymbol{\mathcal{G}}^\text{ME}.


Applying reciprocity to the above expressions for field derivatives yields


.. math::
    :nowrap:

    \[
    \begin{align}
    \frac{\partial\widetilde E_i(\mathbf{x}^\text{obj})}{\partial \epsilon^\text{des}}
    &=-i\omega\VMV{ \widetilde{\mathbf E }^\text{des}}
                  { \boldsymbol{\mathcal{G}}^\text{EE}}
                  { \boldsymbol{\delta}_i^\text{obj}}
    \tag{2}
    \\[5pt]
    \pard{\widetilde H_i(\mathbf{x}^\text{obj})}{\epsilon^\text{des}}
    &=-i\omega\VMV{ \widetilde{\mathbf E }^\text{des}}
                  { \boldsymbol{\mathcal{G}}^\text{ME}}
                  { \boldsymbol{\delta}_i^\text{obj}}
    \tag{3a}
    \\
    \hphantom{\pard{\widetilde H_i(\mathbf{x}^\text{obj})}{\epsilon^\text{des}}}
    &=+i\omega\VMV{ \widetilde{\mathbf E}^\text{des}}
                  { \boldsymbol{\mathcal{G}}^\text{EM}}
                  { \boldsymbol{\delta}_i^\text{obj}}
    \tag{3b}
    \end{align}\]



where in going to the last line we invoked the identity
:math:`\boldsymbol{\mathcal{G}}^\text{EM}=-\boldsymbol{\mathcal{G}}^\text{ME}.`

Note that equations (3a) and (3b), notwithstanding their nearly
identical appearance, describe two rather different
:codename:meep calculations: In the former case
wf place an electric source at :math:`\mathbf x^\text{obj}` and timestep to
compute the resulting magnetic field, while in the latter
case we place a magnetic source and timestep
to compute the resulting electric field. (In both cases,
upon computing the field in question we proceed to compute its
overlap with the unperturbed :math:`\mathbf E` field in the design region.)

--------------------------------------------------------------------------------
Differentiating more complicated functions of field components
--------------------------------------------------------------------------------

Thus far we have only considered derivatives of individual
field components, and then only at a single point :math:`\mathbf{x}^\text{obj}`;
more generally, we will want to differentiate functions of
multiple field components over a subregion of the grid,
which we will call the *objective region* :math:`\mathcal{V}^\text{obj}`.

================================================================================
**E**-field energy in region
================================================================================

As one example, the electric field energy in the objective
region is defined by an integral over that region, which :codename:`meep`
approximates by a weighted sum over grid points:

.. math::

    \mathcal{E}=
    \frac{1}{2}\int_{\mathcal{V}^\text{obj}} \epsilon |\widetilde{\mathbf E}|^2 \,d\mathcal{V}
    \approx
    \frac{1}{2}\sum_{i,\mathbf{n}\in\mathcal{V}^\text{obj}} w_{\mathbf{n}}
    \epsilon_\mathbf {n} \widetilde E_{i\mathbf n}^* \widetilde E_{i\mathbf n}


Here the sum is over all field components :math:`i=\{x,y,z\}` and
all grid points :math:`\mathbf{n}` lying in :math:`\mathcal{V}^\text{obj}`,
and :math:`w_{\mathbf{n}}` is a cubature weight associated with point :math:`\mathbf{n}`.

Differentiating, we have


.. math::
    :nowrap:

    \[
    \begin{align}
    \frac{\partial\mathcal E}{\partial\epsilon^\text{des}}
    &=\text{Re }\sum_{i\mathbf{n}\in\mathcal V^\text{obj}} w_{\mathbf n}\epsilon_{\mathbf n}
      \widetilde{E}^*_{i\mathbf n} \pard{\widetilde{E}_{i\mathbf n}} {\epsilon^\text{des}}
    \\
    &\hspace{-1.5in}\text{Insert equation (1a):}
    \\
    &=\text{Re }\left\{ -i\omega \VMV{\epsilon \widetilde{\mathbf E}^\text{obj*}}
                                      {{\boldsymbol{\mathcal{G}}}^\text{EE}}
                                      {\widetilde{\mathbf E}^\text{des}}
                 \right\}
    \\
    &\hspace{-1.5in}\text{Invoke reciprocity:}
    \\
    &=\text{Re }\left\{ -i\omega \VMV{\widetilde{\mathbf E}^\text{des}}
                                     {{\boldsymbol{\mathcal{G}}}^\text{EE}}
                                     {\epsilon \widetilde{\mathbf E}^\text{obj*}}
                 \right\}
    \end{align}
    \]


================================================================================
Poynting flux
================================================================================

A case that arises frequently is that in which the objective region
is a cross-sectional surface :math:`\mathcal S^\text{obj}` cutting normally through a
waveguide or similar structure and the objective function is the 
normal Poynting flux through :math:`\mathcal S`.
For example, the :math:`x`-directed Poynting flux is given by


.. math::
    S_x
    =
    \frac{1}{2}\text{Re }\left\{ \int_{\mathcal S^\text{obj}} \Big(E^*_y H_z + \cdots\Big) \, d\mathbf{x} \right\}
    \approx \frac{1}{2}\text{Re }\sum_{\mathbf n\in \mathcal S^\text{obj}} w_{\mathbf n}
    \Big(E^*_{y\mathbf n} H_{z\mathbf n} + \cdots\Big)


where :math:`\cdots` refers to three other terms of the form :math:`\pm E^*_i H_j`.
Differentiating and rearranging slightly, we have


.. math::
    :nowrap:


    \[
    \begin{align}
    \frac{\partial S_x}{\partial \epsilon^\text{des}}
    &=\text{Re }\sum_{\mathbf n\in \mathcal S^\text{obj}} w
      \left\{ \widetilde{E}^*_{y} \pard{\widetilde{H}_z}{\epsilon^\text{des}}
             +\widetilde{H}^*_{z} \pard{\widetilde{E}_y}{\epsilon^\text{des}}
            +\cdots
      \right\}
    \\[5pt]
    &\hspace{-0.5in}\text{Use (1a) and (1b):}
    \\[5pt]
    &=\text{Re }\left\{ -i\omega \VMV{\widetilde{\mathbf E}_{y}^\text{obj*}}
                                     {\boldsymbol{\mathcal{G}}^\text{ME}}
                                     {\widetilde{\mathbf E}^\text{des}}
                        -i\omega \VMV{\widetilde{\mathbf H}_z^\text{obj*}} {\boldsymbol{\mathcal{G}}^\text{EE}}
                                     {\widetilde{\mathbf E}^\text{des}}
                        +\cdots
               \right\} 
    \\[5pt]
    &\hspace{-0.5in}\text{Use reciprocity:}
    \\[5pt]
    &=\text{Re }\left\{ -i\omega  \VMV{\widetilde{\mathbf E}^\text{des}}
                                     {\boldsymbol{\mathcal{G}}^\text{ME}}
                                     {\widetilde{\mathbf E}_y^\text{obj*}}
                       -i\omega \VMV{\widetilde{\mathbf E}^\text{des}}
                                    {\boldsymbol{\mathcal{G}}^\text{EE}}
                                    {\widetilde{\mathbf H}_z^\text{obj*}}
                       +\cdots
                 \right\}
    \end{align}
    \]


.. ######################################################################
.. HR20190926 this section current commented out
.. ######################################################################
.. 
.. ======================================================================
.. Mode coefficient
.. ======================================================================
.. 
.. :math:`` \alpha_m^\pm = C_1 \pm C_2 :math:``
.. \begin{align*}
..  C_1 &=\frac{1}{\mathcal{N}}
..    \int_{\mathcal S^\text{obj}} \Big(e^*_y H_z - e^*_z H_y\Big)d\mathbf{x}\\
..  C_2 &=
..    \frac{1}{\mathcal{N}}\int_{\mathcal S^\text{obj}} \Big(h^*_z E_y - h^*_y E_z\Big)d\mathbf{x}\\
.. \end{align*}
.. 
.. 
.. 


.. |br| raw:: html

    <br>


.. ##################################################
.. include:: ../Postamble.rst
.. ##################################################




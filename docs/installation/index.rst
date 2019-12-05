***********************************************************************************
Installation
***********************************************************************************

The `meep_adjoint` package consists of just a handful of python files (i.e. there
are no C++ codes to compile or libraries to link), so the package installation
is essentially instantaneous, **assuming** all prerequisite packages have been
installed on your system.

:strike:`The only potential source of difficulty here is that getting the prerequisites
to play nicely with each other is somewhat tricky.` **Update:** Previously there was 
some difficulty
in creating a Conda environment containing both the :codename:`fenics` and |meep|
packages, which was evaded by building |meep| from source. This approach is
discussed in Section 1**(b)** below. However, as of recently (November 2019) the conda
difficulties seem to have gone away, and the easier approach of Section 1**(a)**
seems to be working generally. 

--------------------------------------------------
1. Install required packages
--------------------------------------------------

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
1A. Create a conda environment containing both :codename:`fenics` and :codename:`meep`
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The simplest way to proceed here is to create a :codename:`conda`_ environment containing all dependencies.
(If you aren't a condaficionado, `this backgrounder`_ in the |meep| documentation is helpful.)
For example, on my linux system running :codename:`conda` version 4.8.0rc0, the following commands
suffice to create and activate a new environment named `py37_for_meep_adjoint` (of course you can
use any name you like):

    .. code-block:: bash
        $ conda create -n py37_for_meep_adjoint -c conda-canary -c conda-forge python=3.7 mpich fenics pymeep psutil
        $ conda activate py37_for_meep_adjoint
        (py37_for_meep_adjoint) $

.. _conda: https://conda.io/docs
.. _this backgrounder: https://meep.readthedocs.io/en/latest/Installation/

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
1B. Create a conda environment containing :codename:`fenics` and build :codename:`meep` from source
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

At one point in the not-so-distant past, the conda-packaged versions of :codename:`fenics` and :codename:`meep` were
incompatible and could not be present simultaneously in the same conda environment. The solution was to
remove :codename:`meep` from the conda environment  (retaining :codename:`fenics`), then fetch the source
distributions for 
:codename:`meep` and its required support packages (:codename:`libctl` and :codename:`mpb`) and build from source
This is not too hard, but it requires installing a few extra :codename:`conda` packages to support the build from
source, without which one tends to get errors arising from the compiler/linker suite attempting to use some headers/libraries
from the conda installation and others from the system installation. The particular constellation of conda packages that
needed to be in place to prevent this seemed to vary with time and could only be determined by an annoying trial-and-error
process (try to build from source, get failure message, scrutinize log files to pinpoint missing conda packages,
install, repeat). Hopefully this is now obviated by the apparent success of the method discussed above. If not,
I will post a script that mostly automates the :codename:`meep` build-from-source process.

--------------------------------------------------
2. Install `meep_adjoint`
--------------------------------------------------



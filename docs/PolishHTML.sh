#!/bin/bash

BASE=/home/homer/work/Simpetus/meep_adjoint/docs/_build/html

#for FILE in `find ${BASE} -name '*html'`; do
FILE=${BASE}/Tutorial/index.html
  sed -i 's/\(toctree-l1.*\)meep_adjoint\(.*\)MEEP/\1<code xref>meep_adjoint<\/code>\2<span class="codename">meep<\/span>/g' ${FILE}
#done

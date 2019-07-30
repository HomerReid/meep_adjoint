#!/bin/bash

# 
# Simple script to generate python code for the meep_adjoint dashboard
# QT widget from the `.ui` file produced by QT Designer.
#

INFILE=qt_dashboard.ui
OUTFILE=qt_dashboard.py
 
pyuic5 ${INFILE} \
 | sed 's/setupUi(self, Form):/setupUi(self, Form, width=960):\n        def _sc(x): return int(x*width\/960.0)/' \
 | sed 's/Form.resize(\([0-9]*\), *\([0-9]*\)/Form.resize(_sc(\1),_sc(\2)/'                              \
 | sed 's/QRect.\([0-9]*\), \([0-9]*\), \([0-9]*\), \([0-9]*\)/QRect(_sc(\1),_sc(\2),_sc(\3),_sc(\4)/'    \
 | sed 's/font.setPointSize.\([0-9]*\)/font.setPointSize(_sc(\1)/'                                        \
 > ${OUTFILE}

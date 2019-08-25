#!/bin/bash

# 
# Simple script to generate python code for the Ui_BaseDashboard
# base widget class from the `.ui` file produced by QT Designer.
#

INFILE=dashboard_gui.ui
OUTFILE=../dashboard_gui.py
 
pyuic5 ${INFILE} \
 | sed 's/setupUi(self, db_widget):/setupUi(self, db_widget, width=960):\n        def _sc(x): return int(x*width\/960.0)/' \
 | sed 's/db_widget.resize(\([0-9]*\), *\([0-9]*\)/db_widget.resize(_sc(\1),_sc(\2)/'                           \
 | sed 's/QRect.\([0-9]*\), \([0-9]*\), \([0-9]*\), \([0-9]*\)/QRect(_sc(\1),_sc(\2),_sc(\3),_sc(\4)/'    	\
 | sed 's/font.setPointSize.\([0-9]*\)/font.setPointSize(_sc(\1)/'                                        	\
 | grep -v 'QPalette.PlaceholderText'										\
 > ${OUTFILE}


pyrcc5 dashboard_theme.qrc > ../dashboard_theme.py

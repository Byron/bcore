# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/gui/widgets/ui/selector.ui'
#
# Created: Tue Jul 30 10:38:02 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SelectorWidget(object):
    def setupUi(self, SelectorWidget):
        SelectorWidget.setObjectName("SelectorWidget")
        SelectorWidget.resize(326, 41)
        self.horizontalLayout = QtGui.QHBoxLayout(SelectorWidget)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.plugins = QtGui.QComboBox(SelectorWidget)
        self.plugins.setObjectName("plugins")
        self.horizontalLayout.addWidget(self.plugins)

        self.retranslateUi(SelectorWidget)
        QtCore.QMetaObject.connectSlotsByName(SelectorWidget)

    def retranslateUi(self, SelectorWidget):
        SelectorWidget.setWindowTitle(QtGui.QApplication.translate("SelectorWidget", "Selector", None, QtGui.QApplication.UnicodeUTF8))
        self.plugins.setToolTip(QtGui.QApplication.translate("SelectorWidget", "A selection of available job submitters", None, QtGui.QApplication.UnicodeUTF8))


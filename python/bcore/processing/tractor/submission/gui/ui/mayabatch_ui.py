# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processing/tractor/submission/gui/ui/mayabatch.ui'
#
# Created: Tue Jul 30 13:26:16 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MayaBatchBox(object):
    def setupUi(self, MayaBatchBox):
        MayaBatchBox.setObjectName("MayaBatchBox")
        MayaBatchBox.resize(306, 120)
        self.verticalLayout = QtGui.QVBoxLayout(MayaBatchBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.cmdpython = QtGui.QTextEdit(MayaBatchBox)
        self.cmdpython.setObjectName("cmdpython")
        self.verticalLayout.addWidget(self.cmdpython)

        self.retranslateUi(MayaBatchBox)
        QtCore.QMetaObject.connectSlotsByName(MayaBatchBox)

    def retranslateUi(self, MayaBatchBox):
        MayaBatchBox.setWindowTitle(QtGui.QApplication.translate("MayaBatchBox", "Maya Batch", None, QtGui.QApplication.UnicodeUTF8))
        MayaBatchBox.setTitle(QtGui.QApplication.translate("MayaBatchBox", "Maya Python Command", None, QtGui.QApplication.UnicodeUTF8))
        self.cmdpython.setToolTip(QtGui.QApplication.translate("MayaBatchBox", "Python command to execute. It may use the \'store\' variable, which is a kvstore with information about the nature of the batch command (it can contain chunking information for example)", None, QtGui.QApplication.UnicodeUTF8))


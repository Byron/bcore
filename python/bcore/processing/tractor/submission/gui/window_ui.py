# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processing/tractor/submission/gui/window.ui'
#
# Created: Tue Jul 30 18:01:05 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SubmitoolWindow(object):
    def setupUi(self, SubmitoolWindow):
        SubmitoolWindow.setObjectName("SubmitoolWindow")
        SubmitoolWindow.resize(342, 231)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SubmitoolWindow.sizePolicy().hasHeightForWidth())
        SubmitoolWindow.setSizePolicy(sizePolicy)
        self.controller = TractorSubmissionController(SubmitoolWindow)
        self.controller.setObjectName("controller")
        self.menubar = QtGui.QMenuBar(SubmitoolWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 342, 26))
        self.menubar.setObjectName("menubar")
        SubmitoolWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(SubmitoolWindow)
        self.statusbar.setObjectName("statusbar")
        SubmitoolWindow.setStatusBar(self.statusbar)

        self.retranslateUi(SubmitoolWindow)
        QtCore.QMetaObject.connectSlotsByName(SubmitoolWindow)

    def retranslateUi(self, SubmitoolWindow):
        SubmitoolWindow.setWindowTitle(QtGui.QApplication.translate("SubmitoolWindow", "Submitool v0.1.0", None, QtGui.QApplication.UnicodeUTF8))

from .controller import TractorSubmissionController

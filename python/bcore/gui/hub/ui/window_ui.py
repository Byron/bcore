# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/gui/hub/ui/window.ui'
#
# Created: Mon Aug  5 09:58:07 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_HubWindow(object):
    def setupUi(self, HubWindow):
        HubWindow.setObjectName("HubWindow")
        HubWindow.resize(557, 449)
        self.centralwidget = QtGui.QWidget(HubWindow)
        self.centralwidget.setObjectName("centralwidget")
        HubWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(HubWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 557, 26))
        self.menubar.setObjectName("menubar")
        HubWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(HubWindow)
        self.statusbar.setObjectName("statusbar")
        HubWindow.setStatusBar(self.statusbar)

        self.retranslateUi(HubWindow)
        QtCore.QMetaObject.connectSlotsByName(HubWindow)

    def retranslateUi(self, HubWindow):
        HubWindow.setWindowTitle(QtGui.QApplication.translate("HubWindow", "The Hub", None, QtGui.QApplication.UnicodeUTF8))


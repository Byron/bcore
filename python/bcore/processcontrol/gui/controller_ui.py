# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processcontrol/gui/controller.ui'
#
# Created: Thu Aug  8 11:11:48 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_PackageViewerWindow(object):
    def setupUi(self, PackageViewerWindow):
        PackageViewerWindow.setObjectName("PackageViewerWindow")
        PackageViewerWindow.resize(345, 282)
        self.vlayout = QtGui.QVBoxLayout(PackageViewerWindow)
        self.vlayout.setObjectName("vlayout")
        self.scrollArea = QtGui.QScrollArea(PackageViewerWindow)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.viewer = PackageViewerWidget()
        self.viewer.setGeometry(QtCore.QRect(0, 0, 325, 226))
        self.viewer.setObjectName("viewer")
        self.scrollArea.setWidget(self.viewer)
        self.vlayout.addWidget(self.scrollArea)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.ok = QtGui.QPushButton(PackageViewerWindow)
        self.ok.setObjectName("ok")
        self.horizontalLayout.addWidget(self.ok)
        self.vlayout.addLayout(self.horizontalLayout)

        self.retranslateUi(PackageViewerWindow)
        QtCore.QObject.connect(self.ok, QtCore.SIGNAL("released()"), PackageViewerWindow.close)
        QtCore.QMetaObject.connectSlotsByName(PackageViewerWindow)

    def retranslateUi(self, PackageViewerWindow):
        PackageViewerWindow.setWindowTitle(QtGui.QApplication.translate("PackageViewerWindow", "Package Information", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setToolTip(QtGui.QApplication.translate("PackageViewerWindow", "Acknowledge the package information and close this window.", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setText(QtGui.QApplication.translate("PackageViewerWindow", "OK", None, QtGui.QApplication.UnicodeUTF8))

from .viewer import PackageViewerWidget

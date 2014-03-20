# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processcontrol/gui/ui/viewer.ui'
#
# Created: Thu Aug  8 20:23:23 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_PackageViewerWidget(object):
    def setupUi(self, PackageViewerWidget):
        PackageViewerWidget.setObjectName("PackageViewerWidget")
        PackageViewerWidget.resize(339, 204)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PackageViewerWidget.sizePolicy().hasHeightForWidth())
        PackageViewerWidget.setSizePolicy(sizePolicy)
        self.vlayout = QtGui.QVBoxLayout(PackageViewerWidget)
        self.vlayout.setObjectName("vlayout")
        self.message = QtGui.QLabel(PackageViewerWidget)
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.message.setObjectName("message")
        self.vlayout.addWidget(self.message)
        self.pnew = QtGui.QGroupBox(PackageViewerWidget)
        self.pnew.setObjectName("pnew")
        self.verticalLayout = QtGui.QVBoxLayout(self.pnew)
        self.verticalLayout.setObjectName("verticalLayout")
        self.vlayout.addWidget(self.pnew)
        self.premoved = QtGui.QGroupBox(PackageViewerWidget)
        self.premoved.setObjectName("premoved")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.premoved)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.vlayout.addWidget(self.premoved)
        self.pchanged = QtGui.QGroupBox(PackageViewerWidget)
        self.pchanged.setObjectName("pchanged")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.pchanged)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.vlayout.addWidget(self.pchanged)
        self.pall = QtGui.QGroupBox(PackageViewerWidget)
        self.pall.setObjectName("pall")
        self.vlayout_2 = QtGui.QVBoxLayout(self.pall)
        self.vlayout_2.setObjectName("vlayout_2")
        self.vlayout.addWidget(self.pall)

        self.retranslateUi(PackageViewerWidget)
        QtCore.QMetaObject.connectSlotsByName(PackageViewerWidget)

    def retranslateUi(self, PackageViewerWidget):
        PackageViewerWidget.setWindowTitle(QtGui.QApplication.translate("PackageViewerWidget", "Viewer", None, QtGui.QApplication.UnicodeUTF8))
        self.message.setText(QtGui.QApplication.translate("PackageViewerWidget", "nothing to display", None, QtGui.QApplication.UnicodeUTF8))
        self.pnew.setToolTip(QtGui.QApplication.translate("PackageViewerWidget", "Newly added packages", None, QtGui.QApplication.UnicodeUTF8))
        self.pnew.setTitle(QtGui.QApplication.translate("PackageViewerWidget", "New Packages", None, QtGui.QApplication.UnicodeUTF8))
        self.premoved.setToolTip(QtGui.QApplication.translate("PackageViewerWidget", "Removed packages", None, QtGui.QApplication.UnicodeUTF8))
        self.premoved.setTitle(QtGui.QApplication.translate("PackageViewerWidget", "Deleted Packages", None, QtGui.QApplication.UnicodeUTF8))
        self.pchanged.setToolTip(QtGui.QApplication.translate("PackageViewerWidget", "Packages whose version or meta-data changed", None, QtGui.QApplication.UnicodeUTF8))
        self.pchanged.setTitle(QtGui.QApplication.translate("PackageViewerWidget", "Changed Packages", None, QtGui.QApplication.UnicodeUTF8))
        self.pall.setToolTip(QtGui.QApplication.translate("PackageViewerWidget", "A list of all packages used by an application", None, QtGui.QApplication.UnicodeUTF8))
        self.pall.setTitle(QtGui.QApplication.translate("PackageViewerWidget", "Packages", None, QtGui.QApplication.UnicodeUTF8))


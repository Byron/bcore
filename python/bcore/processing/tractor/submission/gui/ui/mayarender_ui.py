# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processing/tractor/submission/gui/ui/mayarender.ui'
#
# Created: Tue Jul 30 18:35:01 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MayaRenderBox(object):
    def setupUi(self, MayaRenderBox):
        MayaRenderBox.setObjectName("MayaRenderBox")
        MayaRenderBox.resize(323, 121)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MayaRenderBox.sizePolicy().hasHeightForWidth())
        MayaRenderBox.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(MayaRenderBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_image_output_directory = QtGui.QLabel(MayaRenderBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_image_output_directory.sizePolicy().hasHeightForWidth())
        self.label_image_output_directory.setSizePolicy(sizePolicy)
        self.label_image_output_directory.setMinimumSize(QtCore.QSize(50, 0))
        self.label_image_output_directory.setObjectName("label_image_output_directory")
        self.horizontalLayout.addWidget(self.label_image_output_directory)
        self.image_output_directory = QtGui.QLineEdit(MayaRenderBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.image_output_directory.sizePolicy().hasHeightForWidth())
        self.image_output_directory.setSizePolicy(sizePolicy)
        self.image_output_directory.setObjectName("image_output_directory")
        self.horizontalLayout.addWidget(self.image_output_directory)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(MayaRenderBox)
        QtCore.QMetaObject.connectSlotsByName(MayaRenderBox)

    def retranslateUi(self, MayaRenderBox):
        MayaRenderBox.setWindowTitle(QtGui.QApplication.translate("MayaRenderBox", "GroupBox", None, QtGui.QApplication.UnicodeUTF8))
        MayaRenderBox.setTitle(QtGui.QApplication.translate("MayaRenderBox", "Maya Render Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label_image_output_directory.setText(QtGui.QApplication.translate("MayaRenderBox", "Render Dir", None, QtGui.QApplication.UnicodeUTF8))


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processing/tractor/submission/gui/ui/multitask.ui'
#
# Created: Wed Jul 31 08:10:50 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MultiTaskGeneratorBox(object):
    def setupUi(self, MultiTaskGeneratorBox):
        MultiTaskGeneratorBox.setObjectName("MultiTaskGeneratorBox")
        MultiTaskGeneratorBox.resize(336, 110)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MultiTaskGeneratorBox.sizePolicy().hasHeightForWidth())
        MultiTaskGeneratorBox.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(MultiTaskGeneratorBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.info = QtGui.QLabel(MultiTaskGeneratorBox)
        self.info.setObjectName("info")
        self.verticalLayout.addWidget(self.info)
        self.files = QtGui.QListWidget(MultiTaskGeneratorBox)
        self.files.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.files.sizePolicy().hasHeightForWidth())
        self.files.setSizePolicy(sizePolicy)
        self.files.setMinimumSize(QtCore.QSize(0, 50))
        self.files.setObjectName("files")
        self.verticalLayout.addWidget(self.files)

        self.retranslateUi(MultiTaskGeneratorBox)
        QtCore.QMetaObject.connectSlotsByName(MultiTaskGeneratorBox)

    def retranslateUi(self, MultiTaskGeneratorBox):
        MultiTaskGeneratorBox.setWindowTitle(QtGui.QApplication.translate("MultiTaskGeneratorBox", "Job", None, QtGui.QApplication.UnicodeUTF8))
        MultiTaskGeneratorBox.setTitle(QtGui.QApplication.translate("MultiTaskGeneratorBox", "Multi-File", None, QtGui.QApplication.UnicodeUTF8))
        self.info.setText(QtGui.QApplication.translate("MultiTaskGeneratorBox", "Files to submit xxx", None, QtGui.QApplication.UnicodeUTF8))
        self.files.setToolTip(QtGui.QApplication.translate("MultiTaskGeneratorBox", "A list of files to be processed in this job", None, QtGui.QApplication.UnicodeUTF8))


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processing/tractor/submission/gui/ui/submit.ui'
#
# Created: Mon Jul 29 23:20:52 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SubmitWidget(object):
    def setupUi(self, SubmitWidget):
        SubmitWidget.setObjectName("SubmitWidget")
        SubmitWidget.resize(422, 51)
        self.hlayout = QtGui.QHBoxLayout(SubmitWidget)
        self.hlayout.setSpacing(4)
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setObjectName("hlayout")
        self.label = QtGui.QLabel(SubmitWidget)
        self.label.setObjectName("label")
        self.hlayout.addWidget(self.label)
        self.priority = QtGui.QComboBox(SubmitWidget)
        self.priority.setObjectName("priority")
        self.hlayout.addWidget(self.priority)
        self.paused = QtGui.QCheckBox(SubmitWidget)
        self.paused.setObjectName("paused")
        self.hlayout.addWidget(self.paused)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hlayout.addItem(spacerItem)
        self.submit = QtGui.QPushButton(SubmitWidget)
        self.submit.setEnabled(False)
        self.submit.setObjectName("submit")
        self.hlayout.addWidget(self.submit)

        self.retranslateUi(SubmitWidget)
        self.priority.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(SubmitWidget)

    def retranslateUi(self, SubmitWidget):
        SubmitWidget.setWindowTitle(QtGui.QApplication.translate("SubmitWidget", "Submission", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("SubmitWidget", "Priority", None, QtGui.QApplication.UnicodeUTF8))
        self.priority.setToolTip(QtGui.QApplication.translate("SubmitWidget", "Prioritze your Job according to presets", None, QtGui.QApplication.UnicodeUTF8))
        self.paused.setToolTip(QtGui.QApplication.translate("SubmitWidget", "If checked, the job will not start when it arrives on the queue", None, QtGui.QApplication.UnicodeUTF8))
        self.paused.setText(QtGui.QApplication.translate("SubmitWidget", "Paused", None, QtGui.QApplication.UnicodeUTF8))
        self.submit.setToolTip(QtGui.QApplication.translate("SubmitWidget", "Submit your currently configured job", None, QtGui.QApplication.UnicodeUTF8))
        self.submit.setText(QtGui.QApplication.translate("SubmitWidget", "Submit", None, QtGui.QApplication.UnicodeUTF8))


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processing/tractor/submission/gui/ui/message.ui'
#
# Created: Tue Jul 30 09:58:27 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MessageDialog(object):
    def setupUi(self, MessageDialog):
        MessageDialog.setObjectName("MessageDialog")
        MessageDialog.resize(283, 129)
        MessageDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(MessageDialog)
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(MessageDialog)
        self.label.setText("")
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.buttons = QtGui.QDialogButtonBox(MessageDialog)
        self.buttons.setOrientation(QtCore.Qt.Horizontal)
        self.buttons.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttons.setCenterButtons(False)
        self.buttons.setObjectName("buttons")
        self.verticalLayout.addWidget(self.buttons)

        self.retranslateUi(MessageDialog)
        QtCore.QObject.connect(self.buttons, QtCore.SIGNAL("accepted()"), MessageDialog.accept)
        QtCore.QObject.connect(self.buttons, QtCore.SIGNAL("rejected()"), MessageDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(MessageDialog)

    def retranslateUi(self, MessageDialog):
        MessageDialog.setWindowTitle(QtGui.QApplication.translate("MessageDialog", "Message", None, QtGui.QApplication.UnicodeUTF8))
        self.buttons.setToolTip(QtGui.QApplication.translate("MessageDialog", "\"Close\" the entire window, or confirm with \"OK\"", None, QtGui.QApplication.UnicodeUTF8))


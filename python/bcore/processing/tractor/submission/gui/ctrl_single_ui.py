# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processing/tractor/submission/gui/ctrl_single.ui'
#
# Created: Tue Jul 30 07:30:20 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SingleJob(object):
    def setupUi(self, SingleJob):
        SingleJob.setObjectName("SingleJob")
        SingleJob.resize(240, 201)
        self.vlayout = QtGui.QVBoxLayout(SingleJob)
        self.vlayout.setSpacing(4)
        self.vlayout.setContentsMargins(9, 9, 9, 9)
        self.vlayout.setObjectName("vlayout")
        self.selector = TractorSelectorWidget(SingleJob)
        self.selector.setObjectName("selector")
        self.vlayout.addWidget(self.selector)
        self.properties = TractorGeneratorChainPropertiesWidget(SingleJob)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.properties.sizePolicy().hasHeightForWidth())
        self.properties.setSizePolicy(sizePolicy)
        self.properties.setObjectName("properties")
        self.vlayout.addWidget(self.properties)
        self.submit = TractorSubmissionWidget(SingleJob)
        self.submit.setObjectName("submit")
        self.vlayout.addWidget(self.submit)

        self.retranslateUi(SingleJob)
        QtCore.QMetaObject.connectSlotsByName(SingleJob)

    def retranslateUi(self, SingleJob):
        SingleJob.setWindowTitle(QtGui.QApplication.translate("SingleJob", "SingleSubmitWidget", None, QtGui.QApplication.UnicodeUTF8))

from .widgets import TractorGeneratorChainPropertiesWidget, TractorSubmissionWidget, TractorSelectorWidget

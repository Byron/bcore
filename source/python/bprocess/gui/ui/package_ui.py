# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processcontrol/gui/ui/package.ui'
#
# Created: Thu Aug  8 20:23:23 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_PackageFrame(object):
    def setupUi(self, PackageFrame):
        PackageFrame.setObjectName("PackageFrame")
        PackageFrame.resize(424, 88)
        PackageFrame.setFrameShape(QtGui.QFrame.NoFrame)
        PackageFrame.setFrameShadow(QtGui.QFrame.Plain)
        self.verticalLayout_2 = QtGui.QVBoxLayout(PackageFrame)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame = QtGui.QFrame(PackageFrame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QtCore.QSize(50, 0))
        self.frame.setFrameShape(QtGui.QFrame.Box)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtGui.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        self.package_label = QtGui.QLabel(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.package_label.sizePolicy().hasHeightForWidth())
        self.package_label.setSizePolicy(sizePolicy)
        self.package_label.setObjectName("package_label")
        self.verticalLayout.addWidget(self.package_label)
        self.description_group = QtGui.QWidget(self.frame)
        self.description_group.setObjectName("description_group")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.description_group)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtGui.QSpacerItem(60, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.description = QtGui.QLabel(self.description_group)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.description.sizePolicy().hasHeightForWidth())
        self.description.setSizePolicy(sizePolicy)
        self.description.setWordWrap(True)
        self.description.setObjectName("description")
        self.horizontalLayout_2.addWidget(self.description)
        self.verticalLayout.addWidget(self.description_group)
        self.horizontalLayout.addWidget(self.frame)
        spacerItem1 = QtGui.QSpacerItem(0, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.version_previous = QtGui.QLabel(PackageFrame)
        self.version_previous.setObjectName("version_previous")
        self.horizontalLayout.addWidget(self.version_previous)
        self.help = QtGui.QPushButton(PackageFrame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.help.sizePolicy().hasHeightForWidth())
        self.help.setSizePolicy(sizePolicy)
        self.help.setMinimumSize(QtCore.QSize(40, 40))
        self.help.setMaximumSize(QtCore.QSize(50, 16777215))
        self.help.setObjectName("help")
        self.horizontalLayout.addWidget(self.help)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(PackageFrame)
        QtCore.QMetaObject.connectSlotsByName(PackageFrame)

    def retranslateUi(self, PackageFrame):
        PackageFrame.setWindowTitle(QtGui.QApplication.translate("PackageFrame", "PackageWidget", None, QtGui.QApplication.UnicodeUTF8))
        self.package_label.setToolTip(QtGui.QApplication.translate("PackageFrame", "Package Name and Version", None, QtGui.QApplication.UnicodeUTF8))
        self.package_label.setText(QtGui.QApplication.translate("PackageFrame", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">package@version</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.description.setToolTip(QtGui.QApplication.translate("PackageFrame", "Package Description", None, QtGui.QApplication.UnicodeUTF8))
        self.description.setText(QtGui.QApplication.translate("PackageFrame", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.version_previous.setToolTip(QtGui.QApplication.translate("PackageFrame", "Version of the package in the previous application invocation", None, QtGui.QApplication.UnicodeUTF8))
        self.version_previous.setText(QtGui.QApplication.translate("PackageFrame", "v.old", None, QtGui.QApplication.UnicodeUTF8))
        self.help.setToolTip(QtGui.QApplication.translate("PackageFrame", "Launch a browser to a more descriptive web-page", None, QtGui.QApplication.UnicodeUTF8))
        self.help.setText(QtGui.QApplication.translate("PackageFrame", "?", None, QtGui.QApplication.UnicodeUTF8))


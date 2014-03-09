# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bdevel/core/processing/tractor/submission/gui/ui/executor.ui'
#
# Created: Sun Sep  1 11:02:03 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_ExecuteGeneratorBox(object):
    def setupUi(self, ExecuteGeneratorBox):
        ExecuteGeneratorBox.setObjectName("ExecuteGeneratorBox")
        ExecuteGeneratorBox.resize(451, 324)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ExecuteGeneratorBox.sizePolicy().hasHeightForWidth())
        ExecuteGeneratorBox.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(ExecuteGeneratorBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.title_layout = QtGui.QHBoxLayout()
        self.title_layout.setObjectName("title_layout")
        self.executable_label = QtGui.QLabel(ExecuteGeneratorBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.executable_label.sizePolicy().hasHeightForWidth())
        self.executable_label.setSizePolicy(sizePolicy)
        self.executable_label.setMinimumSize(QtCore.QSize(80, 0))
        self.executable_label.setObjectName("executable_label")
        self.title_layout.addWidget(self.executable_label)
        self.executable = QtGui.QLineEdit(ExecuteGeneratorBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.executable.sizePolicy().hasHeightForWidth())
        self.executable.setSizePolicy(sizePolicy)
        self.executable.setObjectName("executable")
        self.title_layout.addWidget(self.executable)
        self.verticalLayout.addLayout(self.title_layout)
        self.file_layout = QtGui.QHBoxLayout()
        self.file_layout.setObjectName("file_layout")
        self.args_label = QtGui.QLabel(ExecuteGeneratorBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.args_label.sizePolicy().hasHeightForWidth())
        self.args_label.setSizePolicy(sizePolicy)
        self.args_label.setMinimumSize(QtCore.QSize(80, 0))
        self.args_label.setObjectName("args_label")
        self.file_layout.addWidget(self.args_label)
        self.args = QtGui.QLineEdit(ExecuteGeneratorBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.args.sizePolicy().hasHeightForWidth())
        self.args.setSizePolicy(sizePolicy)
        self.args.setObjectName("args")
        self.file_layout.addWidget(self.args)
        self.verticalLayout.addLayout(self.file_layout)
        self.stdincmd_label = QtGui.QLabel(ExecuteGeneratorBox)
        self.stdincmd_label.setObjectName("stdincmd_label")
        self.verticalLayout.addWidget(self.stdincmd_label)
        self.stdincmd = QtGui.QTextEdit(ExecuteGeneratorBox)
        self.stdincmd.setObjectName("stdincmd")
        self.verticalLayout.addWidget(self.stdincmd)

        self.retranslateUi(ExecuteGeneratorBox)
        QtCore.QMetaObject.connectSlotsByName(ExecuteGeneratorBox)

    def retranslateUi(self, ExecuteGeneratorBox):
        ExecuteGeneratorBox.setWindowTitle(QtGui.QApplication.translate("ExecuteGeneratorBox", "Executor", None, QtGui.QApplication.UnicodeUTF8))
        ExecuteGeneratorBox.setTitle(QtGui.QApplication.translate("ExecuteGeneratorBox", "Job Information", None, QtGui.QApplication.UnicodeUTF8))
        self.executable_label.setText(QtGui.QApplication.translate("ExecuteGeneratorBox", "Executable", None, QtGui.QApplication.UnicodeUTF8))
        self.executable.setToolTip(QtGui.QApplication.translate("ExecuteGeneratorBox", "The path to the program to execute.", None, QtGui.QApplication.UnicodeUTF8))
        self.args_label.setText(QtGui.QApplication.translate("ExecuteGeneratorBox", "Arguments", None, QtGui.QApplication.UnicodeUTF8))
        self.args.setToolTip(QtGui.QApplication.translate("ExecuteGeneratorBox", "Optional arguments. You can substitute any key of the context like -file {job.file}", None, QtGui.QApplication.UnicodeUTF8))
        self.stdincmd_label.setText(QtGui.QApplication.translate("ExecuteGeneratorBox", "Standard Input", None, QtGui.QApplication.UnicodeUTF8))
        self.stdincmd.setToolTip(QtGui.QApplication.translate("ExecuteGeneratorBox", "An optional command to pipe into the program via stdin. {job.file} would be substituted to the actual file to process.", None, QtGui.QApplication.UnicodeUTF8))


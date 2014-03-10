#-*-coding:utf-8-*-
"""
@package bcore.gui.cmd
@brief A base class for simplifying qt gui applications 

@copyright 2013 Sebastian Thiel
"""
__all__ = ['PySideGUICommandBase']

import sys

from bcore.cmd import CommandBase

import bcore
from PySide import QtGui


class PySideGUICommandBase(CommandBase):
    """A command to initialize the pipeline context and setup a QApplication
    
    @note SubClasses must implement execute()  
    """
    __slots__ = ()

    
    def _init_qt(self):
        """Initialize a qt application object
        @return newly initialized object"""
        # NOTE: for now we ignore the actual args
        pinfo = new_service(bcore.IPostLaunchProcessInformation)
        return QtGui.QApplication([str(pinfo.executable())], QtGui.QApplication.Type.GuiClient)
    
    def execute(self, args, remaining_args):
        """Subclasses must implement this method and intialize and show their widgets.
        They should return SUCCESS if their setup succeeded, which will trigger the base implementation
        to enter the QApplication's main loop.
        If the return value indicates no success, the command will terminate with it accordingly.
        """
        raise NotImplementedError("To be implemnted by subclass")
        
    @classmethod
    def main(cls):
        """brief docs"""
        inst = cls()
        app = inst._init_qt()
        code = inst.parse_and_execute()
        
        # if the execution fails for some reason, don't bother running the event loop
        if code == cls.SUCCESS:
            code = app.exec_()
        # end handle rval
        sys.exit(code)
    

# end class PySideGUICommandBase

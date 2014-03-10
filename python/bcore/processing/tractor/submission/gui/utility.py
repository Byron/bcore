#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.submission.gui.utiliy
@brief Some utility types

@copyright 2013 Sebastian Thiel
"""
__all__ = ['TractorSubmitoolGUICommand', 'TractorSubmissionWindow']


from PySide import QtGui
from bcore.gui.cmd import PySideGUICommandBase
from .window_ui import Ui_SubmitoolWindow
from bcore.path import Path

class TractorSubmissionWindow(QtGui.QMainWindow):
    """A main window for tractor submission, using a TractorSubmissionController automatically"""
    
    def __init__(self, *args):
        """Initialize this instance"""
        super(TractorSubmissionWindow, self).__init__(*args)
        self.ui = Ui_SubmitoolWindow()
        self.ui.setupUi(self)
        self.setCentralWidget(self.ui.controller)
        # for now we don't need it
        self.setStatusBar(None)
        # Make sure we react
        self.ui.controller.shutdown.connect(self.close)
        
    # -------------------------
    ## @name Interface
    # @{
    
    def init(self, *args, **kwargs):
        """Initialize the controller
        @return this instance
        @note convenience method"""
        self.controller().init(*args, **kwargs)
        self.setWindowTitle(self.ui.controller.windowTitle())
        return self
        
    def controller(self):
        """@return our Controller widget, which is the main widget in the window
        @note you must initialize it exactly once"""
        return self.centralWidget()
        
    ## -- End Interface -- @}

# end class TractorSubmissionWindow


class TractorSubmitoolGUICommand(PySideGUICommandBase):
    """A command to launch the tractor submission gui. We inherit all information from our respective proxy
    command"""
    __slots__ = ('gui')
    
    name = 'submitool-gui'
    version = '0.1.0'
    description = "Launch a GUI for job submission"
    
    def setup_argparser(self, parser):
        parser.add_argument('file', nargs='*', default=list(), type=Path,
                             help='a list of files you want to process in one job')
    
    def execute(self, args, remainin_args):
        """Initialize our GUI"""
        self.gui = TractorSubmissionWindow().init(initial_file_list=args.file)
        self.gui.show()
        return self.SUCCESS

# end class TractorSubmitoolGUICommand


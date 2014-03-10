#-*-coding:utf-8-*-
"""
@package bcore.gui.hub.cmd
@brief Misc utilities related to the hub

@copyright 2013 Sebastian Thiel
"""
__all__ = ['HubGUICommand']


from bcore.gui.cmd import PySideGUICommandBase
from .controller import HubController


class HubGUICommand(PySideGUICommandBase):
    """A command to launch the dashboard"""
    __slots__ = ('gui')
    
    name = 'dashboard-gui'
    version = '0.1.0'
    description = "Launch the dashboard"
    
    def execute(self, args, remainin_args):
        """Initialize our GUI"""
        self.gui = HubController().init()
        self.gui.show()
        return self.SUCCESS

# end class HubGUICommand



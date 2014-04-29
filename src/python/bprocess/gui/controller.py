#-*-coding:utf-8-*-
"""
@package bprocess.gui.controller
@brief Contains package controllers, implementing some logic

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['PackageViewerWindow']
import logging

from PySide import QtGui

import bapp

from bapp.gui.hub.interfaces import IHubPanel
from ..utility import PackageMetaDataChangeTracker
from ..delegates import ControlledProcessInformation

from .controller_ui import Ui_PackageViewerWindow

log = logging.getLogger('bprocess.gui.controller')


class PackageViewerWindow(QtGui.QWidget, IHubPanel):
    """A simple widget to display information about a given package name
    It serves as convenience layer in case you just want to display packages.
    @note it is designed to be its own window !"""
    
    def __init__(self, *args):
        super(PackageViewerWindow, self).__init__(*args)
        self.ui = Ui_PackageViewerWindow()
        self.ui.setupUi(self)
        self._tracker = None
    
    # -------------------------
    ## @name Interface
    # @{
    
    def init(self, package_name_or_tracker = None, changes_only = False):
        """Initialize this instance with package information
        @param package_name_or_tracker if None, it will default to the name of the currently active application (if it is wrapped)
        If tracker, the it will be used right away
        @param changes_only if False, all package data will be shown
        @return this instance"""
        if package_name_or_tracker is None:
            svc = ControlledProcessInformation()
            if not svc.has_data():
                self.viewer().message.setText("Process is not wrapped, no package information available")
                return self
            #end deal with no-wrap 
            package_name_or_tracker = svc.process_data().id 
        # end handle package name
        
        assert package_name_or_tracker is not None, "should have name by now"
        tracker = package_name_or_tracker
        if not isinstance(tracker, PackageMetaDataChangeTracker):
            tracker = PackageMetaDataChangeTracker(package_name_or_tracker)
        #end handle tracker
        
        # store for later
        self._tracker = tracker
        self.viewer().set_tracker(tracker, changes_only = changes_only)
        return self
        
    def tracker(self):
        """@return package meta data tracker used to initialize the viewer"""
        return self._tracker
        
    
    def viewer(self):
        """@return our viewer directly, see PackageViewerWidget"""
        return self.ui.viewer
        
    
    ## -- End Interface -- @}

# end class PackageWidget

bapp.main().context().register(PackageViewerWindow)


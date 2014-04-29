#-*-coding:utf-8-*-
"""
@package bprocess.gui.viewer
@brief A widget to visualize the package structure

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['PackageWidget', 'PackageViewerWidget']

import logging
from PySide import (
                        QtCore, 
                        QtGui
                   )

import bapp
from .ui import (
                    Ui_PackageFrame,
                    Ui_PackageViewerWidget,
                )
from bapp.gui import remove_widget_children
from butility import capitalize

log = logging.getLogger('bprocess.gui.viewer')


class PackageWidget(QtGui.QFrame):
    """A simple widget which represents a single package, providing a few convenience functions 
    useful for the viewer
    
    It can also display information about the previously seen version of a package.
    """

    def __init__(self, *args):
        super(PackageWidget, self).__init__(*args)
        self.ui = Ui_PackageFrame()
        self.ui.setupUi(self)
        # Url to be visited when button is clicked
        self._url = None
        self.ui.help.released.connect(self._on_help_release)
        self.ui.description_group.setHidden(True)
        
    # -------------------------
    ## @name Slots
    # @{
    
    def _on_help_release(self):
        """Show docs """
        assert self._url, "expected to have url already"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self._url))
    
    ## -- End Slots -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def set_package(self, name, data, previous_data = None):
        """Set the widget to display information based on the given package data, which must match
        the schema of the PackageMetaDataChangeTracker
        @param name package name
        @param data package scheme compliant data of the current package state
        @param previous_data similar to data, but the last values we have seen, and only those who have changed
        @return self"""
        self.ui.package_label.setText("<b>%s@%s</b>" % (capitalize(data.name or name), data.version))
        self.ui.help.setVisible(bool(data.url))
        self.ui.version_previous.setHidden(True)
        self._url = data.url
        self.ui.description.setText(data.description)
        self.ui.description_group.setVisible(bool(data.description))
        
        if previous_data:
            # anything could have changed, make sure it is the version indeed
            if previous_data.version != data.version:
                self.ui.version_previous.setHidden(False)
                self.ui.version_previous.setText("Previous Version: %s" % str(previous_data.version))
            # end handle version change
        # end handle version
        
        return self
    
    ## -- End Interface -- @}

# end class PackageWidget


class PackageViewerWidget(QtGui.QWidget):
    """A controller showing a multitude of PackageWidgets, based on some context
    
    This GUI has three areas, one is for Changed Packages, for new packages, the other one for all packages
    that a root package depends on. Both will only ever show information related to a single root package, 
    which can be changed on the fly
    
    It is possible to display both individually
    """

    def __init__(self, *args):
        super(PackageViewerWidget, self).__init__(*args)
        self.ui = Ui_PackageViewerWidget()
        self.ui.setupUi(self)
        self.reset()
        
        
    def _update_packages(self, widget, packages, previous_packages = None, may_create = lambda name: True):
        """Update the contents of the given widget to contain one widget per package
        @param widget the QGroupWidget to fill with entries
        @param packages a dict of package-name => package_data entries
        @param previous_packages A dict of the previous state of all packages, format is similar to 'packages'
        @param may_create if True, the widget for the package with the given name may be created
        @note for now we are lazy and don't reuse widgets"""
        previous_packages = previous_packages or dict()
        for name, data in packages.iteritems():
            if not may_create(name):
                continue
            # end handle predicate
            widget.layout().addWidget(PackageWidget(self).set_package(name, data, previous_packages.get(name)))
        # end for each package
        
    # -------------------------
    ## @name Slots
    # @{
    
    def reset(self):
        """Clear the widget and make sure it doesn't display anything"""
        for widget in (self.ui.pall, self.ui.pchanged, self.ui.pnew, self.ui.premoved):
            widget.setHidden(True)
        # end for each widget to hide
        self.ui.message.setVisible(True)
    
    def set_tracker(self, tracker, changes_only = False):
        """Initialize this instance with the package tracker to visualize
        @param tracker a PackageMetaDataChangeTracker instance
        @param changes_only if True, only changed packages will be shown, not all the tracked packages
        @return self"""
        self.reset()
        
        changes = tracker.changes()
        
        packages = dict(((name, data) for data, name in tracker.iter_package_data()))
        previous_packages = dict(((name, data) for data, name in tracker.iter_package_data(previous=True)))
        
        hide_message = lambda: self.ui.message.setVisible(False)
        
        if not changes and not packages:
            log.warn("Input tracker was empty")
            return self
        # end bail out if there is nothing to display
        
        if changes:
            hide_message()
             
            # new packages
            added = set(packages.keys()) - set(previous_packages.keys())
            self.ui.pnew.setVisible(bool(added))
            self._update_packages(self.ui.pnew, packages, previous_packages, lambda name: name in added)
            
            # removed packges
            removed = set(previous_packages.keys()) - set(packages.keys())
            self.ui.premoved.setVisible(bool(removed))
            self._update_packages(self.ui.premoved, previous_packages, packages, lambda name: name in removed)
            
            # remaining packages
            remaining = set(changes.packages.keys()) - added
            self.ui.pchanged.setVisible(bool(remaining))
            self._update_packages(self.ui.pchanged, packages, previous_packages, lambda name: name in remaining)
        # end handle gui
        
        if changes_only:
            return self
        # end bail out if there where changes
        
        # fill in all packages
        hide_message()
        self.ui.pall.setVisible(True)
        self.ui.pall.setTitle("%s Packages" % capitalize(tracker.package_name()))
        self._update_packages(self.ui.pall, packages)
        
    ## -- End Slots -- @}
    
# end class PackageViewerWidget



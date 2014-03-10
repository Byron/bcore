#-*-coding:utf-8-*-
"""
@package bcore.gui.widgets.plugin_selector
@brief Contains a widget to help selecting plugins providing a certain interface

@copyright 2013 Sebastian Thiel
"""
__all__ = ['PluginSelectorWidget']

from PySide import (
                        QtGui,
                        QtCore,
                    )
from . import ui


class PluginSelectorWidget(QtGui.QWidget):
    """A simple selector for a list of instances which are derived from the Plugin type. 
    
    The main benefit is that you can receive selection_changed signals with your actual instance, 
    instead of just a string or index in case of a standard combo-box.
    
    @note at some point this widget might evolve into something more complex than a combobox
    """
    
    def __init__(self, *args):
        """Initialize this instance"""
        super(PluginSelectorWidget, self).__init__(*args)
        self._plugins = list()
        self.ui = ui.Ui_SelectorWidget()
        self.ui.setupUi(self)
        self.ui.plugins.currentIndexChanged.connect(self._on_current_index_change)
        
        
    # -------------------------
    ## @name Signals
    # @{
    
    ## Emitted with the currently selected object if it changes, or None if there is no selection
    selection_changed = QtCore.Signal(object)
    
    ## Emitted with the new currently selected generator, after the selection changed
    
    ## -- End Signals -- @}
    
    # -------------------------
    ## @name Slots
    # @{
    
    def _on_current_index_change(self, index):
        """Convert into our own signal"""
        self.selection_changed.emit(self.selected())
    
    ## -- End Slots -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def plugins(self):
        """@return a list of all currently available plugin instances"""
        return self._plugins
    
    def selected(self):
        """@return the currently selected plugin, or None if nothing is selected"""
        if not self._plugins:
            return None
        return self.ui.plugins.itemData(self.ui.plugins.currentIndex(), QtCore.Qt.UserRole)
        
    def set_plugins(self, plugins):
        """Set the given list of plugin instance to be displayed in the widget
        @param plugins a list of 
        @return this instance"""
        self._plugins = plugins
        for plugin in plugins:
            self.ui.plugins.addItem(plugin.plugin_name(), plugin)
        # end for each 
        return self
        
    ## -- End Interface -- @}

# end class PluginSelectorWidget

#-*-coding:utf-8-*-
"""
@package bcore.gui.hub.interfaces
@brief A collection of interfaces to help using and customizing the hub

@copyright 2013 Sebastian Thiel
"""
__all__ = ['IHubPanel']

import bcore

class IHubPanel(object):
    """Implemented by widgets which can be shown as Hub-Panel
    
    @note A panel is much like a plugin-widget, and its to be defined what we need exactly, and if it
    should be named like this
    @note must be a PySide widget currently
    @note cannot be derived from our InterfaceBase as there is a metaclass layout conflict
    """
    __slots__ = ()
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    @bcore.abstractmethod
    def init(self):
        """Will be called after the widget was instantiated, and will cause it to initialize itself
        @return this instance"""
    
    ## -- End Interface -- @}

# end class HubDockWidget

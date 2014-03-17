#-*-coding:utf-8-*-
"""
@package bcore.log.interfaces
@brief Contains interfaces related to logging

@copyright 2013 Sebastian Thiel
"""
__all__ = ['ILog']

import bcore

class ILog(bcore.InterfaceBase):
    """Provides logger instances for use by everyon using the core framework"""
    __slots__ = ()
    
    # -------------------------
    ## @name Interface
    # @{
    
    @bcore.abstractmethod
    def new(self, name):
        """@return a logger initialized and suitable for use by the given module or class
        @param name a dot-separated module name, like 'bcore.yourmodule', or bcore.MyClass
        @note loggers form a tree which can be configured hierarchically"""
    
    ## -- End Interface -- @}

# end class ILog

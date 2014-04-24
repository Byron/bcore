#-*-coding:utf-8-*-
"""
@package bprocess.app
@brief Contains a Process aware Application implementation

@copyright 2014 Sebastian Thiel
"""
__all__ = ['ProcessAwareApplication']

import bapp

from .delegates import ControlledProcessInformation
from .utility import (ControlledProcessContext,
                      PythonPackageIterator )


class ProcessAwareApplication(bapp.Application):
    """An application type which ignores all configuration, and initialized the application context 
    by loading it from the context previously saved by the bootstrapper.

    It should always be used if your application can be wrapped, which is probably True for most of them.
    """
    __slots__ = ()

    @classmethod
    def new(cls, *args, **kwargs):
        """Restore the previously created context as stored in the process environment
        If this is not a process setup by ProcessControl, the default Application implementation is used 
        automatically. This means that generally, you should use this implementation in order to support
        everything.
        Relevant keys are only 'load_plugins', which is True by default, and setup_logging, which is True as well
        @return a new application instance"""
        proc_env = ControlledProcessContext()
        if not proc_env.has_data():
            return super(ProcessAwareApplication, cls).new(*args, **kwargs)
        # end handle no process control

        inst = cls._init_instance()
        inst.context().push(proc_env)

        if kwargs.get('setup_logging', True):
            cls.LogConfiguratorType.initialize()
        # end handle logging setup

        if kwargs.get('load_plugins', True):
            PythonPackageIterator().import_modules()
        # end handle plugin loading

        return inst

    # -------------------------
    ## @name Interface
    # @{

    @classmethod
    def process_information(cls):
        """@return an instance providing the IControlledProcessInformation interface. Use it to learn 
        about the way you where started.
        @note just a convenience method, which should help to raise awareness of the different kinds of
        applications we have.
        """
        return ControlledProcessInformation()
    
    ## -- End Interface -- @}

# end class ProcessAwareApplication

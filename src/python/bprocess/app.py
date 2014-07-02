#-*-coding:utf-8-*-
"""
@package bprocess.app
@brief Contains a Process aware Application implementation

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = ['ProcessAwareApplication']

import bapp

from .utility import (ControlledProcessContext,
                      ControlledProcessInformation,
                      PythonPackageIterator )

from bcontext import HierarchicalContext


class ProcessAwareApplication(bapp.Application):
    """An application type which ignores all configuration, and initialized the application context 
    by loading it from the context previously saved by the bootstrapper.

    It should always be used if your application can be wrapped, which is probably True for most of them.
    """
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{

    ## The type to use a ControlledProcessContext
    ControlledProcessContextType = ControlledProcessContext
    
    ## -- End Configuration -- @}

    @classmethod
    def new(cls, *args, **kwargs):
        """Restore the previously created context as stored in the process environment
        If this is not a process setup by ProcessControl, the default Application implementation is used 
        automatically. This means that generally, you should use this implementation in order to support
        everything.
        Relevant keys are only 'load_plugins_from_settings', which is True by default, and setup_logging, which 
        is True as well
        'load_plugins_from_settings' will traverse all the python.* statements in our package configuration and
        
        @return a new application instance"""
        # NOTE: you have to take off all custom options right here
        load_plugins_from_settings = kwargs.pop('load_plugins_from_settings', True)
        if not ControlledProcessInformation.has_data():
            return super(ProcessAwareApplication, cls).new(*args, **kwargs)
        # end handle no process control

        inst = cls._init_instance()
        proc_ctx = cls.ControlledProcessContextType(inst)
        inst.context().push(proc_ctx)

        if kwargs.get('setup_logging', True):
            cls.LogConfiguratorType.initialize()
        # end handle logging setup

        # We also have to load plug-ins from the plug-ins directory, as this would usually be done by each context
        if kwargs.get('load_plugins_from_trees', False):
            # At this stage, we only have this information in hash_maps, and of course the traditional contexts
            lpkwargs = dict( recurse     =kwargs.get('recursive_plugin_loading', False),
                             subdirectory=kwargs.get('plugins_subtree', 'plug-ins') )
            proc_ctx.load_plugins(**lpkwargs)
            
            # We just load these as we 
            for ctx in inst.context().stack():
                if isinstance(ctx, HierarchicalContext):
                    ctx.load_plugins(**lpkwargs)
            # end for each context from which to load plugins
        # end load plug-ins directories

        if load_plugins_from_settings:
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

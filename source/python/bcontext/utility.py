#-*-coding:utf-8-*-
"""
@package bcontext.plugin
@brief Implementation of utility types for registering plugins

@copyright 2014 Sebastian Thiel
"""
__all__ = ['PluginMeta', 'PluginLoader', 'Plugin', 'ContextStackClient']

import imp
import os
import sys
import re
import logging

from butility import MetaBase

log = logging.getLogger(__name__)


# ==============================================================================
## @name Plugin Hanlding
# ------------------------------------------------------------------------------
# Convenience facilities to help writing plugins and interfaces for easy use the ContextStack
## @{


# inherits from InterfaceMeta to support inheritance in the implements() function
class PluginMeta(MetaBase):
    """ metaclass for Plugin, registers the Plugin subclass in the currently set
        Context. Can be used with any type, doesn't need to derive from Plugin.
        However, the Plugin implementation will register instances, which the implementor would have to 
        do by himself otherwise."""
        
    ## See Plugin._stack
    _stack = None

    def __new__(mcls, name, bases, clsdict):
        """Registers the plugin's type to allow it to be instantiated""" 
        new_type = MetaBase.__new__(mcls, name, bases, clsdict)
        if name != 'Plugin' and hasattr(new_type, '_auto_register_class') and new_type._auto_register_class:
            assert mcls._stack, 'ContextStack must be set in PluginMeta for it to work'
            mcls._stack.register(new_type)
        # end exclude our own plugin marker (when type is instantated)
        return new_type
        

# end class PluginMeta

# Careful about renames: name is used verbatim in code above !
class Plugin(object):
    """ base class for all Plugins implementing interfaces"""
    __metaclass__ = PluginMeta
    __slots__ = tuple()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## ContextStack to use when handling service registration
    # Will default to the context of our metaclass if unset
    _stack = None
    
    ## If True, new instances will automatically register themselves with the current Context
    _auto_register_instance = True
    
    ## If True, any subclass of this type will be registered automatically with the current Context
    _auto_register_class = True
    
    ## -- End Configuration -- @}
    
    
    def __new__(cls, *args, **kwargs):
        """ overloaded class creator, registers the instance in the current
            Context for all our instances """
        self = super(Plugin, cls).__new__(cls)
        if cls._auto_register_instance:
            stack = cls._stack or cls.__metaclass__._stack
            assert stack, "ContextStack must be set in Plugin type"
            stack.register(self)
        # end handle registration
        return self
        
        
    # -------------------------
    ## @name Interface
    # @{
    
    ## Subclasses can set this variable to easily set their plugin name, which can be used for GUI purposes
    _plugin_name = None
    
    @classmethod
    def plugin_name(cls):
        """@return the name of the Plugin
        @note by default, we just create a name from the name of the class, unless _plugin_name is 
        set as member variable"""
        return cls._plugin_name or cls.__name__
    
    ## -- End Interface -- @}

# end class Plugin


class PluginLoader(object):
    """ loads .py files from a given directory or load the given file, with recursion if desired
        @note it just loads the .py files"""
    __slots__ = (
                '_path',   # path at which to load plugins 
                '_recurse' # search for loadable plugins will be performed recursively
                )
        
    def __init__(self, path, recurse=False):
        self._path    = Path(path)
        self._recurse = recurse

    def _load_files(self, path, files):
        """ load all python \a files from \a path 
        @return list of loaded files as full paths"""
        res = list()
        def py_filter(f):
            return filename.endswith('.py') and not \
                   filename.startswith('__')
        # end filter

        for filename in filter(py_filter, files):
            py_file = os.sep.join([path, filename])
            (mod_name, _) = os.path.splitext(os.path.basename(py_file))
            try:
                self.load_file(py_file, mod_name)
            except Exception:
                # TODO: fix the logger issue, traceback shouldn't be required
                import traceback
                traceback.print_exc()
                log.error("Failed to load %s from %s", mod_name, py_file, exc_info=True)
            else:
                log.info("loaded %s into module %s", py_file, mod_name)
                res.append(py_file)
            # end handle result
        # end for eahc file to load
        return res

    def load(self):
        """ perform the actual loading
        @return a list of files loaded successfully"""
        # if we should recurse, we just use the standard dirwalk.
        # we use topdown so top directories should be loaded before their
        # subdirectories and we follow symlinks, since it seems likely that's
        # what people will expect
        res = list()
        if self._path.isfile():
            res += self._load_files(self._path.dirname(), [self._path.basename()])
        else:
            for path, dirs, files in os.walk(self._path, topdown=True, followlinks=True):
                res += self._load_files(path, files)
                if not self._recurse:
                    break
                # end handle recursion
            # end for each directory to walk
        # end handle file or directory
        return res
        
    @classmethod
    def load_file(cls, python_file, module_name):
        """Load the contents of the given python file into a module of the given name.
        If the module is already loaded, it will be reloaded
        @return the loaded module object
        @throws Exception any exception raised when trying to load the module"""
        imp.load_source(module_name, python_file)
        return sys.modules[module_name]
        
# end class PluginLoader

## -- End Plugin Handling -- @}

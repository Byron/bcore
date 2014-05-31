#-*-coding:utf-8-*-
"""
@package bcontext.utility
@brief Implementation of utility types for registering plugins

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals

from minifuture import with_metaclass
__all__ = ['PluginMeta', 'Plugin']

from itertools import chain

from butility import Meta


# ==============================================================================
## @name Plugin Handling
# ------------------------------------------------------------------------------
# Convenience facilities to help writing plugins and interfaces for easy use the ContextStack
## @{


# inherits from InterfaceMeta to support inheritance in the implements() function
class PluginMeta(Meta):
    """ metaclass for Plugin, registers the Plugin subclass in the currently set
        Context. Can be used with any type, doesn't need to derive from Plugin.
        However, the Plugin implementation will register instances, which the implementor would have to 
        do by himself otherwise."""
        
    def __new__(mcls, name, bases, clsdict):
        """Registers the plugin's type to allow it to be instantiated""" 
        new_type = Meta.__new__(mcls, name, bases, clsdict)
        original_plugin_type = globals().get('Plugin')

        if original_plugin_type is not None and hasattr(new_type, '_auto_register_class_') and new_type._auto_register_class_:
            # at this point, we are already treating some Plugin subclass
            plugin_base = None
            for typ in chain(*(base.mro() for base in bases)):
                if issubclass(typ, original_plugin_type):
                    plugin_base = typ
                    break
                # end obtain Plugin
            # end for each base of type Plugin
            assert plugin_base, "Didn't find a single base of type Plugin, this MetaClass must not be used alone"
            # We assume someone overrides Plugin and implements the one method that needs implementation.
            # Therefore, direct Plugin bases are assumed to be the base of the type we would be interested in
            # Which also shouldn't ever get into the registry
            if original_plugin_type is not plugin_base:
                plugin_base._stack().register(new_type)
            # end handle type registration
        # end handle Plugin instantiation

        return new_type
        # end check 
        
# end class PluginMeta

# Careful about renames: name is used verbatim in code above !
class Plugin(with_metaclass(PluginMeta, object)):
    """ base class for all Plugins implementing interfaces"""
    
    # -------------------------
    ## @name Configuration
    # @{

    ## A ContextStack instance to use to register new types and instances.
    # Must be set in subclass
    _stack_ = None
    
    ## If True, new instances will automatically register themselves with the current Context
    _auto_register_instance_ = True
    
    ## If True, any subclass of this type will be registered automatically with the current Context
    _auto_register_class_ = True
    
    ## -- End Configuration -- @}
    
    
    def __new__(cls, *args, **kwargs):
        """ overloaded class creator, registers the instance in the current
            Context for all our instances """
        self = super(Plugin, cls).__new__(cls)
        if cls._auto_register_instance_:
            cls._stack().register(self)
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

    # -------------------------
    ## @name Subclass Interface
    # @{

    @classmethod
    def _stack(cls):
        """@return our current context stack. By default, we will return our own class member _stack_, which 
        must not be None"""
        assert cls._stack_, "Subclass should have set _stack_ variable, or have overridden this method"
        return cls._stack_
        
    
    ## -- End Subclass Interface -- @}

# end class Plugin

## -- End Plugin Handling -- @}

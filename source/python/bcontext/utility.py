#-*-coding:utf-8-*-
"""
@package bcontext.utility
@brief Implementation of utility types for registering plugins

@copyright 2014 Sebastian Thiel
"""
__all__ = ['PluginMeta', 'Plugin']

from butility import MetaBase



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
            assert mcls._stack, 'ContextStack must be set in %s for it to work' % mcls.__name__
            mcls._stack.register(new_type)
        # end exclude our own plugin marker (when type is instantated)
        return new_type
        # end check 
        
    # -------------------------
    ## @name Interface
    # @{

    @classmethod
    def new(self, stack):
        """@return a new \a Plugin type which uses the given stack for registering instances.
        Additionally, it will use a custom metaclass that uses the stack as well for registering new types
        @param stack a context stack instance. It will be used to auto-register new types and instances
        @todo this method might want to move to BApplication, or similar"""
        prefix = 'CustomStack'
        clsdict = {'_stack' : stack}
        meta_class_type = MetaBase.__new__(MetaBase, prefix + 'PluginMeta', (PluginMeta,), clsdict)

        clsdict['__metaclass__'] = meta_class_type
        plugin_type = meta_class_type.__new__(meta_class_type, prefix + 'Plugin', (Plugin,), clsdict)

        return plugin_type
        
    ## -- End Interface -- @}
        

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

## -- End Plugin Handling -- @}

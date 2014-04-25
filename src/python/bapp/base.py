#-*-coding:utf-8-*-
"""
@package bapp.base
@brief Implements the Application type

@copyright 2014 Sebastian Thiel
"""
__all__ = ['Application', 'TypeNotFound', 'InstanceNotFound']

from itertools import chain

from bcontext import (ContextStack,
                      Context)

from .utility import (LogConfigurator,
                      StackAwareHierarchicalContext)

import bcontext




# -------------------------
## @name Exceptions
# @{

class TypeNotFound(ValueError):
    """Thrown if a type cannot be found in the context"""
    __slots__ = ()

# end class TypeNotFound


class InstanceNotFound(TypeNotFound):
    """Thrown if a requested instance could not be found in the context"""
    __slots__ = ()

# end class InstanceNotFound

## -- End Exceptions -- @}


class Application(object):
    """An application contains all state for a particular application.

    Even though it is valid to have multiple instances in one process, the first created Application instance
    will be the one representing the process itself.

    Therefore, general purpose code is allowed to use facilities provided by the main application instance, 
    without knowing or caring who created it.

    * hold application interfaces
    * keep ContextStack to allow easy access to settings and plugin/type registry
    * setup logging mechanism

    The common way of using this type is to instantiate one during application startup.

    @note by itself, the Application is not a singleton, but can be used as such. For that reason, the 'bapp'
    is taking care of instantiating them, keeping the first as the 'global' one.
    """
    # slots just used as documentation to make instance-overrides of class members work
    # __slots__ = ('_stack',  # A ContextStack instance
    #            'Plugin'   # An instance level Plugin type, returning our own stack
    #             )


    # -------------------------
    ## @name Constants
    # @{

    ## A variable to keep the first created Application instance, see Application.new()
    ## The very same instance will be placed in bapp.app
    main = None
    
    ## -- End Constants -- @}

    # -------------------------
    ## @name Subclass Configuration
    # Variables for overrides by subclasses
    # @{

    ## Type used when building the ContextStack (settings, registry)
    HierarchicalContextType = StackAwareHierarchicalContext

    ## The name of the sub-directory to consider when loading plugins from all settings directories
    # May be None to load plugins from the settings directories directly
    plugins_subtree = 'plug-ins'

    ## The kind of Plugin we use
    PluginType = bcontext.Plugin

    ## The type of ContextStack we create
    ContextStackType = ContextStack

    ## A utility to setup the logging system
    LogConfiguratorType = LogConfigurator

    ## The default OS context type
    # Lazliy imported, but may be overridden by subclass
    OSContextType = None

    ## The default application context type
    # See above
    ApplicationContextType = None

    
    ## -- End Subclass Configuration -- @}

    # -------------------------
    ## @name Types
    # @{

    class Plugin(PluginType):
        """This is an intermediat Plugin type implementation which may be used by code 
        which is run even though there is no Application yet.
        Instead of dealing with this directly, you should use bapp.plugin_type()"""
        __slots__ = ()

        default_stack = ContextStack()

        @classmethod
        def _stack(cls):
            # NOTE: Should we better keep a ref the the actual stack ? Would be better, and means
            # each Application instance has it's own PluginType. It could just set a type variables
            # and the base implementation returns it.
            # Then this implementation could keep its own catch-all stack which is later merged
            # by us if present.
            # Each Application instance will just set a respective instance variable with the custom type
            if Application.main is None:
                if len(cls.default_stack) == 1:
                    cls.default_stack.push("early-startup-intermediary")
                # end create first user-controlled context
                return cls.default_stack
            # end handle default stack
            return Application.main.context()
    
    # end class Plugin

    ## -- End Types -- @}

    def __init__(self, context_stack):
        """Initialize this instance with it's own context stack"""
        # If our type's Plugin's default stack still has anything in its registry, put it onto our stack.
        # It came first, and should thus be first. 
        def_stack = type(self).Plugin.default_stack
        if len(def_stack) > 1:
            prev_contexts = def_stack.pop(until_size=1)
            cur_contexts = context_stack.pop(until_size=1)
            for ctx in chain(prev_contexts, cur_contexts):
                assert not ctx.settings().data(), "Settings of context should be unset"
                context_stack.push(ctx)
            # end handle context merge
        # end bring in latest items

        self._stack = context_stack
        self.Plugin = self.PluginType.__metaclass__.__new__(self.PluginType.__metaclass__,
                                                            'ApplicationPlugin', 
                                                           (self.PluginType,), 
                                                           dict(_stack_ = context_stack))


    # -------------------------
    ## @name Subclass Interface
    # @{

    @classmethod
    def _init_instance(cls):
        """Create a new instance, and set our main variable.
        Additionally, setup logging
        @return new instance of our type"""
        stack = cls.ContextStackType()
        inst = cls(stack)

        # We always set the current application to the global one. 
        # This will fail in multi-threaded application, but that is not supposed to work anyway
        # There should only be one application per process
        # NOTE: Doing this also means that someone creating a new application in the middle of a running application
        # will be default get rid of all registered plugin types.
        # NOTE: In case someone overrides our base Application, cls.main would assign not to our 
        # Application.main, but to a new class member in our derived class. This in turn 
        # Would break anyone relying on Application.main, which is not intended
        Application.main = inst
        # end set main only if we are the first

        return inst
        
    ## -- End Subclass Interface -- @}

    # -------------------------
    ## @name Interface
    # @{

    @classmethod
    def new(cls, settings_trees=tuple(), settings_hierarchy=False, 
                 load_plugins_from_trees = False, recursive_plugin_loading = False, plugins_subtree='plug-ins',
                 user_settings = True,
                 setup_logging = True,
                 with_default_contexts = True ):
        """Create a new Application instance, configured with all items an application needs to function.
        This is mainly a registry for settings, types and instances providing particular instances.

        Everything an application instance provides can also be used without it. However, it's main
        purpose is to serve as central stable point for general purpose code, which allows Application aware
        code to keep record of new types.

        @param settings_trees an iterable of butility.Path instances pointing to directories which should
        be searched for application settings.
        Settings are supposed to be stored in yaml files, which may have any name. As the search is non-recursive,
        settings must be located directly within the directory. This implies that yaml files unrelated to 
        application configuration should be placed underneath subdirectories.
        @param settings_hierarchy if True, default False, the entire parent hierarchy of each
        settings_search_path will be searched for configuration files too. By default, 'etc' directories will
        be considered a source for settings files.
        @param load_plugins_from_trees if True, plugins will be loaded from all plugin subdirectories. Each of them
        is expected in one of the valid configuration directories we are effectively using.
        This shouldn't be confused with configuring plugin load paths in the application settings, which is 
        another means of doing that. The difference is that the latter can't know the configuration files
        @param recursive_plugin_loading if True, plugins may reside in sub-folders and will be loaded anyway
        @param plugins_subtree the directory within each configuration directory which should be searched
        for plug-ins. That way, you can separate plug-ins from other code
        @param user_settings if True, user settings will be loaded from directory at user.config (within application settings)
        @param setup_logging if True, logging will be configured using the LogConfigurator, which in turn
        is setup using our context
        @param with_default_contexts if True, we will initialize an OSContext and an ApplicationContext
        @return a new Application instance
        @note in every program, the Application instance must be initialized before anything that uses the 
        default application is imported. Otherwise, types cannot be registered
        """
        inst = cls._init_instance()

        # This needs lazy import
        from .contexts import (OSContext, 
                               ApplicationContext)

        if with_default_contexts:
            typ = cls.OSContextType or OSContext
            inst.context().push(typ('os'))

            typ = cls.ApplicationContextType or ApplicationContext
            inst.context().push(typ('app', user_settings=user_settings))
        # end handle ApplicationContext

        for path in settings_trees:
            ctx = inst.context().push(cls.HierarchicalContextType(path,
                                                            traverse_settings_hierarchy=settings_hierarchy,
                                                            application=inst))
            if load_plugins_from_trees:
                ctx.load_plugins(recurse = recursive_plugin_loading,
                                 subdirectory = plugins_subtree)

        # end for each path to push

        if setup_logging:
            cls.LogConfiguratorType.initialize()
        # end handle log setup

        return inst

    def instance(self, interface, predicate = lambda service: True):
        """@return the first found instance implementing the given interface. 
        The instance is persistent and owned by the Application's context.
        @param interface a class/type, that the instance should support
        @param predicate f(instance) => Bool, returning True for each instance supporting interface that 
        should be returned
        @throws InstanceNotFound
        @note use this function assuming that you will receive a service, no checking necessary. 
        Of course using it that way is only possible if your code is in an application that may make such 
        assumptions. Otherwise, see Application.context().instances()"""
        instances = self.context().instances(interface, predicate = predicate)
        if not instances:
            raise InstanceNotFound(interface)
        # end handle no instance
        return instances[0]

    def new_instance(self, interface, *args, **kwargs):
        """@return a new instance owned by you which supports the given interface. You will receive
        an instance of a type most suitable for you based on it's position in the ContextStack.
        @param interface the new instance must implement
        @param args given to new instance
        @param kwargs given to new instance
        @throws InstanceNotFound"""
        new_instances = self.context().new_instances(interface, take_ownership=False, 
                                                     maycreate = lambda cls, instances: not instances,
                                                     args=args, kwargs=kwargs)
        if not new_instances:
            raise InstanceNotFound(interface)
        # end handle no instance
        return new_instances[0]
        
    def type(self, interface, predicate = lambda type: True):
        """@return a type which implements the given interface. You can use it to create a new instance
        @param interface which must be supported by the returned type
        @param predicate f(type) => Bool, returning True for each type which seems usable
        @throws TypeNotFound"""
        types = self.context().types(interface, predicate = predicate)
        if not types:
            raise TypeNotFound(interface)
        # end handle no type
        return types[0]

    def context(self):
        """@return our ContextStack instance"""
        return self._stack

    def settings(self):
        """A shortcut to context().settings()
        @return the KeyValueStoreProvider representing our settings"""
        return self.context().settings()
        

    ## -- End Interface -- @}
# end class Application

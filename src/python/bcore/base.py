#-*-coding:utf-8-*-
"""
@package bapplication.base
@brief Implements the Application type

@copyright 2014 Sebastian Thiel
"""
__all__ = ['Application']

from itertools import chain

from bcontext import (HierarchicalContext,
                      ContextStack,
                      Context)

import bcontext

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
    ## The very same instance will be placed in bcore.app
    main = None
    
    ## -- End Constants -- @}

    # -------------------------
    ## @name Subclass Configuration
    # Variables for overrides by subclasses
    # @{

    ## Type used when building the ContextStack (settings, registry)
    HierarchicalContextType = HierarchicalContext

    ## The name of the sub-directory to consider when loading plugins from all settings directories
    # May be None to load plugins from the settings directories directly
    plugins_subdirectory = 'plug-ins'

    ## The kind of Plugin we use
    PluginType = bcontext.Plugin

    ## The type of ContextStack we create
    ContextStackType = ContextStack
    
    ## -- End Subclass Configuration -- @}

    # -------------------------
    ## @name Types
    # @{

    class Plugin(PluginType):
        """An App-Aware Plugin which will retrieve the current application context when needed.
        It is only actually used by types which are  """
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
            if main is None:
                if len(cls.default_stack) == 1:
                    cls.default_stack.push("early-startup-intermediary")
                # end create first user-controlled context
                return cls.default_stack
            # end handle default stack
            return main.context()
    
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
            for ctx in chain(contexts, cur_contexts):
                context_stack.push(ctx)
            # end handle context merge
        # end bring in latest items

        self._stack = context_stack
        self.Plugin = self.PluginType.__metaclass__.__new__(self.PluginType.__metaclass__,
                                                            'ApplicationPlugin', 
                                                           (self.PluginType,), 
                                                           dict(_stack_ = context_stack))


    # -------------------------
    ## @name Interface
    # @{

    @classmethod
    def new(cls, settings_paths=tuple(), settings_hierarchy=False, 
                 load_plugins = True):
        """Create a new Application instance, configured with all items an application needs to function.
        This is mainly a registry for settings, types and instances providing particular instances.

        Everything an application instance provides can also be used without it. However, it's main
        purpose is to serve as central stable point for general purpose code, which allows Application aware
        code to keep record of new types.

        @param settings_paths an iterable of butility.Path instances pointing to directories which should
        be searched for application settings.
        Settings are supposed to be stored in yaml files, which may have any name. As the search is non-recursive,
        settings must be located directly within the directory. This implies that yaml files unrelated to 
        application configuration should be placed underneath subdirectories.
        @param settings_hierarchy if True, default False, the entire parent hierarchy of each
        settings_search_path will be searched for configuration files too. By default, 'etc' directories will
        be considered a source for settings files.
        @param load_plugins if True, plugins will be loaded from all plugins subdirectories
        @return a new Application instance
        @note in every program, the Application instance must be initialized before anything that uses the 
        default application is imported. Otherwise, types cannot be registered
        """
        stack = cls.ContextStackType()
        inst = cls(stack)
        # NOTE: should we have a default Application that will later be merged into anyone created by the user ?
        # Or should this be default behaviour ? Any existing app is merged into the new one ?
        # Could be undesirable, and can only be properly handled (in to catch types I believe)

        if cls.main is None:
            cls.main = inst
        # end set main only if we are the first

        return inst

    ## -- End Interface -- @}
# end class Application

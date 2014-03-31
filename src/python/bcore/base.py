#-*-coding:utf-8-*-
"""
@package bapplication.base
@brief Implements the Application type

@copyright 2014 Sebastian Thiel
"""
__all__ = ['Application']


from bcontext import (HierarchicalContext,
                      Context)

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
    __slots__ = ('_stack')


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
    HierarchicalContextType = HiearchicalContext

    ## The name of the directory to consider when loading plugins
    
    ## -- End Subclass Configuration -- @}


    # -------------------------
    ## @name Interface
    # @{

    @classmethod
    def new(cls, settings_paths=tuple(), settings_hierarchy=False, plugins_load = True):
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

        @return a new Application instance"""
        
    
    ## -- End Interface -- @}

    

    

# end class Application

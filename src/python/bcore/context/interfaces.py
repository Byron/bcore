# -*- coding: utf-8 -*-
"""
@package bcore.context.interfaces
@brief Most basic interfaces for general usage, useful in all host applications !

@copyright 2012 Sebastian Thiel
"""

__all__ = ['IHostApplication', 'IPlatformService', 'IContextController', 
           'IProjectService', 'IDirectoryService', 'ISiteService']

from butility import (InterfaceBase,
                      abstractmethod,
                      Error)


class IHostApplication(InterfaceBase):
    """ Host Application Interface with the standard functions
        we expect host applications to support """
        
    @abstractmethod
    def version(self):
        """@return a \ref bcore.Version "Version" instance, representing the host application version"""
        
    @abstractmethod
    def name(self):
        """@return string of name of host application"""
    
    @abstractmethod
    def quit(self, exit_code):
        """shutdown the host application
        @param exit_code a value from 0 to 255, 0 indicating no error"""

    @abstractmethod
    def load(self, filepath):
        """load a scene from filepath
        @return self"""

    @abstractmethod
    def save(self, filepath):
        """save the scene as filepath.
        Overwrite existing files without user intervention
        @return self"""
        
    @abstractmethod
    def loaded_file(self):
        """@return path to the currently loaded file or None if there is no loaded file"""
        
        
        
class IContextController(InterfaceBase):
    """A controller to deal with the context changes of a typical application.
    
    It deals with two kinds of context:
    
    - executable context
      + Each process is (usually) started using process control. In this case, we will set the context
        to contain information picked up from the executable path.
      + Part of static initialization/boot sequence
    - scene context
      + Each application is assumed to load a scene or file at some point. Before that happens, we must
        verify that this instance is using the right packages (see process control), e.g. the right versions 
        of plugins, before we change to the new scene. If its okay, we may proceed, otherwise the scene change
        should be aborted.
        
    @note If we talk about context, we mean the kvstore of the bcore.environment instance.
    @note This type is meant to be used as Singleton, and must be initialized once during your application's 
    boot sequence.
    """
    __slots__ = ()
    
    
    class ContextIncompatible(Error):
        """Indicate the new scene context is not compatible with the current one.
        If converted to string, a descriptive error message should be generated"""
        __slots__ = ()
    

    # end class ContextIncompatible

    
    # -------------------------
    ## @name Interface
    # @{
    
    @abstractmethod
    def init(self):
        """Should be used to initialize the executable context as well as callbacks to follow the scene context.
        @note must be called exactly once on a new instance, which should exist only once per application"""
        
    @abstractmethod
    def pop_scene_context(self):
        """Remove all environments pushed onto the stack if they belong to the scene context.
        
        @return list of popped environments in natural order
        @note its safe to call this method even if no scene context was previously pushed
        @note Should be called whenever the scene context is left undefined, for instance by entering 
        an unnamed scene"""
    
    ## -- End Interface -- @}
        
    # -------------------------
    ## @name Callbacks
    # @{
    
    @abstractmethod
    def change_scene_context(self, filepath):
        """Change our context from the previous one the to one indicated by the given file.
        
        If the context of the current scene is incompatible to the one we are about to change to (or have
        changed to), and execption of type 
        
        @note should be called by subclasses from their respective callbacks
        @param filepath butility.Path instance of filename to change the context to in one way or another
        @throws IContextController.ContextIncompatible
        """
        
    ## -- End Callbacks -- @}
        
        
# end class IContextController
        
    

class IPlatformService(InterfaceBase):
    """Interface for platform instances specific to operating systems"""
    
    # -------------------------
    ## @name Constants
    # @{
    
    ## the short canonical name of the platform
    ID_SHORT = "short"
    ## canonical name of platform including architecture and our compiler
    ID_FULL = "full"
    
    ## search path for dynamically loaded shared objects, dlls
    SEARCH_DYNLOAD = 'dynload'
    ## search path for executables
    SEARCH_EXECUTABLES = 'executable'
    ## -- End Constants -- @}
    
    # -------------------------
    ## @name Configuration
    # To be overridden by subclass
    # @{
    
    ## the name of the platform we're supporting
    platform = None
        
    ## -- End Configuration -- @}

    # -------------------------
    ## @name Interface
    # @{
    
    @abstractmethod
    def id(self, id_type = ID_SHORT):
        """@return a string id identifying the platform we are currently on
        @param id_type a constant of type ID_* to define the kind of id
        @throws ValueError if the passed id type is unknown"""

    @abstractmethod
    def search_path_variable(self, variable_type):
        """@return environment variable name for a search path of the given type
        @param variable_type one of the SEARCH_* constants to identify the kind of variable
        @throw ValueError if the passed it variable type is unknown"""

    ## -- End Interface -- @}
    
    
class IDirectoryService(InterfaceBase):
    """Provides information about the directory structure, and generally where to find things"""
    __slots__ = ()

    # -------------------------
    ## @name Interface
    # @{

    @abstractmethod
    def path(self, id):
        """@return a path matching a path ID as obtained by path_ids()
        @throws ValueError if the constant is unknown"""
    
    
    @abstractmethod
    def path_ids(self):
        """@return a list of all valid path ids"""
        
    ## -- End Interface -- @}

# end class IDirectoryService
    

class IProjectService(IDirectoryService):
    """An interface to query project-specific information"""
    __slots__ = ()
    
    place_into_root_package = True

    # -------------------------
    ## @name Constants
    # Constants for use some of our interface functions
    # @{
    
    ## A directory with all executable paths
    PATH_EXECUTABLES = 'executables'
    ## Path for all project configuration files
    PATH_CONFIGURATION = 'configuration'
    ## A directory with all project-specific generated files, like renderings, caches, etc. It can be useful
    ## to do that as it allows different filesystem and backup policies to be implemented
    PATH_OUTPUT = 'output'
    ## Directory with all source files, basically the root of it all
    PATH_SOURCE = 'source'
    
    ## -- End Constants -- @}
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    @abstractmethod
    def id(self):
        """@return id or name of the current project"""
    
    ## -- End Interface -- @}
        
# end class IProjectService


class ISiteService(IDirectoryService):
    """Provides information about the current site and usable paths"""
    __slots__ = ()
    
    place_into_root_package = True
    
    # -------------------------
    ## @name Constants
    # @{
    
    PATH_EXECUTABLES = IProjectService.PATH_EXECUTABLES
    PATH_CONFIGURATION = IProjectService.PATH_CONFIGURATION
    ## Root of our repository, usually the root of all custom and packaged software
    PATH_REPOSITORY = 'repository'
    ## Root for software packages
    PATH_SOFTWARE = 'software'
    ## Base path containing the bcore
    PATH_CORE = 'core'
    ## Root path containing all projects
    PATH_PROJECTS = 'projects'
    
    ## -- End Constants -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    @abstractmethod
    def id(self):
        """@return the name of the site"""
    
    ## -- End Interface -- @}
    

# end class ISiteService



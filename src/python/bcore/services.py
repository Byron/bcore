# -*- coding: utf-8 -*-
"""
@package bcore.services
@brief core services providing basic information

@copyright 2012 Sebastian Thiel
"""

__all__ = ['LinuxPlatformService', 'MacPlatformService', 'ProjectInformation', 'WindowsPlatformService']

import sys


import bcore
from butility import abstractmethod
from bcontext import HierarchicalContext
from .utility import ApplicationSettingsClient

from .interfaces import (IPlatformService,
                         IProjectService,
                         ISiteService)

from . import schema


class PlatformServicesBase(IPlatformService, ApplicationSettingsClient, bcore.plugin_type()):
    """Base implementation for platform instances"""
    
    platform_names_map = HierarchicalContext.platform_names_map
                       
    # -------------------------
    ## @name Configuration
    # To be overridden by subclass
    # @{
    
    ## the name of the platform we're supporting
    platform = None
        
    ## Environment variable with path where executables are searched in
    executable_search_path_evar = 'PATH'
    
    ## Environment variable with path where the dynmamic linker looks for shared objects/dlls
    dynload_search_path_eval = None
    
    ## our platform schema
    _schema = schema.platform_schema


    # We want to be pure singleton instances, no one should instantiate one of our subclasses
    _auto_register_class_ = False
    
    ## -- End Configuration -- @}

    # -------------------------
    ## @name Interface
    # @{
    
    def id(self, id_type = IPlatformService.ID_SHORT):
        if id_type == self.ID_SHORT:
            try:
                return self.platform_names_map[sys.platform]
            except KeyError:
                raise EnvironmentError("Unknown platform: %s" % sys.platform)
        elif id_type == self.ID_FULL:
            # TODO: cache this with lazymixin
            return self.settings_value().platform.id
        else:
            raise ValueError("invalid id type")
        # end handle type

    def search_path_variable(self, variable_type):
        """@return environment variable name for a search path of the given type
        @param variable_type one of the SEARCH_* constants"""
        if variable_type == self.SEARCH_DYNLOAD:
            return self.dynload_search_path_eval
        elif variable_type == self.SEARCH_EXECUTABLES:
            return self.executable_search_path_evar
        else:
            raise ValueError('invalid variable type')
        # end handle type

    ## -- End Interface -- @}
    
# end class PlatformServicesBase


class LinuxPlatformService(PlatformServicesBase):
    """Platform instances specific for Linux"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    platform = 'lnx'
    executable_search_path_evar = 'PATH'
    dynload_search_path_eval = 'LD_LIBRARY_PATH' 
    
    ## -- End Configuration -- @}
    
# end class LinuxPlatformService

    
class MacPlatformService(PlatformServicesBase):
    """Platform instances specific for Mac OS X"""
    # -------------------------
    ## @name Configuration
    # @{
    
    platform = 'mac'
    executable_search_path_evar = 'PATH'
    dynload_search_path_eval = 'DYLD_LIBRARY_PATH' 
    
    ## -- End Configuration -- @}
    
# end class MacPlatformService


class WindowsPlatformService(PlatformServicesBase):
    """Platform instances specific to windows"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    platform = 'win'
    executable_search_path_evar = 'PATH'
    dynload_search_path_eval = executable_search_path_evar 
    
    ## -- End Configuration -- @}
    
# end class WindowsPlatformService


class DirectoryServicesMixin(object):
    """Implements some methods in a general way"""
    __slots__ = ()
    
    # -------------------------
    ## @name Subclass Interface
    # Methods for implementation or overrides by subclass
    # @{
    
    @abstractmethod
    def _directory_data(self):
        """@return a dictionary whose values are behind keys with names matching PATH_(.*)
        @note Used by the default path() implementation"""
        
    
    ## -- End Subclass Interface -- @}
    
    def id(self):
        """Default implemnetation which assumes we have an id attribute to obtain a name"""
        return self.settings_value().id
    
    def path(self, id):
        root = self._directory_data()
        path = getattr(root, id.lower(), None)
        if path is None:
            raise ValueError("Invalid id: '%s'" % id)
        # end handle key
        return path

    def path_types(self):
        """@return all path ids matching our type's PATH_ constants"""
        return [getattr(self, name) for name in dir(type(self)) if name.startswith('PATH_')]
        

# end class DirectoryServicesMixin


class ProjectInformation(DirectoryServicesMixin, IProjectService, ApplicationSettingsClient):
    """Implements the project information interface, using the kvstore exclusively"""
    __slots__ = ()

    _schema = schema.project_schema
    
    def _directory_data(self):
        return self.settings_value().directory
    
# end class ProjectInformation


class SiteInformation(DirectoryServicesMixin, ISiteService, ApplicationSettingsClient):
    """Implements the site information interface, using the kvstore exclusively"""
    __slots__ = ()

    _schema = schema.site_schema
    
    def _directory_data(self):
        return self.settings_value().root_path
    
# end class SiteInformation


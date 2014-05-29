# -*- coding: utf-8 -*-
"""
@package bapp.services
@brief core services providing basic information

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from future.builtins import object

__all__ = ['LinuxPlatformService', 'MacPlatformService', 'WindowsPlatformService', 'ProjectInformation']

import sys


import bapp
from butility import abstractmethod
from bcontext import HierarchicalContext
from .utility import ApplicationSettingsMixin

from .interfaces import (IPlatformService,
                         IProjectService)

from . import schema


class PlatformServices(IPlatformService, ApplicationSettingsMixin, bapp.plugin_type()):
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
    
# end class PlatformServices


class LinuxPlatformService(PlatformServices):
    """Platform instances specific for Linux"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    platform = 'lnx'
    executable_search_path_evar = 'PATH'
    dynload_search_path_eval = 'LD_LIBRARY_PATH' 
    
    ## -- End Configuration -- @}
    
# end class LinuxPlatformService

    
class MacPlatformService(PlatformServices):
    """Platform instances specific for Mac OS X"""
    # -------------------------
    ## @name Configuration
    # @{
    
    platform = 'mac'
    executable_search_path_evar = 'PATH'
    dynload_search_path_eval = 'DYLD_LIBRARY_PATH' 
    
    ## -- End Configuration -- @}
    
# end class MacPlatformService


class WindowsPlatformService(PlatformServices):
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
    
    def _directory_data(self):
        """@return a dictionary whose values are behind keys with names matching PATH_(.*)
        @note Used by the default path() implementation.
        @note base implementation uses the 'paths' key"""
        return self.settings_value().paths
        
    
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
        """@return all path ids for values currently available for us"""
        return list(self._directory_data().keys())
        

# end class DirectoryServicesMixin


class ProjectInformation(DirectoryServicesMixin, IProjectService, ApplicationSettingsMixin):
    """Implements the project information interface, using the kvstore exclusively"""
    __slots__ = ()

    _schema = schema.project_schema
    
# end class ProjectInformation

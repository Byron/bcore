# -*- coding: utf-8 -*-
"""
@package bcore.environ.components
@brief core components providing basic pipeline foundation support

@copyright 2012 Sebastian Thiel
"""

__all__ = ['PythonHostApplication', 'LinuxPlatformService', 'MacPlatformService', 'ProjectInformation', 
           'WindowsPlatformService']

import os
import sys
import platform

from butility import Version


import bcore
from .utility import ContextStackClient
from .interfaces import (
                            IPlatformService,
                            IHostApplication,
                            IProjectService,
                            ISiteService
                        )

from . import schema


class PlatformServicesBase(IPlatformService, ContextStackClient):
    """Base implementation for platform instances"""
    
    _platform_names = {'linux2': 'lnx',
                       'sunos5': 'sun',
                       'darwin': 'mac',
                       'win32':  'win'}
                       
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
    
    ## -- End Configuration -- @}

    # -------------------------
    ## @name Interface
    # @{
    
    def id(self, id_type = IPlatformService.ID_SHORT):
        if id_type == self.ID_SHORT:
            try:
                return self._platform_names[sys.platform]
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


class LinuxPlatformService(PlatformServicesBase, bcore.plugin_type()):
    """Platform instances specific for Linux"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    platform = 'lnx'
    executable_search_path_evar = 'PATH'
    dynload_search_path_eval = 'LD_LIBRARY_PATH' 
    
    ## -- End Configuration -- @}
    
# end class LinuxPlatformService

    
class MacPlatformService(PlatformServicesBase, Plugin):
    """Platform instances specific for Mac OS X"""
    # -------------------------
    ## @name Configuration
    # @{
    
    platform = 'mac'
    executable_search_path_evar = 'PATH'
    dynload_search_path_eval = 'DYLD_LIBRARY_PATH' 
    
    ## -- End Configuration -- @}
    
# end class MacPlatformService


class WindowsPlatformService(PlatformServicesBase, Plugin):
    """Platform instances specific to windows"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    platform = 'win'
    executable_search_path_evar = 'PATH'
    dynload_search_path_eval = executable_search_path_evar 
    
    ## -- End Configuration -- @}
    
# end class WindowsPlatformService


class PythonHostApplication(IHostApplication, Plugin):
    """A simple environment when running just inside of a standard python interpreter"""
    __slots__ = ()

    def version(self):
        return Version('.'.join(str(token) for token in sys.version_info))
        
    def name(self):
        return 'cpython'
        
    def quit(self, exit_code):
        sys.exit(exit_code)
    
    def load(self, filename):
        raise NotImplementedError("can't be done")
        
    def save(self, filename):
        raise NotImplementedError("can't be done")
        
    def loaded_file(self):
        raise NotImplementedError("can't be done")

# end class PythonHostApplication


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

    def path_ids(self):
        """@return all path ids matching our type's PATH_ constants"""
        return [getattr(self, name) for name in dir(type(self)) if name.startswith('PATH_')]
        

# end class DirectoryServicesMixin


class ProjectInformation(DirectoryServicesMixin, IProjectService, ContextStackClient, Plugin):
    """Implements the project information interface, using the kvstore exclusively"""
    __slots__ = ()

    _schema = schema.project_schema
    
    def _directory_data(self):
        return self.settings_value().directory
    
# end class ProjectInformation


class SiteInformation(DirectoryServicesMixin, ISiteService, ContextStackClient, Plugin):
    """Implements the site information interface, using the kvstore exclusively"""
    __slots__ = ()

    _schema = schema.site_schema
    
    def _directory_data(self):
        return self.settings_value().root_path
    
# end class SiteInformation


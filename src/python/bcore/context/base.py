#-*-coding:utf-8-*-
"""
@package bcore.environ.base
@brief contains readonly convenience access to the bcore.envrironment stack

@copyright 2012 Sebastian Thiel
"""
__all__ = [ 'OSContext', 'ApplicationContext', 'HostApplicationEnvironment']

import sys
import os
import platform
import logging

import bcore
import bcontext

from . import components
from .schema import (site_schema,
                     platform_schema)



from .interfaces import IPlatformService

from butility import (OrderedDict,
                      login_name)
from ..kvstore import (YAMLKeyValueStoreModifier,
                       KeyValueStoreSchema )

from butility import (Path,
                      PythonFileLoader )
import socket

log = logging.getLogger('bcore.environ.' + __name__)


class OSContext(bcontext.Context):
    """Context containing information about the operating system we're running on.
    Provides IPlatformService implementations"""
    _category = 'platform'
    _schema = platform_schema
    
    def __init__(self, name):
        """make sure platform instances for the current OS are available"""
        super(OSContext, self).__init__(name)

        # instantiate platform singleton
        try:
            inst = dict(
                    linux2 = components.LinuxPlatformService,
                    sunos5 = components.LinuxPlatformService,
                    darwin = components.MacPlatformService,
                    win32 = components.WindowsPlatformService
                    )[sys.platform]()
                    
            value = self.settings_value(self._kvstore, resolve=False)
            if not value.platform.id:
                value.platform.id = inst.id(inst.ID_FULL)
            # Enforce the actual system user
            value.user.login = login_name()
            value.user.home = Path('~').expanduser()
            value.host.fqname = socket.gethostname()
            value.host.name = value.host.fqname.split('.')[0]
            self._set_settings_value(value)
        except KeyError:
            raise EnvironmentError("Unknown platform %s" % sys.platform)
        # end handle platform singleton

        # Basic directory information
        # Those will need the ApplicationContext to have acted already (when used)
        # Order matters, as we go from general to granular
        components.SiteInformation()
        components.ProjectInformation()
        
# end class OSContext
        
        
class ApplicationContext(bcontext.HierarchicalContext):
    """Environment containing basic information about the pipelne context
       we were started in.
       We will also load most fundamental pipeline configuration, located in directories at our location,
       moving upwards"""
    _category = 'pipeline base'
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## schema for our particular context
    _schema = site_schema
    
    ## -- End Configuration -- @}

    def __init__(self, name):
        """puts pipeline base paths and python paths into the context and the
           environment. It also creates some basic components"""
        super(ApplicationContext, self).__init__(Path(__file__).dirname())
        
    def _filter_directories(self, directories):
        """amend the user's private configuration directory - people can just drop files there"""
        user_dir = self.user_config_directory()
        if user_dir.isdir():
            directories.append(user_dir)
        # user dir needs to exist - for now we don't create it
        return super(ApplicationContext, self)._filter_directories(directories)
        
    def _load_configuration(self):
        """Modify the repository_root value to what we determined at runtime 
        """
        super(ApplicationContext, self)._load_configuration()
        value = self.settings_value(self._kvstore, resolve=False)
        if not value.root_path.repository:
            value.root_path.repository = self._root_path()
        if not value.root_path.software:
            value.root_path.software = self._root_path() / 'software'
        if not value.root_path.executables:
            value.root_path.executables = self._root_path() / 'bin' / service(IPlatformService).id(IPlatformService.ID_FULL)
        if not value.root_path.configuration:
            value.root_path.configuration = Path(value.root_path.repository) / self.config_dir_name
        if not value.root_path.core:
            value.root_path.core = Path(__file__).dirname().dirname().dirname().dirname()
        self._set_settings_value(value)
        
    def _root_path(self):
        """@return the assumed pipeline root path
        @note The pipeline being self contained, we should be in the pipeline directory hierarchy,
        wherefore if we go up the directory hierarchy, we must be able to find the config dir,
        which is located in what we take to be the pipeline base directory"""
        return self.config_directories()[0].dirname()
        
    # -------------------------
    ## @name Interface
    # @{
    
    @classmethod
    def user_config_directory(cls):
        """@return the directory in which the user configuration is to be found"""
        return Path('~').expanduser() / cls.config_dir_name
        
    ## -- End Interface -- @}

# end class HierarchicalContext

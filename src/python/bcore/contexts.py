#-*-coding:utf-8-*-
"""
@package bcore.contexts
@brief custom contexts to ingest additional information into the ContextStack

@copyright 2012 Sebastian Thiel
"""
__all__ = [ 'OSContext', 'ApplicationContext']

import sys
import socket

import bcore
from bcontext import (HierarchicalContext,
                      Context)

from . import services
from .schema import (site_schema,
                     platform_schema)
from .utility import ApplicationSettingsClient


from .interfaces import IPlatformService

from butility import (OrderedDict,
                      login_name)
from bkvstore import (YAMLKeyValueStoreModifier,
                      KeyValueStoreSchema )

from butility import (Path,
                      PythonFileLoader )



class OSContext(Context, ApplicationSettingsClient):
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
                    linux2 = services.LinuxPlatformService,
                    sunos5 = services.LinuxPlatformService,
                    darwin = services.MacPlatformService,
                    win32 = services.WindowsPlatformService
                    )[sys.platform]()
                    
            value = self.settings_value(self._kvstore, resolve=False)
            if not value.platform.id:
                value.platform.id = inst.id(inst.ID_FULL)
            # Enforce the actual system user
            value.user.login = login_name()
            value.user.home = Path('~').expanduser()
            value.host.fqname = socket.gethostname()
            value.host.name = value.host.fqname.split('.')[0]

            self.settings().set_value_by_schema(self.settings_schema(), value)
        except KeyError:
            raise EnvironmentError("Unknown platform %s" % sys.platform)
        # end handle platform singleton
        
# end class OSContext
        
        
class ApplicationContext(HierarchicalContext, ApplicationSettingsClient):
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
            value.root_path.executables = self._root_path() / 'bin' / bcore.app().instance(IPlatformService).id(IPlatformService.ID_FULL)
        if not value.root_path.configuration:
            value.root_path.configuration = Path(value.root_path.repository) / self.config_dir_name
        if not value.root_path.core:
            value.root_path.core = Path(__file__).dirname().dirname().dirname().dirname()
        self.settings().set_value_by_schema(self.settings_schema(), value)

        # Basic directory information
        # Those will need the ApplicationContext to have acted already (when used)
        # Order matters, as we go from general to granular
        services.SiteInformation()
        services.ProjectInformation()
        
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

# end class ApplicationContext

#-*-coding:utf-8-*-
"""
@package bapp.contexts
@brief custom contexts to ingest additional information into the ContextStack

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division
__all__ = [ 'OSContext', 'ApplicationContext']

import sys
import socket

import bapp
from bcontext import Context

from . import services
from .schema import platform_schema
from .utility import (ApplicationSettingsMixin,
                      StackAwareHierarchicalContext)

from .interfaces import IPlatformService

from butility import (OrderedDict,
                      login_name)
from bkvstore import (YAMLKeyValueStoreModifier,
                      KeyValueStoreSchema )

from butility import Path



class OSContext(Context, ApplicationSettingsMixin):
    """Context containing information about the operating system we're running on.
    Provides IPlatformService implementations"""
    _category = 'platform'
    _schema = platform_schema

    # -------------------------
    ## @name Configuration
    # @{

    platform_service_type = dict(   linux = services.LinuxPlatformService,
                                    linux2 = services.LinuxPlatformService,
                                    sunos5 = services.LinuxPlatformService,
                                    darwin = services.MacPlatformService,
                                    win32 = services.WindowsPlatformService
                                    )[sys.platform]

    ## -- End Configuration -- @}
    
    def __init__(self, name):
        """make sure platform instances for the current OS are available"""
        super(OSContext, self).__init__(name)

        # instantiate platform singleton
        try:
            inst = self.platform_service_type()
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

    # -------------------------
    ## @name Interface
    # @{


    
    ## -- End Interface -- @}
        
# end class OSContext
        
        
class ApplicationContext(StackAwareHierarchicalContext):
    """Environment containing basic information about the pipelne context
       we were started in.
       We will also load most fundamental pipeline configuration, located in directories at our location,
       moving upwards"""
    _category = 'application'
    __slots__ = ()
    

    def __init__(self, name, user_settings = True, traverse_settings_hierarchy = True):
        """Assure that we load all configuration at bcore and above.
           It also creates some basic services to obtain information about some paths.
           @param user_settings if True, we will load user specfic settings, by default searched in ~/etc
           """
        super(ApplicationContext, self).__init__(self._root_path(),
                                                 traverse_settings_hierarchy=traverse_settings_hierarchy)

        if user_settings:
            user_dir = self.user_config_directory()
            if user_dir.isdir():
                # We expect the configuration directories to be pre-parsed
                assert self._config_dirs
                self._config_dirs.append(user_dir)
            # user dir needs to exist - for now we don't create it
        # end handle user settings

    def _load_configuration(self):
        """Modify the repository_root value to what we determined at runtime 
        """
        super(ApplicationContext, self)._load_configuration()
        # Basic directory information
        # Those will need the ApplicationContext to have acted already (when used)
        # Order matters, as we go from general to granular
        services.ProjectInformation()

    def _root_path(self):
        """@return location at which we are placed.
        @note The application being self contained, we should be in the application directory hierarchy,
        therefore if we go up the directory hierarchy, we must be able to find a config dir,
        which is located in what we take to the application's assembly"""
        return Path(__file__).dirname()
        
    # -------------------------
    ## @name Interface
    # @{
    
    @classmethod
    def user_config_directory(cls):
        """@return the directory in which the user configuration is to be found """
        return Path('~').expanduser() / cls.config_dir_name

    ## -- End Interface -- @}

# end class ApplicationContext

#-*-coding:utf-8-*-
"""
@package bcore.environ.base
@brief contains readonly convenience access to the bcore.envrironment stack

@copyright 2012 Sebastian Thiel
"""
__all__ = [ 'OSEnvironment', 'PipelineBaseEnvironment', 'StackAwareHierarchicalContext', 
            'HostApplicationEnvironment']

import sys
import os
import platform
import logging
import hashlib

import bcore
import bcontext

from . import components
from .schema import (
                        site_schema,
                        platform_schema
                    )



from .interfaces import (
                            IHostApplication,
                            IPlatformService,
                       )

from butility import (
                        OrderedDict,
                        login_name
                       )
from ..kvstore import (
                        YAMLKeyValueStoreModifier,
                        KeyValueStoreSchema
                      )

from butility import (
                        Path,
                        make_path,
                        PythonFileLoader
                    )
import socket

log = logging.getLogger('bcore.environ.' + __name__)


class OSEnvironment(bcontext.Context):
    """Environment containing instances and information about the operating system we're running on.
    Provides IPlatformService implementations"""
    _category = 'platform'
    _schema = platform_schema
    
    def __init__(self, name):
        """make sure platform instances for the current OS are available"""
        super(OSEnvironment, self).__init__(name)

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
        # Those will need the PipelineBaseEnvironment to have acted already (when used)
        # Order matters, as we go from general to granular
        components.SiteInformation()
        components.ProjectInformation()
        
        # Default host application is a python interpreter
        components.PythonHostApplication()
        
# end class OSEnvironment
        
        
class HostApplicationEnvironment(bcontext.Context):
    """A base class for all host applications."""
    __slots__ = ()
    

# end class HostApplicationEnvironment
        

class StackAwareHierarchicalContext(bcontext.HierarchicalContext):
    """A context which will assure a configuration file is never loaded twice.
    This can happen if paths have common roots, which is the case almost always.

    To prevent duplicate loads, which in turn may yield somewhat unexpected application settings, this implementation 
    uses the current applications stack to find other Contexts of our type.
    """
    __slots__ = ('_hash_map')

    def __init__(self, directory, **kwargs):
        super(StackAwareHierarchicalContext, self).__init__(directory, **kwargs)
        self._hash_map = OrderedDict()

    def _iter_config_environments(self):
        """@return iterator yielding environments of our type on the stack, which are not us"""
        for env in bcore.environment.stack():
            # we should be last, but lets not assume that
            if env is self or not isinstance(env, HierarchicalContext):
                continue
            yield env
        # end for each environment
        
    def _filter_directories(self, directories):
        """@note default implementation will ignore directories that have already been loaded by other environments
        on the stack
        """
        # for now, just iterate the environment stack directly, lets just pretend we know it very well
        # as we are an environment !
        # We keep file ordering
        current_dirs = set()
        for env in self._iter_config_environments():
            current_dirs |= set(env.config_directories())
        # end for each stack environment
        return filter(lambda dir: dir not in current_dirs, directories)

    def _filter_files(self, files):
        """@note our implementation will compare file hashes in our own hash map with ones of other
        instances of this type on the stack to assure we don't accidentally load the same file
        @note This method will update our _hash_map member"""
        for config_file in files:
            self._hash_map[hashlib.md5(open(config_file).read()).digest()] = config_file
        #end for each file
        
        # subtract all existing hashes
        our_files = set(self._hash_map.keys())
        for env in self._iter_config_environments():
            our_files -= set(env._hash_map.keys())
        #end for each environment
        
        # return all remaining ones
        # Make sure we don't change the sorting order !
        return list(self._hash_map[key] for key in self._hash_map if key in our_files) 

    # -------------------------
    ## @name Interface
    # @{

    def hash_map(self):
        """@return a dictionary of a mapping of md5 binary strings to the path of the loaded file"""
        return self._hash_map
    
    ## -- End Interface -- @}

# end class StackAwaHierarchicalContext
        
    
class PipelineBaseEnvironment(bcontext.HierarchicalContext):
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
        super(PipelineBaseEnvironment, self).__init__(make_path(__file__).dirname())
        
    def _filter_directories(self, directories):
        """amend the user's private configuration directory - people can just drop files there"""
        user_dir = self.user_config_directory()
        if user_dir.isdir():
            directories.append(user_dir)
        # user dir needs to exist - for now we don't create it
        return super(PipelineBaseEnvironment, self)._filter_directories(directories)
        
    def _load_configuration(self):
        """Modify the repository_root value to what we determined at runtime 
        """
        super(PipelineBaseEnvironment, self)._load_configuration()
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
        return make_path('~').expanduser() / cls.config_dir_name
        
    ## -- End Interface -- @}

# end class HierarchicalContext

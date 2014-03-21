#-*-coding:utf-8-*-
"""
@package bcore.environ.base
@brief contains readonly convenience access to the bcore.envrironment stack

@copyright 2012 Sebastian Thiel
"""
__all__ = [ 'OSEnvironment', 'PipelineBaseEnvironment', 'ConfigHierarchyEnvironment', 
            'HostApplicationEnvironment']

import sys
import os
import platform
import hashlib

import bcore
import bcontext

from . import components
from .schema import (
                        site_schema,
                        platform_schema
                    )

from ..log import module_logger

from .interfaces import (
                            IHostApplication,
                            IPlatformService,
                       )

from butility import (
                        int_bits,
                        tagged_file_paths,
                        update_env_path,
                        LazyMixin,
                        OrderedDict,
                        login_name
                       )
from ..kvstore import (
                        YAMLKeyValueStoreModifier,
                        KeyValueStoreSchema
                      )

from butility import (
                        Path,
                        make_path
                    )
import socket

log = module_logger('bcore.environ.' + __name__)


class OSEnvironment(bcontext.Environment):
    """Environment containing services and information about the operating system we're running on.
    Provides IPlatformService implementations"""
    _category = 'platform'
    _schema = platform_schema
    
    def __init__(self, name):
        """make sure platform services for the current OS are available"""
        super(OSEnvironment, self).__init__(name)

        # instantiate platform singleton
        try:
            inst = dict(
                    linux2 = components.LinuxPlatformService,
                    sunos5 = components.LinuxPlatformService,
                    darwin = components.MacPlatformService,
                    win32 = components.WindowsPlatformService
                    )[sys.platform]()
                    
            value = self.context_value(self._kvstore, resolve=False)
            if not value.platform.id:
                value.platform.id = inst.id(inst.ID_FULL)
            # Enforce the actual system user
            value.user.login = login_name()
            value.user.home = Path('~').expanduser()
            value.host.fqname = socket.gethostname()
            value.host.name = value.host.fqname.split('.')[0]
            self._set_context_value(value)
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
        
        
class HostApplicationEnvironment(bcontext.Environment):
    """A base class for all host applications."""
    __slots__ = ()
    _category = "host_application"
    

# end class HostApplicationEnvironment
        
        
class ConfigHierarchyEnvironment(bcontext.Environment, LazyMixin):
    """An environment which is finding configuration paths in the directory hierarchy based on some root, 
    and which loads yaml files into its own context.
    
    A2dditionally, it can load plug-ins from the very same folders, however, this should be triggerd once
    the environment was put onto the stack.
    
    As a main feature, the loader will find other loaders on the same stack and prevent the same file to 
    be laoded multiple times, just in case multiple loaders are created on different levels of the same
    hierarchy.
    """
    _category = 'recursive-directory-loader'
    __slots__ = (
                    '_directory',       ## Directory from were to start the search for configuartion directories
                    '_config_dirs',     ## Cache for all located configuration directories
                    '_config_files',    ## All files we have loaded so far, in loading-order
                    '_hash_map'         ## a mapping between a hash of a configuration file, and the file itself
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## the name of the directory in which we expect configuration files
    default_config_dir_name = 'etc'
    
    ## -- End Configuration -- @}
    
    def __init__(self, directory, load_config = True):
        """Initialize the instance with a directory from which it should search for configuration paths 
        and plug-ins.
        @param directory from which to start finding directories to laod values from
        @param load_config if True, we will load the configuration from all found configuration directories
        @note plugins must be loaded separately, if desired, to assure they end up in this environment, not in 
        the previous one.
        """
        super(ConfigHierarchyEnvironment, self).__init__(directory)
        self._hash_map = OrderedDict()
        self._directory = make_path(directory)
        self._config_files = tuple()
        if load_config:
            self._load_configuration()
        # end handle configuration loading
        
    def _iter_config_environments(self):
        """@return iterator yielding environments of our type on the stack, which are not us"""
        for env in bcore.environment._env_stack_readonly():
            # we should be last, but lets not assume that
            if env is self or not isinstance(env, ConfigHierarchyEnvironment):
                continue
            yield env
        # end for each environment
        
    def _filter_directories(self, directories):
        """@return a list of directories that we should actually use to obtain configuration from
        @param directories a list of input-directories that should be filtered
        @note default implementation will ignore directories that have already been loaded by other environments
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
        """Filter the given files which are supposed to be loaded by YAMLKeyValueStoreModifier
        @return a sorted list of files that should actually be loaded
        @note our implementation will compare file hashes in our own hash map with ones of other
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
        
    def _load_configuration(self):
        """Load all configuration files from our directories.
        Right now we implement it using tagged configuration files
        @todo at some point, support writing to the user directory. However, its non-trivial and we 
        have to do it at some later point"""
        svc = service(IPlatformService)
        tags = (svc.id(svc.ID_SHORT), svc.id(svc.ID_FULL), str(int_bits()))
        config_paths = list()
        
        for path in self._filter_directories(self.config_directories()):
            config_paths.extend(tagged_file_paths(path, tags, '*' + YAMLKeyValueStoreModifier.StreamSerializerType.file_extension))
        # end for each path in directories
        
        # We may have no configuration files left here, as the filter could remove them all (in case they
        # are non-unique)
        # for now, no writer
        config_paths = self._filter_files(config_paths)
        if config_paths:
            log.debug("Environment %s initializes its paths", self.name())
            #end for each path
            self._kvstore = YAMLKeyValueStoreModifier(config_paths)
            self._config_files = tuple(config_paths)
        # end handle yaml store
        
    def _set_cache_(self, name):
        if name == '_config_dirs':
            dirs = list()
            path = self._directory.abspath() 
            new_path = Path()
            # prevent to reach root, on linux we would get /etc, which we don't search for anything
            while path.dirname() != path:
                new_path = path / self.default_config_dir_name
                if new_path.isdir():
                    dirs.insert(0, new_path)
                # end keep existing
                path = path.dirname()
            # end less loop
            self._config_dirs = dirs
        else:
            super(ConfigHierarchyEnvironment, self)._set_cache_(name)
        # end handle name
        
    # -------------------------
    ## @name Interface
    # @{
    
    def config_directories(self):
        """@return a list of directories, least significant, highest-level directory first, directories 
        deeper down the hierarchy follow, i.e. [/foo, /foo/bar, /foo/bar/baz/feps] that will be used to load 
        configuration and plugins
        @note returned list is a reference
        """
        return self._config_dirs
        
    def config_files(self):
        """@return a tuple of all configuration files loaded by this instance as tuple. May be empty if 
        nothing was loaded yet"""
        return self._config_files

    def hash_map(self):
        """@return a dictionary of a mapping of md5 binary strings to the path of the loaded file"""
        return self._hash_map
        
        
    def load_plugins(self):
        """Call this method explicitly once this instance was pushed onto the top of the environment stack.
        This assures that new services are properly registered with it
        @note plugins should be loaded only AFTER this environment was pushed onto the stack. Otherwise
        loaded plugins will end up in the previous environment, not in this one"""
        for path in self._filter_directories(self.config_directories()):
            PluginLoader(path, recurse=True).load()
        # end load all plugins
    
    ## -- End Interface -- @}
    
# end class ConfigHierarchyEnvironment
        
    
class PipelineBaseEnvironment(ConfigHierarchyEnvironment):
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
        value = self.context_value(self._kvstore, resolve=False)
        if not value.root_path.repository:
            value.root_path.repository = self._root_path()
        if not value.root_path.software:
            value.root_path.software = self._root_path() / 'software'
        if not value.root_path.executables:
            value.root_path.executables = self._root_path() / 'bin' / service(IPlatformService).id(IPlatformService.ID_FULL)
        if not value.root_path.configuration:
            value.root_path.configuration = Path(value.root_path.repository) / self.default_config_dir_name
        if not value.root_path.core:
            value.root_path.core = Path(__file__).dirname().dirname().dirname().dirname()
        self._set_context_value(value)
        
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
        return make_path('~').expanduser() / cls.default_config_dir_name
        
    ## -- End Interface -- @}

# end class ConfigHierarchyEnvironment

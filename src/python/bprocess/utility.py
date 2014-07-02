#-*-coding:utf-8-*-
"""
@package bprocess.utility
@brief Misc utilities for use with the package system of process control

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division

__all__ = ['PackageMetaDataChangeTracker', 'FlatteningPackageDataIteratorMixin', 'application_context',
           'ProcessControllerPackageSpecification', 'PackageDataIteratorMixin',
           'ExecutableContext', 'PythonPackageIterator', 'CommandlineOverridesContext', 
           'ControlledProcessContext', 'ControlledProcessInformation']

import sys
import os

# This yaml import is save, as bkvstore will place it's own yaml module there just in case there is no 
# installed one 
import yaml

import binascii
import zlib

import logging

from contextlib import contextmanager

import bapp
from bapp import PersistentApplicationSettingsMixin
from bkvstore import (KeyValueStoreModifier,
                      KeyValueStoreProvider,
                      KeyValueStoreSchema,
                      NoSuchKeyError,
                      PathList)
from butility import ( OrderedDict,
                       StringChunker,
                       DictObject,
                       Path,
                       load_files,
                       Singleton,
                       LazyMixin )

from butility.compat import pickle

from bcontext import Context
from bapp import         ( StackAwareHierarchicalContext,
                           ApplicationSettingsMixin )
from .schema import ( controller_schema,
                      package_schema,
                      process_schema,
                      python_package_schema,
                      package_meta_data_schema)

from .interfaces import IControlledProcessInformation


log = logging.getLogger('bprocess.utility')

from bapp import StackAwareHierarchicalContext



# ==============================================================================
## @name Context Managers
# ------------------------------------------------------------------------------
## @{

@contextmanager
def application_context(*paths, **kwargs):
    """A context manager which sets up a a context based on the given file paths. To achieve that, it will 
    alter the current global context as defined in bapp.main().context() to contain all environments obtained when
    creating StackAwareHierarchicalContext instances for all the given paths.
    @return returned value is the altered bapp.main().context() instance, just for convenience
    @note this will temporarily change the bapp.main().context(), which is a rather expensive operation both in terms
    of IO and CPU
    @param paths any path that should be used to define the future context. If empty, the current 
    environment will not be altered. Each path should be a directory !
    @param kwargs valid keys are 
    + load_plugins default False, if True, plugins will be loaded for all given paths.
    @note usage: application_context(scene, executable, cwd) as env: env.context() ..."""
    if not paths:
        yield bapp.main().context()
        raise StopIteration
    # end handle empty paths
    
    # This is potentially dangerous, but we only assume to find the pipeline base environment which is 
    # supposed to hold the main pipeline configuration, and which must exist. We will keep this one, 
    # but recreate all others based on the input paths
    size = -1
    for index, env in enumerate(bapp.main().context().stack()):
        if isinstance(env, ControlledProcessContext):
            size = index + 1
            break
        # end check for special environment
    # end for each env
    assert size > -1, "Didn't find ControlledProcessContext on stack"
    
    popped_environments = list()
    try:
        while len(bapp.main().context()) > size:
            popped_environments.append(bapp.main().context().pop())
        # end pop environments
        for path in paths:
            env = bapp.main().context().push(StackAwareHierarchicalContext(path))
            if kwargs.get('load_plugins', False):
                env.load_plugins()
            # end handle plugins
        # end for each path
        yield bapp.main().context()
    finally:
        if len(bapp.main().context()) > size:
            bapp.main().context().pop(until_size = size)
        # end only pop if it makes sense
        
        # put all environments back, after removing previous ones
        for env in reversed(popped_environments):
            bapp.main().context().push(env)
        # end for each env

## -- End Context Managers -- @}


class ControlledProcessInformation(IControlledProcessInformation, Singleton, LazyMixin):
    """Store the entire kvstore (after cleanup) in a data string in the environment and allow to retrieve it
    @note this class uses a cache to assure we don't get data more often than necessary. It is all static and 
    will not change"""
    __slots__ = (
                     '_data',       # all used as cache
                     '_kvstore',     
                     '_procdata',
                     '_cmdline_overrides',
                     '_hash_map',
                )

    key_sep = ','

    def _set_cache_(self, name):
        if name == '_data':
            self._data = None
            if not self.has_data():
                return
            # end handle not started that way
            # just return it without regarding the order
            keys = os.environ[self.storage_environment_variable].split(self.key_sep)
            self._data = self._decode(''.join(os.environ[k] for k in keys).encode())
        elif name == '_kvstore':
            data = self.data()
            self._kvstore = None
            if data is None:
                return
            # end handle no data
            self._kvstore = KeyValueStoreProvider(data)
        elif name == '_procdata':
            pdata = self._yaml_data(self.process_information_environment_variable)
            if pdata is not None:
                # Cleanup afterwards to prevent inheriting it to subprocesses
                pdata = DictObject(pdata)
            self._procdata = pdata
        elif name == '_cmdline_overrides':
            self._cmdline_overrides = self._yaml_data(self.commandline_overrides_environment_variable)
        elif name == '_hash_map':
            self._hash_map = None
            if self.config_file_hash_map_environment_variable in os.environ:
                self._hash_map = self._decode(os.environ[self.config_file_hash_map_environment_variable].encode())
            # end decode value if present
        else:
            return super(ControlledProcessInformation, self)._set_cache_(name)
        # end handle cached attributes

    @classmethod        
    def _yaml_data(cls, evar):
        """@return object as loaded from the yaml string retrieved from the given environment variable,
        or None if it was unset
        @note sibling of _store_yaml_data()"""
        yaml_string = os.environ.get(evar, None)
        if yaml_string is None:
            return None
        # end handle uncontrolled process
        return yaml.load(yaml_string)
    
    @classmethod    
    def _store_yaml_data(cls, evar, env, data):
        """Store the given piece of yaml data in the given environment dictionary
        @param evar environment variable
        @param env environment dict
        @param data structure to store
        @note sibling of _yaml_data()"""
        env[evar] = yaml.dump(data)

    @classmethod
    def _encode(cls, data):
        """@return encoded version of data, suitable to be stored in the environment"""
        # make sure we pickle with protocol 2, to allow running python3 for bootstrap, 
        # which launches python2
        # We also have to be sure it's a string object, in order to be working in an environment dict
        return binascii.b2a_base64(zlib.compress(pickle.dumps(data, 2), 9)).decode()
        
    @classmethod
    def _decode(cls, data_string):
        """@return decoded version of the previously encoded data_string"""
        kwargs = (sys.version_info[0] > 2) and dict(encoding = 'utf-8') or dict()
        return pickle.loads(zlib.decompress(binascii.a2b_base64(data_string)), **kwargs)

    # -------------------------
    ## @name Interface
    # @{
    
    def data(self):
        return self._data
        
    @classmethod
    def has_data(cls, environ = None):
        return cls.storage_environment_variable in (environ or os.environ)

    def process_data(self):
        return self._procdata
        
    def commandline_overrides(self):
        return self._cmdline_overrides

    def config_hashmap(self):
        return self._hash_map
        
    ## -- End Interface -- @}
    
    
    # -------------------------
    ## @name Custom Interface
    # @{
    
    def as_kvstore(self):
        """@return a keyvalue store provider instance intialized with our data(), or None if this 
        process wasn't launched using process control"""
        return self._kvstore
        
    @classmethod
    def store(cls, env, context_stack, chunk_size=1024):
        """Store the data within the given application context within the environment dict for later retrieval
        @param env the environment dict to be used for the soon-to-be-started process
        @param context_stack a ContextStack instance from which to store all data
        @param chunk_size the size of each chunk to be stored within the environment"""
        source = cls._encode(context_stack.settings().data())

        if source:
            sc = StringChunker()

            keys = sc.split(source, chunk_size, env)
            env[cls.storage_environment_variable] = cls.key_sep.join(keys)
        # end handle source too big to be stored
        
        # store process data as well
        cls._store_yaml_data(cls.process_information_environment_variable, env, context_stack.settings().value_by_schema(process_schema))

        # Store ConfigHierarchy hashmap for restoring it later
        # merge and store
        hash_map = OrderedDict()
        for einstance in context_stack.stack():
            if isinstance(einstance, StackAwareHierarchicalContext):
                hash_map.update(einstance.hash_map())
            # end update hash_map
        # end for each env on stack

        # Always store it, even if empty
        env[cls.config_file_hash_map_environment_variable] = cls._encode(hash_map)
        
    @classmethod
    def store_commandline_overrides(cls, env, data):
        """Store the information in the given kvstore for the process that is about to be launched. He can 
        retrieve the stored information.
        @param env dict to store the data in
        @param data a dictionary or data structure with the commandline overrides
        """
        cls._store_yaml_data(cls.commandline_overrides_environment_variable, env, data)
        
    def executable(self):
        """@return executable wrapper as Path instance that was originally used to start the 
        currently running process, or None if we are not in a controlled environment"""
        process_data = self.process_data()
        if process_data is None:
            # Without a wrapper, we can only rely on our actual executable
            return None
        # end handle uncontrolled environment
        return process_data.executable
    
    ## -- End Custom Interface -- @}

# end class ControlledProcessInformation


class PackageDataIteratorMixin(object):
    """A mixin to provide functionality to iterate the process controller's package database.
    
    To do that, it will just follow the 'requires' field of each package.
    
    Subclasses should use its schema as a default and merge their own schema in as to allow to access
    their own data with each package data block the iterator returns.
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    @classmethod
    def new_controller_schema(cls, schema = package_schema):
        """Called during type instantiation to put your own schema onto package level. This allows 
        your data to be returned upon query by placing it into a KeyValueStoreSchema whose hierarchy fits
        to the one of the package controller
        @param cls
        @param schema KeyValueStoreSchema or any dict representing the data you wish to associate with
        a package. The schema must have the 'requires' key 
        @return KeyValueStoreSchema suitable for use in iteration. Assign it to your _schema class variable
        if you are an ApplicationSettingsMixin subclass"""
        return KeyValueStoreSchema(controller_schema.key(), 
                                            {   
                                                package_schema.key() : schema
                                            }
                                            )

    @classmethod
    def _package_key(cls, name):
        """@return kvstore key for package with 'name'"""
        return '%s.%s' % (controller_schema.key(), name)

    def _internal_iter_package_data(self, settings_value_or_kvstore, package_name, schema = None):
        """If schema is None, we use the settings_value mode, otherwise we access a kvstore directly"""
        if schema:
            data_by_name = lambda n: settings_value_or_kvstore.value(self._package_key(n), schema, resolve=True)
        else:
            data_by_name = lambda n: settings_value_or_kvstore[n]
        # end handle query function

        seen = set()
        def recurse_packages(name):
            if name in seen:
                raise StopIteration
            seen.add(name)
            try:
                pdata = data_by_name(name)
            except (KeyError, NoSuchKeyError):
                raise KeyError("A package named '%s' wasn't configured. It should be located at '%s'."
                                                    % (name, self._package_key(name)))
            # end provide nice exceptions
            requires = pdata.requires   # cache it !
            yield pdata, name
            del(pdata)
            for child in requires:
                for item in recurse_packages(child):
                    yield item
            # end for each child iterate
        # end utility
        
        return recurse_packages(package_name)

    def _iter_package_data(self, settings_value, package_name):
        """@return iterator yielding tuples (data, package_name) from your given settings_value, matching your package schema
        @param settings_value top-level data structure containing everything below the 'packages' key of the 
        corresponding kvstore. If you are an ApplicationSettingsMixin, this value is the settings_value()
        @param package_name name of the package at which to start the iteration - it will be returned as well."""
        return self._internal_iter_package_data(settings_value, package_name)

    def _iter_package_data_by_schema(self, kvstore, package_name, package_schema):
        """As _iter_package_data(), but more efficient as it will pick the packages individually. This 
        method should be preferred due to increased efficiency"""
        return self._internal_iter_package_data(kvstore, package_name, package_schema)
        
    def _to_package(self, name, data):
        """@return A ProcessControllerPackageSpecification instance allowing you to query the root path of 
        the package, among other things
        @param name package name
        @param data data you retrieved for the packge.
        @note in order to work properly, your data must have the trees member. Ideally, only use this
        with the default schema, i.e. package_schema, to be sure you have all the information the interface
        would want to read"""
        assert hasattr(data, 'trees'), "Data requrires 'trees' attribute for package to be functional"
        return ProcessControllerPackageSpecification(name, data)
        
        
    ## -- End Subclass Interface -- @}
        
# end class PackageIteratorMixin


class FlatteningPackageDataIteratorMixin(PackageDataIteratorMixin):
    """A mixin which provides additional functions to flatten the package data"""
    __slots__ = ()

    def _flattened_package_tree(self, program, kvstore):
        """Flatten the packge tree for the given program and return it as nested structure, which by itself
        matches the package_comparison_schema.
        @return nested ordered dict"""
        tree = OrderedDict()
        sub_tree = OrderedDict()
        tree[controller_schema.key()] = sub_tree
        
        for data, name  in self._iter_package_data(self.settings_value(kvstore), program):
            # We keep requires to allow iteration
            sub_tree[name] = data
        #end for each package to query
        return tree    

# end class FlattenedPackgeTreeMixin


class PackageMetaDataChangeTracker( PersistentApplicationSettingsMixin, 
                                    FlatteningPackageDataIteratorMixin):
    """A utility to track and query changes done to meta-data of individual packages, and to iterate 
    package information.
    
    Note that initially, you will see no changes, as it will assume everything as unchanged if there was
    no previous package data.
    
    To acknowledge changes or start tracking them, you must call make_package_state_current() at least once.
    
    PackageData we provide includes:
    
    + version
    + url
    + description
    + name (suitable for GUI purposes)
    
    """
    __slots__ = ('_package_name')
    
    _schema = PackageDataIteratorMixin.new_controller_schema(package_meta_data_schema)
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Suffix to be prepended to our settings file
    settings_prefix = 'package_state.'
    
    ## -- End Configuration -- @}
    
    def __init__(self, package_name):
        """Intiailize this instnace
        @param package_name the package (and its dependent packages) that we are supposed to track"""
        self._package_name = package_name
    
    def _initial_settings_value(self):
        """@return a flattened list of just the packages we are concerned with"""
        return self._flattened_package_tree(self._package_name, bapp.main().context().settings())
    
    def settings_id(self):
        """@return our settings id
        @note this implementation is project-aware, which is why it is recommended to set a project 
        accordingly."""
        return self.settings_prefix + '%s.%s' % (bapp.main().new_instance(bapp.IProjectService).id(), self._package_name)
    
    # -------------------------
    ## @name Interface
    # @{
    
    def changes(self):
        """@return A DictObject with changed fields and their previous values in all our dependent packages, 
        which may be empty if there was no change"""
        return self.settings_kvstore().changes()
        
    def package_data(self, previous = False):
        """@return data matching our schema of the state of all packages (not only the ones related to 
        our root package). It may be there is not a single package in it at all.
        @param previous if False, you will get the current state data, if True it will be the previous data
        @note will always return data, which might match our current state if there were no changes
        You should query changes() beforehand"""
        context = None
        if previous:
            path = self._settings_path()
            data = None
            if path.isfile():
                # Data can be empty if there is a read-error
                try:
                    data = self.settings_kvstore().settings_data(open(path))
                except Exception as err:
                    # usually program startup fails if we fail here, lets be verbose, but forgiving
                    log.error("Failed to load file at '%s' - discarding it", path, exc_info=True)
                # end empty files cause it to fail
            # end load data from file

            if not data:
                # kvstore raises if it doesn't even have the primary key in store
                data = { self._schema.key() : dict() }
            # end handle file exists
            context = KeyValueStoreModifier(data)
        # end handle previous value
        return self.settings_value(context)
        
    def iter_package_data(self, previous = False):
        """@return iterator returning tuples of (data, name) package data and name items. The data matches our 
        schema, and was retrieved from the envrionments kvstore.
        @param previous if False, you will get the current state data, if True it will be the previous data
        """
        data = self.package_data(previous=previous)
        # especially previous data might not have a change for our key
        if self._package_name not in data:
            return iter(list())
        #end handle key is not there
        return self._iter_package_data(data, self._package_name)
        
    def make_package_state_current(self):
        """Remember the state of our packages, to make it the basis for a future comparison
        @note will create settings directory if required.
        @return self"""
        path = self._settings_path()
        if not path.dirname().isdir():
            path.dirname().makedirs()
        # end assure directory exists
        self.settings_kvstore().StreamSerializerType().serialize(self._initial_settings_value(), open(path, 'w'))
        return self
        
    def package_name(self):
        """@return the name of our root package"""
        return self._package_name
        
    ## -- End Interface -- @}
    

# end class PackageMetaDataChangeTracker


class ProcessControllerPackageSpecification(LazyMixin):
    """A utility interface to provide information about the process to be launched."""
    __slots__ = (
                '_name', 
                '_data',
                '_root_path',    # cache for the root_path
                '_quiet'         # don't warn about an invalid root-path (used internally)
                )
    
    def __init__(self, name, data, quiet=False):
        """initialize the instance from pacakge data compatible to the ProcessController schema
        @param name of package this instance represents
        @param data block of data as extracted from a kvstore
        @param quiet if True, we will not log warnings"""
        self._name = name
        self._data = data
        self._quiet = quiet
        
    def _set_cache_(self, name):
        if name == '_root_path':
            try:
                # NOTE: type of this one can actually be a KVPath - we don't want that, ever
                self._root_path = Path(self._data.trees.first_accessible_tree)
            except ValueError:
                self._root_path = None          # default
                if not self._quiet:
                    log.warn("None of the given trees of package '%s' was accessible: [%s]", self.name(), ', '.join(self._data.trees))
                # end handle warning
            # end handle inaccessible directory
        else:
            super(ProcessControllerPackageSpecification, self)._set_cache_(name)
        #end handle cache name
        
    # -------------------------
    ## @name Interface
    # @{
    
    def name(self):
        """@return name of this package"""
        return self._name
    
    def root_path(self):
        """@return butility.Path instance pointing at the *existing* root of the package
        or None if there is no such path or if the configured path doesn't exist"""
        return self._root_path
        
    def data(self):
        """@return our data package"""
        return self._data
        
    def to_abs_path(self, path):
        """Convert the given possibly relative path to an absolute path, if necessary
        @note it is not checked for existence
        @param path string or butility.Path
        @return absolute version of the path, as butility.Path
        @throws ValueError if the path is relative and there is no valid root path
        @note assumes the best when an environment variable is found, which never be made absolute.
        Will only appliy to paths like '$FOO/bar', not to 'foo/$BAR'"""
        path = Path(path)
        if path.isabs():
            return path
        if path.containsvars():
            return path
        if self.root_path() is None:
            raise EnvironmentError("Cannot convert '%s' to absolute path in package '%s' without a single valid tree, tried: [%s]" % (path, self.name(), ', '.join(self._data.trees)))
        # end handle root path
        return self.root_path() / path
        
    def executable(self, env):
        """@return butility.Path to executable - its not verified to be existing
        @note for now this is uncached, but its okay for our use
        @note we always resolve environment variables
        """
        executables = self.data().executable
        if not executables:
            raise ValueError("no executable set for package '%s'" % self.name())

        error = None
        executable_path = None
        for executable in executables:
            executable_path = Path._expandvars_deep(executable, env)
            try:
                executable_path = self.to_abs_path(executable_path)
            except EnvironmentError as err:
                if '$' in executable_path:
                    # give it more time, let them work with it until something breaks
                    # Don't have another choice
                    executable_path = Path(executable_path)
                else:
                    error = err
                    continue
            # end handle conversion

            if os.name == 'nt':
                # We assume exe by default, and not com or bat.
                # Even though magic isn't good, I see no point in making this configurable, people 
                # can just be explicit about the extension
                win_ext = '.exe'
                if not executable_path.ext():
                    executable_path += win_ext
                # handle extension
            # end handle windows

            # If we have variables in the path, we can't assume anything (nor resolve) as it might be too early 
            # for that. In that case, we assume the best. Otherwise, the executable must exist
            if not executable_path.containsvars() and not executable_path.isfile():
                continue
            # end 

            return executable_path
        # end for each executable to try
        assert executable_path or error, "Should have collected at least one error at this point"
        if error:
            raise error
        return executable_path
    ## -- End Interface -- @}

# end class ProcessControllerPackageSpecification


class PythonPackageIterator(ApplicationSettingsMixin, PackageDataIteratorMixin):
    """A utility type allowing to deal with additional python information
    
    Currently it is able to import any of the given modules, per package
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    _schema = PackageDataIteratorMixin.new_controller_schema(python_package_schema)
    
    ## -- End Configuration -- @}


    # -------------------------
    ## @name Interface
    # @{
    
    @classmethod
    def import_module(cls, module, force_reimport = False):
        """Import the given module, and return its name if it was imported, or None otherwise
        @param force_reimport if True, we will not use any cached module. This can be useful if 
        plugins are to be reloaded every time, just to be sure we have the latest version.
        This is what would be expected if new Application instance is created, which shouldn't keep 
        state in the python interpreter currently running, but which will at least leave loaded 
        modules behind"""
        try:
            if force_reimport:
                try:
                    sys.modules.pop(module)
                except KeyError:
                    pass
                # end ignore exceptions
            # end handle force_reimport

            if module not in sys.modules:
                __import__(module)
            # end be less verbose
        except Exception:
            log.error("Failed to import module", exc_info=True)
        else:
            return module
        # end ignore exceptions
        return None
    
    def import_modules(self, store=None, package_name=None):
        """Imports all additional modules as specified in the configuration of our loaded packages
        @param store a kvstore with package settings (and more), usually Application.context().
        If set, we need a package_name as well
        @param package_name needs to be set if a store is given. Useful if no wrapper is involved
        @return a list of import-paths to modules that were loaded successfully.
        @note import errors will be logged, but ignored. We do not reload !
        @note only works if this process is wrapped
        @note this is a way to load plug-ins"""
        if not (store and package_name):
            assert ControlledProcessInformation.has_data()
            info = ControlledProcessInformation()
            store = info.as_kvstore()
            package_name = info.process_data().id
        # end get information

        imported_modules = list()
        if store is None:
            return imported_modules
        # end handle no wrapped process

        for pdata, pname in self._iter_package_data_by_schema(store, package_name, python_package_schema):
            for module in getattr(pdata.python, 'import'):
                imp_module = self.import_module(module, force_reimport=True)
                if imp_module:
                    log.info("Imported module '%s' for package '%s'", module, pname)
                    imported_modules.append(module)
                # end ignore exceptions
            # end for each module to laod
            plugin_paths = pdata.python.plugin_paths
            if plugin_paths:
                package = self._to_package(pname, pdata)
                for plugin_path in plugin_paths:
                    try:
                        if not plugin_path.isabs():
                            plugin_path = package.to_abs_path(plugin_path)
                        # end make plugin path absolute
                        load_files(plugin_path.expand_or_raise())
                    except Exception as err:
                        # plugin's shouldn't be essential, and make a program fail to startup (at least until
                        # we make it a configuration flag)
                        log.error("Failed to load plugin(s) at '%s' with error: %s", plugin_path, err)
                    # end don't quit on failures to load plugins
                #end for each plugin path
            # end handle plugin paths
        #end for each package
        return imported_modules
    
    ## -- End Interface -- @}    

# end class PythonPackageIterator


class ExecutableContext(StackAwareHierarchicalContext):
    """An environment automatically adding process information if this process was launched 
    through process control
    Additionally it will load python modules as defined in the respective schema
    @note we will only read the post-launch information, which is the configuration the wrapper used
    @note only effective in a controlled process"""
    __slots__ = ()

    def __init__(self):
        """Initialize this instance with the path of our executable, and add process information 
        to the kvstore"""
        pinfo = ControlledProcessInformation()
        executable = pinfo.executable()
        super(ExecutableContext, self).__init__(executable or "Executable Environment (uncontrolled process)", 
                                                    load_config = executable is not None)
        
        
        if pinfo.has_data():
            self.settings().set_value_by_schema(process_schema, pinfo.process_data())
        else:
            # Make sure we will never configure anything. Subclass would take the name we provide, 
            # and convert it to an absolute path based on the cwd, which would possibly pick up configuration
            # we want in other environments, and load it !
            self._config_dirs = list()
        # end handle data
# end class ExecutableContext


class ControlledProcessContext(StackAwareHierarchicalContext):
    """An environment which may only be created in processes started by ProcessControll to restore the exact 
    environment used when the wrapper was invoked.

    We are also a HierarchicalContext to assure that future environments will not load the 
    same yaml files again.

    @note useful for assuring the wrapped process behaves exactly like the wrapper itself
    """
    __slots__ = ()

    def __init__(self, application):
        """Set ourselves to all data provided by the wrapper
        @note does nothing if we are not wrapped"""
        # Make sure the based doesn't to any work
        super(ControlledProcessContext, self).__init__("Boot Environment", 
                                                        load_config = False, 
                                                        traverse_settings_hierarchy=False,
                                                        application=application)

        ppi = ControlledProcessInformation()
        store = ppi.as_kvstore()
        if store:
            self._kvstore = store
        # end handle store

        self._hash_map = ppi.config_hashmap()

        seen_dirs = set()
        self._config_files = list(self._hash_map.values())
        self._config_dirs = list()

        # Be a good citizen, and rebuild the internal structure
        for config_file in self._config_files:
            cdir = config_file.dirname()
            if cdir not in seen_dirs:
                self._config_dirs.append(cdir)
            # end if this is an unseen directory
        # end for each configuration file to obtain directory from

    # -------------------------
    ## @name Interface
    # documentation
    # @{
    
    def has_data(self):
        """@return True if we have data"""
        return ControlledProcessInformation.has_data()

    ## -- End Interface -- @}

# end class ControlledProcessContext


class CommandlineOverridesContext(Context):
    """An environment to re-apply commandline overrides. It should usually be added last
    @todo this would better be part of the executable environment, just MERGING the overrides into 
    the kvstore would do just fine"""
    __slots__ = ()

    def __init__(self, name='commandline overrides'):
        """Setup our commandline overrides, if there are some"""
        super(CommandlineOverridesContext, self).__init__(name)
        
        overrides = ControlledProcessInformation().commandline_overrides()
        if overrides:
            self._kvstore = KeyValueStoreModifier(overrides)
        # end handle overrides

        # finally, import modules based on a rather complete configuration
        iterator.import_modules()
        
# end class CommandlineOverridesContext


#-*-coding:utf-8-*-
"""
@package bprocess.controller
@brief Contains the controller implementation

@copyright 2013 Sebastian Thiel
"""
__all__ = ['ProcessController', 'ProcessControllerPackageSpecification', 'PackageDataIteratorMixin',
           'ExecutableContext', 'PythonPackageIterator', 'CommandlineOverridesContext', 
           'ControlledProcessContext']

import sys
import os
import subprocess
import logging

from pprint import pprint

import bapp
from butility import ( Version,
                       Path,
                       TRACE,
                       LazyMixin,
                       update_env_path,
                       GraphIteratorBase,
                       DictObject )

from bkvstore import NoSuchKeyError

from bkvstore import ( KeyValueStoreModifier,
                       KeyValueStoreSchema,
                       RootKey )
from bcontext import Context
from .interfaces import IProcessControllerDelegate
from bapp import         ( IPlatformService,
                           StackAwareHierarchicalContext,
                           ApplicationContext, 
                           ApplicationSettingsClient,
                           OSContext)
from .delegates import ( DelegateContextOverride,
                         PostLaunchProcessInformation,
                         ProcessControllerDelegateProxy,
                         DisplayHelpException,
                         DisplayContextException )
from .schema import ( controller_schema,
                      package_schema,
                      package_vspec_schema,
                      process_schema,
                      python_package_schema )


log = logging.getLogger('bprocess.controller')


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{
    

class _ProcessControllerContext(Context):
    """An environment to allow us to persistently alter the context and to bring in values"""
    __slots__ = ()
    
    _category = 'ProcessController'
    _schema = process_schema
    
    def __init__(self, program, executable, bootstrap_dir):
        """Store the bootstrap directory in our context"""
        super(_ProcessControllerContext, self).__init__("ProcessController")
        
        process = self.settings().value(self._schema.key(), self._schema)
        process.id = program
        if not process.executable_directory:
            process.executable_directory = str(bootstrap_dir)
        # end allow bootstap dir override
        process.executable_path = str(executable)
        process.bcore_directory = str(Path(__file__).dirname().dirname())
        self.settings().set_value(self._schema.key(), process)
        
# end class _ProcessControllerContext
        

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
            self._root_path = None          # default
            roots = self._data.root_paths
            for path in roots:
                if path.isdir():
                    self._root_path = path
                    break
                # end check is directory
            # end for each path
            if not self._quiet and self._root_path is None:
                log.warn("None of the given root paths of package '%s' was accessible: [%s]", self.name(), ', '.join(roots))
            # end handle roots
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
        @throws ValueError if the path is relative and there is no valid root path"""
        path = Path(path)
        if path.isabs():
            return path
        if self.root_path() is None:
            raise EnvironmentError("Cannot convert '%s' to absolute path in package '%s' without a single valid root path, tried: [%s]" % (path, self.name(), ', '.join(self._data.root_paths)))
        # end handle root path
        return self.root_path() / path
        
    def executable(self):
        """@return butility.Path to executable - its not verified to be existing
        @note for now this is uncached, but its okay for our use
        """
        executable_path = self.to_abs_path(self.data().executable)
        if os.name == 'nt':
            win_ext = '.exe'
            if not executable_path.ext():
                executable_path += win_ext
            # handle extension
        # end handle windows
        return executable_path
    ## -- End Interface -- @}

# end class ProcessControllerPackageSpecification


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
    def new_controller_schema(cls, schema):
        """Called during type instantiation to put your own schema onto package level. This allows 
        your data to be returned upon query by placing it into a KeyValueStoreSchema whose hierarchy fits
        to the one of the package controller
        @param cls
        @param schema KeyValueStoreSchema or any dict representing the data you wish to associate with
        a package. The schema must have the 'requires' key 
        @return KeyValueStoreSchema suitable for use in iteration. Assign it to your _schema class variable
        if you are an ApplicationSettingsClient subclass"""
        return KeyValueStoreSchema(controller_schema.key(), 
                                            {   
                                                package_schema.key() : schema
                                            }
                                            )
    
    def _internal_iter_package_data(self, settings_value_or_kvstore, package_name, schema = None):
        """If schema is None, we use the settings_value mode, otherwise we access a kvstore directly"""
        if schema:
            data_by_name = lambda n: settings_value_or_kvstore.value('%s.%s' % (controller_schema.key(), n), schema)
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
                raise KeyError("A package named '%s' wasn't configured. It should be located at '%s.%s'."
                                                    % (name, controller_schema.key(), name))
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
        corresponding kvstore. If you are an ApplicationSettingsClient, this value is the settings_value()
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
        @note in order to work properly, your data must have the root_paths member"""
        assert hasattr(data, 'root_paths'), "Data requrires 'root_paths' attribute for package to be functional"
        return ProcessControllerPackageSpecification(name, data)
        
        
    ## -- End Subclass Interface -- @}
        
# end class PackageIteratorMixin


class PythonPackageIterator(ApplicationSettingsClient, PackageDataIteratorMixin):
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
    def _import_module(cls, module):
        """Import the given module, and return its name if it was imported, or None otherwise"""
        try:
            if module not in sys.modules: 
                __import__(module)
            # end be less verbose
        except Exception:
            log.error("Failed to import module", exc_info=True)
        else:
            return module
        # end ignore exceptions
        return None
    
    def import_modules(self):
        """Imports all additional modules as specified in the configuration of our loaded packages
        @return a list of import-paths to modules that were loaded successfully.
        @note import errors will be logged, but ignored. We do not reload !
        @note only works if this process is wrapped
        @note this is a way to load plug-ins"""
        info = PostLaunchProcessInformation()
        store = info.as_kvstore()
        imported_modules = list()
        
        if store is None:
            return imported_modules
        # end handle no wrapped process
        for pdata, pname in self._iter_package_data_by_schema(store, info.process_data().id, python_package_schema):
            for module in getattr(pdata.python, 'import'):
                imp_module = self._import_module(module)
                if imp_module:
                    log.info("Imported module '%s' for package '%s'", module, pname)
                    imported_modules.append(module)
                # end ignore exceptions
            # end for each module to laod
            plugin_paths = pdata.python.plugin_paths
            if plugin_paths:
                package = self._to_package(pname, pdata)
                for plugin_path in plugin_paths:
                    if not plugin_path.isabs():
                        plugin_path = package.root_path() / plugin_path
                    # end make plugin path absolute
                    PythonFileLoader(plugin_path).load()
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
        pinfo = PostLaunchProcessInformation()
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

    def __init__(self):
        """Set ourselves to all data provided by the wrapper
        @note does nothing if we are not wrapped"""
        super(ControlledProcessContext, self).__init__("Wrapped Environment", load_config = False)

        ppi = PostLaunchProcessInformation()
        store = ppi.as_kvstore()
        if store:
            self._kvstore = store
        # end handle store

        self._hash_map = ppi.config_hashmap()

    # -------------------------
    ## @name Interface
    # documentation
    # @{
    
    def has_data(self):
        """@return True if we have data"""
        return PostLaunchProcessInformation.has_data()
        
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
        
        overrides = PostLaunchProcessInformation().commandline_overrides()
        if overrides:
            self._kvstore = KeyValueStoreModifier(overrides)
        # end handle overrides

        # finally, import modules based on a rather complete configuration
        iterator.import_modules()
        
# end class CommandlineOverridesContext

## -- End Utilities -- @}


class ProcessController(GraphIteratorBase, ApplicationSettingsClient, bapp.plugin_type()):
    """The main interface to deal with \ref processcontrol "Process Control" .
    
    It allows to control the environment in which processes are executed, as well as to alter their input 
    arguments and to filter their output.
    
    Mainly it is used as entry point which sets up the most important context before custom implementations
    or configurations alter the behaviour depending on the program to be launched, or other context, like the 
    currently set project or the file passed as commandline argument.
    
    * Initializes the environment based on configuration found in cwd and bootstrap dir (search upwards)
    * Use Environment's context to prepare the process launch environment
    * Spawn or exec a process, or call a python entry point.
    * To facilitate in-process spawn, it will assure the environment stack remains unchanged
    
    @see __init__()
    """
    __slots__ = ( 
                    '_boot_executable',  # our bootstrapper's executable's name
                    '_args',        # arguments provided to executable
                    '_delegate',    # our delegate
                    '_cwd',         # current working dir to use as context
                    '_environ',     # environment dictionary
                    '_executable_path', # path to executable of process we should create
                    '_spawn_override', # See set_should_spawn_process_override
                    '_help_string', # if set, no matter what, just display this help string and exit
                    '_app'          # the Application we are using to obtain information about our environment
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## don't actually launch a process, causing exec to return None in any case. Useful for testing
    dry_run = False
    
    ## A schema containing all possible values we expect for a process
    _schema = controller_schema
    
    ## if True, we will resolve package data when iterating
    # We need this flag as we can't pass arguments while iterating
    _package_data_schema = package_schema
    
    ## -- End Configuration -- @}
    
    @classmethod
    def _is_debug_mode(cls):
        """@return True if we are in debug mode"""
        return log.getEffectiveLevel() <= logging.DEBUG
    
    def __init__(self, executable, args = list(), delegate = None, cwd = None):
        """
        Initialize this instance to make it operational
        Our executable does not have to actually exist, as we will look it up in the kvstore of our environment.
        This environment stack is based on the executable's directory, which should be (but doesn't have to be) 
        accessible. Additionally it is influenced by the cwd.
        
        Callers who just want to spawn a process should make sure they manipulate the executable path to be 
        in the directory context they require, or use the cwd for that purpose if the program isn't negatively
        affected by that.
        
        @param executable of the bootstrapper program, that was launched originally. e.g. /usr/local/bin/maya
        @param args all commandline arguments passed to the executable, as list of strings. 
        @param delegate instance of type IProcessControllerDelegate. If None, the component system will be used
        to find one.
        If the envrionment stack is altered by the IProcessControllerDelegate.prepare_context() method, 
        the delegate may be overwritten.
        @param cwd current working directory to be used as additional context. If None, the actual cwd will be used.
        @return self
        @note must call _setup_execution_environment, as this instance is assumed to be ready for execute()
        """
        # NOTE: it is valid to provide a relative path (or a path which just contains the basename of the executable)
        # However, the bootstrap_dir will still be relevant to configuration (possibly), which is why it should 
        # be as sane as possible. The only way to do this is to check if we are already in a bootstapped process,
        # and use the direname accordingly
        # For using the process controller from within existing applications, guys usually just specify the name of the 
        # package to start, like 'nuke' or 'rvio'
        executable = Path(executable)
        if not executable.isabs():
            if PostLaunchProcessInformation.has_data():
                executable = PostLaunchProcessInformation().process_data().bootstrap_dir / executable
            else:
                # otherwise, just take what we have ... but as absolute path.
                executable = Path(executable).abspath()
            # end assure executable is absolute
        # end check
        self._boot_executable = Path(executable).abspath()
        self._args = list(args)
        # we will always use delegates that where explicitly set, but get it as service on first access
        self._delegate = delegate
        self._cwd = cwd or os.getcwd()
        self._environ = dict()
        self._spawn_override = None
        self._help_string = False
        
        try:
            self._setup_execution_environment()
        except DisplayHelpException, err:
            self._help_string = err.help_string
        except DisplayContextException:
            sys.stderr.write(str(bapp.main().context()._contents_str()))
            # just cause us to exit elegantly
            self._help_string = "Context displayed\n"
        except Exception, err:
            if self._is_debug_mode():
                sys.stderr.write(str(bapp.main().context()._contents_str()))
            # end handle debug mode
            raise
        #end assure context is written
        
    def _predecessors(self, program):
        """@return names for programs we depend on"""
        return self._package_data(program).requires
        
    def _successors(self, program):
        """cannot look into the future"""
        raise NotImplementedError("don't have successors")
        
    def _package_data(self, name):
        """@return verified package data for a package of the given name"""
        key = '%s.%s' % (self._schema.key(), name)
        if not self._app.context().settings().has_value(key):
            raise EnvironmentError("A package named '%s' did not exist in the database, searched at '%s'" % (name, key))
        # end graceful key handling
        return self._app.context().settings().value(key, self._package_data_schema, resolve=True)
        
    def _package(self, name):
        """@return _ProcessControllerPackageSpecification instance matching the given name
        @throws KeyError if it doesn't exist"""
        return ProcessControllerPackageSpecification(name, self._package_data(name))
        
    # -------------------------
    ## @name Subclass Interface
    # @{
            
    def _pre_execve(self):
        """Called before replacing the current process with an execve call.
        It must release all system-resources we are still holding, like open file handles 
        (might include stdin/out/err), network connections, X resources thanks to graphical interface
        @note especially gui launchers should override this method and close their GUI accordingly
        @todo close file handles
        """
        # Its unbuffered, be sure we see whats part of our process before replacement
        sys.__stdout__.flush()
        
    ## -- End Subclass Interface -- @}
    
    
    # -------------------------
    ## @name Interface
    # Our own custom interface
    # @{
    
    def delegate(self):
        # Always create a new delegate if we have none set to respond better to 
        if self._delegate is None:
            return self._app.new_instance(IProcessControllerDelegate)
        # end delay delegate instantiation
        return self._delegate
        
    def set_delegate(self, delegate):
        """Sets our delegate to the given one.
        @param delegate a ProcessControllerDelegate instance.
        @return self
        @note could be useful before the execute() call
        """
        assert delegate, 'delegate must not be unset'
        self._delegate = delegate
        return self
        
    def iter_packages(self, package_name):
        """@return iterator yielding ProcessControllerPackageSpecification instances for all packages that the given one requires
        , including the ProcessControllerPackageSpecification corresponding to package_name itself, in unspecified order.
        @param package_name name of the package from which to start the iteration.
        @note database used is the currently active kvstore, as provided by bapp.main().context().settings()
        """
        package = self._package(package_name)
        yield package
        for child in package.data().requires:
            for item in self.iter_packages(child):
                yield item
            # end for each recursive item
        # end for each child to recurse
        
    def execute_in_current_context(self, stdin=None, stdout=None, stderr=None):
        """Use this method if you would like execute any configured program within your current context, which 
        can be useful if you want to spawn a process from a running application.
        The program will always be spawned, and if desired, you can communicate with it yourself by specifying
        the respective channels.
        If any of the input channel arguments is not None, it must either be a true file object (i.e. by calling
        open(), or subprocess.PIPE. See IProcessControllerDelegate.process_filedescriptors() for more information
        about their meaning.
        @param stdin
        @param stdout
        @param stderr see IProcessControllerDelegate.process_filedescriptors()
        @return the spawned process as subprocess.Popen object. It will be ready to communicate if at least
        one channel is not None. Otherwise it will be terminated already - this method will have communicated
        with it until its natural termination. Therefore, we will block in that case."""
        # at this point, we have been initialized already and are ready to go.
        # We will smuggle in a proxy to ourselve which will return the given file-descriptors.
        # If all are None, it will communicate
        self.set_delegate(ProcessControllerDelegateProxy(self.delegate(), stdin, stdout, stderr))
        self.set_should_spawn_process_override(True)
        return self.execute()
    
    ## -- End Interface -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def _name(self):
        """Name of the process we should control"""
        return self._boot_executable.namebase()
    
    def _load_plugins(self, env_name):
        """Load all plugins from all our packages into the environment of the given name.
        It will be pushed on the stack automatically.
        @return self"""
        self._app.context().push(env_name)
        
        # First iteration sets the python path
        package_cache = list()
        for package_name, depth in self._iter_(self._name(), self.upstream, self.breadth_first):
            package = self._package(package_name)
            pdata = package.data()
            package_cache.append((package, pdata))
            
            for path in pdata.python_paths:
                if path not in sys.path:
                    if not path.isdir():
                        log.error("Wrapper python path at '%s' wasn't accessible - might not be able to load delegate", path) 
                    else:
                        sys.path.append(path)
                    # verify path is valid
                # end append path if needed
            # end for each python path to append
        # end for each package
        
        # Second iteration does the import
        plugin_paths = list()
        import_modules = list()
        for package, pdata in package_cache:
            # Plugin Paths
            ##############
            # Insert all plugin paths in front to make sure overrides are in the right order
            for path in pdata.plugin_paths:
                plugin_paths.insert(0, package.to_abs_path(path))
            # end for each plugin path to absoludify
            for module in pdata.import_modules:
                import_modules.insert(0, module)
        # end for each package
        
        for path in plugin_paths:
            PythonFileLoader(path).load()
        # end for each sorted plug-in to load
        
        for module in import_modules:
            PythonPackageIterator._import_module(module)
        # end for each module to import
        
        return self
        
    def _setup_execution_environment(self):
        """Initialize the context in which the process will be executed to the point right before it will actually
        be launched. This is called automaticlaly by during __init__() and must be called exactly once.
        
        This implementation will add an application-specific configuration file, if possible, to a new environment
        and try to apply our schema to a data structure stored at a key matching the application basename.
        
        Then we will execute all operations as indicated by the data in the current context
        
        @return self
        """
        def root_package_and_executable_provider():
            root_package = executable_provider_package = self._package(program)
            # recursively resolve the alias
            seen = set()
            while executable_provider_package.data().executable_alias:
                if executable_provider_package.data().executable_alias in seen:
                    raise AssertionError("hit loop at '%s' when trying to resolve %s" % (executable_provider_package.data().executable_alias, ', '.join(seen)))
                # end raise assertion
                seen.add(executable_provider_package.data().executable_alias)
                executable_provider_package = self._package(executable_provider_package.data().executable_alias)
            # end handle alias executable
            return root_package, executable_provider_package
        # end utility
        
        # Setup Environment according to Executable Dir and CWD
        #########################################################
        # use Environment (tagged configuration files form all /etc dirs + plugin loading)
        # and stack handling
        # First, our one to bring in some variables
        # Have to deal with the possibility that people don't provide an absolute directory or that the directory
        # is outside of the vincinity of the default configuration
        program = self._name()
        
        bootstrap_dir = self._boot_executable.dirname()
        if not bootstrap_dir.isdir():
            new_bootstrap_dir = Path(__file__).dirname()
            log.warn("Adjusted bootstrap_dir %s to %s as previous one didn't exist", bootstrap_dir, new_bootstrap_dir)
            bootstrap_dir = new_bootstrap_dir
         # end assure we have at least a good initial configuration

        # In any case, setup our own App to be absolutely fresh, to not interfere with other implementations
        self._app = app = bapp.Application.new(settings_paths=(bootstrap_dir, self._cwd),
                                               settings_hierarchy=True,
                                               user_settings=True)

        app.context().push(_ProcessControllerContext(program, self._boot_executable, bootstrap_dir))
        app.context().push(ApplicationContext('Process Controller Base'))

        # Evaluate Program Database
        ############################
        platform = OSContext.platform_service_type()
        ld_env_var = platform.search_path_variable(platform.SEARCH_DYNLOAD)
        exec_env_var = platform.search_path_variable(platform.SEARCH_EXECUTABLES)
        plugin_paths = list()
        
        # our program's package
        try:
            # Set it now, we might not get into the loop where it would be set natively. However, except case
            # uses it
            package_name = program
            
            # LOAD PLUGINS
            ###############
            # We have a basic envrionment now, load delegate plugins, before using the delegate the 
            # first time
            self._load_plugins("process-controller-stage-1")

             # UPDATE DELEGATE
            ######################
            # note: if program wouldn't have data, we would already know by now.
            root_package, executable_provider_package = root_package_and_executable_provider()
            
            # delegate could be set in constructor - keep this one as long as possible
            if self._delegate is None:
                self._delegate = root_package.data().delegate.instance
            # end use delegate overrides
            
            self._executable_path = executable_provider_package.executable()
            prev_len = len(app.context())
            self.delegate().prepare_context(app, self._executable_path, self._environ, self._args, self._cwd)
            
            # If there were changes to the environment, pick them up by clearing our data. This would the delegate 
            # name to be updated as well.
            if len(app.context()) != prev_len:
                root_package, executable_provider_package = root_package_and_executable_provider()
                self._executable_path = executable_provider_package.executable()
                
                # If the delegate put on an additional environment, we have to reload everything
                log.debug('reloading data after delegate altered environment')
                # Reload plugins, delegate configuration could have changed
                self._load_plugins("process-controller-stage-2")
                # delgate from context can be None, but future access will be delegate() only, which deals 
                # with that
                self._delegate = root_package.data().delegate.instance
            # end update data
            
            # TODO: remove this flag
            if root_package.data().legacy_inherit_env:
                # this is useful if we are started from another wrapper, or if 
                # Always copy the environment, never write it directly to assure we can do in-process launches
                self._environ.update(os.environ)

                # But be sure we don't inherit this evar - it can be set later through config though
                if bapp.minimal_init_evar in os.environ:
                    del(sefl._environ[bapp.minimal_init_evar])
                # end cleanup environment
            # end reuse full parent environment
            
            # PREPARE PROCESS ENVIRONMENT
            ##############################
            delegate = self.delegate()
            log.log(TRACE, "Using delegate of type '%s'", type(delegate).__name__)

            # In order to allow skipping particular packages, we keep an exclude list
            # It is just implemented here as this is the only place where it should be required
            exclude_packages = set()

            # A dictionary holding all variables we set - paths use a list, everything 
            # else a simple key-value pair 
            debug = dict()
            cwd_handled = False # Will be True if a package altered the current working dir
            for package_name, depth in self._iter_(program, self.upstream, self.breadth_first):
                log.debug("Using package '%s'", package_name)
                # save this one call ... 
                if package_name == program:
                    package = root_package
                else:
                    package = self._package(package_name)
                #end save one package call

                # don't exclude what's in an excluded package
                if package_name in exclude_packages:
                    log.debug("Excluding %s", package_name)
                    continue
                # end ignore excluded packages

                # update ex
                exclude_packages |= set(package.data().exclude)
                if package.data().exclude:
                    log.debug('%s: added exclude packages %s', package_name, ', '.join(package.data().exclude))
                # end handle logging
                
                # Adjust arguments
                ####################
                self._args = package.data().arguments.prepend + self._args
                self._args.extend(package.data().arguments.append)

                # CWD Adjustment
                if not cwd_handled and package.data().cwd:
                    new_cwd = package.data().cwd
                    if self._cwd == os.getcwd():
                        log.debug("%s: setting cwd override to '%s'", package_name, new_cwd)
                        # Only set it if the directory existed
                        if new_cwd.isdir():
                            self._cwd = new_cwd
                        else:
                            log.error("%s: Configured working directory '%s' was not accessible - ignoring it", package_name, new_cwd)
                        # end assure it exists
                        
                    else:
                        log.debug("%s: Will not use package-cwd '%s' as the cwd was overridden by caller", package_name, new_cwd)
                    # end don't change overridden cwd
                    cwd_handled = True
                # end first one to set cwd wins
                
                # Special Search Paths
                #######################
                for evar, paths in ((ld_env_var, package.data().environment.linker_search_paths),
                                    (exec_env_var, package.data().environment.executable_search_paths)):
                    for path in paths:
                        path = delegate.verify_path(evar, package.to_abs_path(path))
                        if path is not None:
                            debug.setdefault(evar, list()).append((str(path), package_name))
                            update_env_path(evar, path, append = True, environment = self._environ)
                        # end append path if possible
                    # end for each path
                # end for each special environment variable
                
                # Set environment variables
                ############################
                for evar, values in package.data().environment.variables.items():
                    evar_is_path = delegate.variable_is_path(evar)
                    for value in values:
                        # for now we append, as we walk dependencies breadth-first and items coming later
                        # should be effective later
                        if evar_is_path:
                            value = delegate.verify_path(evar, package.to_abs_path(value))
                            if value is None:
                                continue
                            # end handle invalid path
                        # end prepare path's value
                        
                        if evar_is_path and delegate.variable_is_appendable(evar, value):
                            debug.setdefault(evar, list()).append((str(value), package_name))
                            update_env_path(evar, value, append = True, environment = self._environ)
                        else:
                            # Don't overwrite value with older/other values
                            if evar not in self._environ:
                                debug[evar] = (str(value), package_name)
                                self._environ[evar] = str(value)
                            else:
                                log.debug("%s: can't set variable %s as its already set to %s", package_name, evar, self._environ[evar])
                        #end handle path variables
                    # end for each value to set
                # end for each variable,values tuple

                # BUILD TRANSACTION
                ###################
                for action_key in package.data().actions:
                    Action = delegate.action(action_key)
                    # TODO: It looks odd if it adds itself implicitly, possibly change that to be added explicitly
                    log.debug("Adding action '%s'", action_key)
                    Action(delegate.transaction(), action_key, Action.data(action_key), package_name, package.data())
                # end for each action
            # end for each program
        except KeyError, err:
            msg = "Configuration for program '%s' not found - error was: %s" % (package_name, str(err))
            raise EnvironmentError(msg) 
        # end handle unknown dependencies
        
        if self._is_debug_mode():
            log.debug("EFFECTIVE WRAPPER ENVIRONMENT VARIABLES")
            pprint(debug, stream=sys.stderr)
        # end show debug information
        
    def set_should_spawn_process_override(self, override):
        """This override to let the controller's caller decide if spawning is desired or not, independently of what the delgate 
        might decide. By default, the delegate will be asked.
        @param override Either True to enforce the child to be spawned, or False to enforce the process to be replaced using 
        execve. None can be set to undo any override, and let the delgate decide.
        @return the previous value
        """
        res = self._spawn_override 
        self._spawn_override = override
        return res

    def execute(self):
        """execute the executable we were initialized with, based on the context we built during initialization
        @return spawned a process instance of type Subprocess.Popen after it finished execution.
        Alterntively it can execv() a process and never returns.
        @note if execv is used, you should shutdown your frameworks and release your resources before 
        calling this method
        @throws EnvironmentError if the executable cannot be found, or if program configuration could not be
        determined.
        """
        if self._help_string:
            # This allows the bootstrapper to work
            sys.stderr.write(self._help_string)
            return DictObject(dict(returncode = 0))
        # end handle display help
        
        # Prepare EXECUTABLE
        #####################
        # Its not required to have a valid root unless the executable or one of the  is relative
        delegate = self.delegate()
        
        executable, env, args, cwd = delegate.pre_start(self._executable_path, self._environ, self._args, self._cwd)
        # play it safe, implementations could change type
        executable = Path(executable)
        if not executable.isfile():
            raise EnvironmentError("executable for package '%s' could not be found at '%s'" % (self._name(), executable))
        # end handle executable
        
        # Fill post-launch interface
        ############################
        # Allow others to override our particular implementation
        # NOTE: This should be part of the delegate, and generally we would need to separate classes more
        # as this file is way too big !!
        PostLaunchProcessInformation.store(env, self._app.context())
        
        
        should_spawn = delegate.should_spawn_process()
        if self._spawn_override is not None:
            should_spawn = self._spawn_override
        # end handle spawn override

        log.log(TRACE, "%s %s (%s)", executable, ' '.join(args), should_spawn and 'child process' or 'replace process')
        
        # Make sure arg[0] is always an executable
        # And be sure we have a list, in case people return tuples
        args = list(args)
        args.insert(0, str(executable))
        
        if not self.dry_run:
            
            if os.name == 'nt' and not should_spawn:
                # TODO: recheck this - only tested on a VM with python 2.7 ! Could work on our image
                log.warn("On windows, execve seems to crash python and is disabled in favor of spawn")
                should_spawn = True
            # end windows special handling
            
            if should_spawn:
                stdin, stdout, stderr = delegate.process_filedescriptors()
                process = subprocess.Popen( args, shell=False, 
                                            stdin = stdin, stdout = stdout, stderr = stderr,
                                            cwd = cwd, env = env)
                
                return delegate.communicate(process)
            else:
                # Cleanup our existing process - close file-handles, bring down user interface
                # We would need a callback here, ideally using some sort of event system
                self._pre_execve()
                os.chdir(cwd)
                ##############################################
                os.execve(executable, args, env)
                ##############################################
            # end 
            assert False, "Shouldn't reach this point"
        else:
            # This allows the bootstrapper to work
            return DictObject(dict(returncode = 0))
        # end handle dry-run
        
    def executable(self):
        """@return Path instance to executable that will actually be instantiated when execute() is called
        @note may only be called after a call to init()"""
        return self._executable_path
        
    ## -- End Interface -- @}

# end class ProcessController


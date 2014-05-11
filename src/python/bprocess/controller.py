#-*-coding:utf-8-*-
"""
@package bprocess.controller
@brief Contains the controller implementation

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['ProcessController', 'DisplayContextException', 'DisplaySettingsException', 
           'DisplayHelpException', 'DisplayLoadedYamlException']

import sys
import os
import subprocess
import logging
import traceback

from pprint import pformat

import bapp
from butility import ( Path,
                       TRACE,
                       update_env_path,
                       GraphIteratorBase,
                       LazyMixin,
                       PythonFileLoader,
                       DictObject,
                       set_log_level )

from bcontext import Context
from bkvstore import KeyValueStoreModifier
from bapp import         ( Application,
                           ApplicationSettingsMixin,
                           StackAwareHierarchicalContext,
                           OSContext,
                           LogConfigurator)
from .delegates import ( ControlledProcessInformation,
                         ProcessControllerDelegateProxy,
                         ProcessControllerDelegate )
from .schema import ( controller_schema,
                      package_schema,
                      process_schema,
                      package_manager_schema )
from .utility import  ( ProcessControllerPackageSpecification, 
                        PythonPackageIterator )


log = logging.getLogger('bprocess.controller')


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{


class DisplayHelpException(Exception):
    """A marker exception to indicate help should be displayed"""
    
    __slots__ = 'help_string'
    
    def __init__(self, help):
        super(DisplayHelpException, self).__init__()
        self.help_string = help
        
# end class DisplayHelpException


class DisplayContextException(Exception):
    """A marker to indicate we want the context displayed"""
    __slots__ = ()

# end class DisplayContextException


class DisplaySettingsException(Exception):
    """A marker to indicate we want the settings"""
    __slots__ = ()

# end class DisplayContextException


class DisplayLoadedYamlException(Exception):
    """A marker to indicated we want to see all yaml files"""
    __slots__ = ()

# end class DisplayLoadedYamlException


class _ProcessControlCommandlineOverridesContext(Context):
    """An environment with a custom initializer to allow storing an arbitrary dict as kvstore override"""
    __slots__ = ()
    
    def __init__(self, name, data = None):
        """Intiailize ourselves and set our kvstore to the given data dictionary, if set
        @param name of context
        @param data if set, it may be KeyValueStoreProvider instance."""
        super(_ProcessControlCommandlineOverridesContext, self).__init__(name)
        self._kvstore = data

# end class _ProcessControlCommandlineOverridesContext


class _ProcessControllerContext(Context):
    """An environment to allow us to persistently alter the context and to bring in values"""
    __slots__ = ()
    
    _category = 'ProcessController'
    _schema = process_schema
    
    def __init__(self, program, executable, bootstrap_dir, args):
        """Store the bootstrap directory in our context"""
        super(_ProcessControllerContext, self).__init__("ProcessController")
        
        process = self.settings().value(self._schema.key(), self._schema)
        process.id = program
        process.executable = str(executable)
        process.raw_arguments = list(args)
        process.python_executable = sys.executable
        process.core_tree = str(Path(__file__).dirname().dirname())
        self.settings().set_value(self._schema.key(), process)

def by_existing_dirs_and_files(fs_items):
    """@return tuple(dirs, files) sort filesystem items by their type, ignore inaaccessible ones
    @param fs_items iterable of Path objects"""
    dirs = list()
    files = list()
    for item in fs_items:
        if not item.exists():
            continue
        if item.isdir():
            dirs.append(item)
        else:
            files.append(item)
        # end sort by type
    return dirs, files
    
# end class _ProcessControllerContext
        
## -- End Utilities -- @}


class ProcessController(GraphIteratorBase, LazyMixin, ApplicationSettingsMixin):
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
                    '_boot_executable',   # our bootstrapper's executable's name
                    '_args',              # arguments provided to executable
                    '_delegate',          # our delegate
                    '_cwd',               # current working dir to use as context
                    '_environ',           # environment dictionary
                    '_executable_path',   # path to executable of process we should create
                    '_spawn_override',    # See set_should_spawn_process_override
                    '_app',               # the Application we are using to obtain information about our environment
                    '_prebuilt_app',      # An Application instance optionally provided by the user
                    '_delegate_override', # the delegate the caller might have set
                    '_dry_run',           # if True, we will not actually spawn the application,
                    '_package_data_cache',# intermediate data cache, to reduce overhead during iteration
                    '_resolve_args',      # if True, we will resolve arguments in some way
                    '_logging_override',  # log level we parsed from the commandline, or None
                    '_debug_mode',        # a flag to indicate we are in debug mode
                    '_next_exception'     # type of exception to throw if something goes wrong during preparation
                )
    
    # -------------------------
    ## @name Contants
    # @{
    
    ## A schema containing all possible values we expect for a process
    _schema = controller_schema
    
    ## if True, we will resolve package data when iterating
    # We need this flag as we can't pass arguments while iterating
    _package_data_schema = package_schema

    ## A prefex we use to determine if the argument is destined to be used for the wrapper
    wrapper_arg_prefix = '---'

    ## A prefix indicating what follows is a context location
    wrapper_context_prefix = '@'
    
    ## Separator for key-value pairs
    wrapper_arg_kvsep = '='
    
    ## adjustable wrap-time logging levels
    wrapper_logging_levels = ('trace', 'debug')

    ## Help for how to use the custom wrapper args
    _wrapper_arg_help = \
    """usage: <wrapper> [@path/to/context] [---option ...]
    ---<variables>=<value>
        A variable in the kvstore that is to receive the given value, like ---logging.verbosity=DEBUG or
       ---packages.maya.version=2013.2.0
    @/path/to/existing/dir/or_file.ext
        Shorthand for setting the application context, equivalent to cd /path/to/existing/dir && program.
        To pass @so to your program, escape the argument like @@so
    ---dry-run
        If set, we will only pretend to run the command, and not actually do it
    ---trace|debug
        Set logging verbosity at wrap time to either TRACE or DEBUG
    ---debug-context
        Print the entire context to stderr and abort program execution. Useful to learn about the contet at 
        wrap time.
    ---debug-settings
        Print the settings, which are a fully merged result of the context
    ---debug-yaml
        Print paths to all yaml files in order of appearance on the context stack
    ---help
        Prints this help and exits.

    Set the BAPP_STARTUP_LOG_LEVEL=DEBUG variable to see even more output from the startup time of the entire
    framework.
    """
    
    ## -- End Contants -- @}

    # -------------------------
    ## @name Subclass Configuration
    # @{

    ## If True, when initializing the process contexts, additional configuration will be searched 
    # upwards from the boot directory
    traverse_process_path_hierachy = True

    ## If True, when initializing Hierarchical contexts for the CWD and possibly parsed paths, these 
    # will be followed upwards to find more configuration directories
    traverse_additional_path_hierachies = True

    ## If True, user settings will be loaded
    load_user_settings = True

    ## The type to use for stack-aware hierarchical contexts
    StackAwareHierarchicalContextType = StackAwareHierarchicalContext

    ## The kind of application we create if not provided during __init__
    ApplicationType = Application
    
    ## -- End Subclass Configuration -- @}

    
    def __init__(self, executable, args = list(), delegate = None, cwd = None, dry_run = False, 
                      application = None):
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
        @param dry_run if True, we will not actually spawn any process, but make preparations as usual
        @param application if not None, this application instance will be used and modified while preparing
        to start the program in question. This can be useful if you want to control which configuration to load
        when launching something, as a few semantics are implied otherwise.
        If None, a default Application is created automatically
        @note must call _setup_execution_context, as this instance is assumed to be ready for execute()
        """
        # NOTE: it is valid to provide a relative path (or a path which just contains the basename of the executable)
        # However, the process.executable.dirname will still be relevant to configuration (possibly), which is why it should 
        # be as sane as possible. The only way to do this is to check if we are already in a bootstapped process,
        # and use the direname accordingly
        # For using the process controller from within existing applications, guys usually just specify the name of the 
        # package to start, like 'nuke' or 'rvio'
        self._dry_run = dry_run
        executable = Path(executable)
        if not executable.isabs():
            if ControlledProcessInformation.has_data():
                executable = ControlledProcessInformation().process_data().executable.dirname() / executable
            else:
                # otherwise, just take what we have ... but as absolute path.
                executable = Path(executable).abspath()
            # end assure executable is absolute
        # end check
        self._boot_executable = Path(executable).abspath()
        self._args = list(args)
        # we will always use delegates that where explicitly set, but get it as service on first access
        self._delegate_override = delegate
        self._cwd = cwd or os.getcwd()
        self._environ = dict()
        self._spawn_override = None
        self._resolve_args = False
        self._next_exception = None
        self._debug_mode = False
        self._logging_override = None
        # NOTE: We can't set the _app attribute right away, as we rely on lazy mechanisms to initialize ourselves
        # when needed. The latter wouldn't work if we set the attribute directly
        self._prebuilt_app = application
        self._package_data_cache = dict()

    def _set_cache_(self, name):
        if name in ('_app', '_executable_path', '_delegate'):
            try:
                self._setup_execution_context()
            except Exception, err:
                # convert to a custom type, in case we got that far, to respect stuff the user wanted
                # prior to the issue. This makes sure we can show debug information, for instance
                if self._next_exception is not None:
                    msg = str(err)
                    if self.is_debug_mode():
                        msg = traceback.format_exc() + '\n' + msg
                    # end prepend the original stacktrace
                    raise self._next_exception(msg)
                else:
                    # otherwise, just let it go
                    raise
                # end handle conversion of exception type
        else:
            return super(ProcessController, self)._set_cache_(name)
        # end handle name

    def _predecessors(self, program):
        """@return names for programs we depend on"""
        return self._package_data(program).requires
        
    def _successors(self, program):
        """cannot look into the future"""
        raise NotImplementedError("don't have successors")
        
    def _package_data(self, name):
        """@return verified package data for a package of the given name"""
        key = '%s.%s' % (self._schema.key(), name)
        try:
            return self._package_data_cache[key]
        except KeyError:
            pass
        # end ignore cache miss
        if not self._app.context().settings().has_value(key):
            raise EnvironmentError("A package named '%s' did not exist in the database, searched at '%s'" % (name, key))
        # end graceful key handling
        pd = self._app.context().settings().value(key, self._package_data_schema, resolve=True)
        self._package_data_cache[key] = pd
        return pd
        
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
        """@return our delegate. If none is set, a default-delegate is created for you"""
        if self._delegate is None:
            # NOTE: We intentionally don't use the registry here, as we don't just want any delegate.
            # It's common, in ProcessControl, to specify exactly which delegate to use, in order to get
            # perfectly determined behaviour
            return ProcessControllerDelegate(self.application())
        # end create default
        return self._delegate
        
    def set_delegate(self, delegate):
        """Sets our delegate to the given one.
        @param delegate a ProcessControllerDelegate instance.
        @return self
        @note could be useful before the execute() call
        """
        assert delegate, 'delegate must not be unset'
        self._delegate = delegate
        self._delegate_override = None
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

    def _clear_package_data_cache(self):
        """Clear our package cache"""
        self._package_data_cache = dict()
    
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
            
            for path in pdata.boot.python_paths:
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
            for path in pdata.boot.plugin_paths:
                plugin_paths.insert(0, package.to_abs_path(path))
            # end for each plugin path to absoludify
            for module in getattr(pdata.boot, 'import'):
                import_modules.insert(0, module)
        # end for each package
        
        for path in plugin_paths:
            PythonFileLoader.load_files(path)
        # end for each sorted plug-in to load
        
        for module in import_modules:
            PythonPackageIterator.import_module(module, force_reimport=True)
        # end for each module to import
        
        return self

    def _gather_external_configuration(self, program):
        """@return a new Context filled with a merge of all directories and files we found so far, or None 
        if there was not a single one.
        @note As we return stack-aware context, it might end up loading nothing if the respective files
        # have been loaded already. The caller should not push it onto the stack if it's kvstore is empty"""
        # aggregate the dirs and files
        all_dirs = list()
        all_files = list()

        rel_to_abs = lambda paths, pkg: (pkg.to_abs_path(p) for p in paths)

        for package_name, depth in self._iter_(self._name(), self.upstream, self.breadth_first):
            pkg = self._package(package_name)
            pd = pkg.data()
            if pd.include:
                dirs, files = by_existing_dirs_and_files(rel_to_abs(pd.include, pkg))
                all_dirs.extend(dirs)
                all_files.extend(files)
            # end sort includes
        # end for each package
        
        if not (all_dirs or all_files):
            return None
        # end bailout if there is nothing to do

        return self.StackAwareHierarchicalContextType(all_dirs, 
                                             config_files=all_files,
                                             traverse_settings_hierarchy=self.traverse_additional_path_hierachies)

    def _filter_application_directories(self, dirs):
        """@return a list of directories that our about-to-be-initialized Application instance is
        @param dirs the unfiltered source of the directories"""
        return dirs

    def _find_delegate(self, root_package, alias_package):
        """@return a delegate instance which is the most suitable one.
        Look for custom ones in order of: root_package, alias_package, all requirements (breadth-first)"""
        default_name = package_schema.delegate.name()
        for package in (root_package, alias_package):
            if package.data().delegate.name() != default_name:
                return package.data().delegate.instance(self._app.context(), self._app)
            # end check non-default one
        # end for each primary package

        # Look for one within our requirement chain
        for package_name, depth in self._iter_(self._name(), self.upstream, self.breadth_first):
            pd = self._package_data(package_name)
            if pd.delegate.name() != default_name:
                return pd.delegate.instance(self._app.context(), self._app)
            # end check delegate name

        # Finally, just return the default one. We assume it's just the standard one ProcessController
        return ProcessControllerDelegate(self._app)

    @classmethod
    def _parse_value(cls, string):
        """@return the actual numeric instance the value string represents"""
        if string in ('on', 'yes', 'true', 'True'):
            return True
        if string in ('off', 'no', 'false', 'False'):
            return False
        
        # more conversions are not required, as they are handled by the schema
        return string

    def _handle_arguments(self, args):
        """Parse args for those that can be understood by us, and return a new list with all the args 
        we didn't consume.
        We parse the following:
        * context 
        * kvstore overrides
        * logging and debugging configuration
        @return possibly pruned arg list, a possibly change cwd, and context with commandline overrides. 
        The latter should be put later when all of the configuration was already loaded.
        @note may raise exceptions to stop the program flow and instruct the bootstrapper what to do next
        """
        # Will be a kvstore if there have been overrides
        kvstore_overrides = KeyValueStoreModifier(dict())
        res = list()
        ctx = None
        cwd = self._cwd
        for arg in args:
            prefix = arg.startswith(self.wrapper_arg_prefix) and self.wrapper_arg_prefix or None
            prefix = arg.startswith(self.wrapper_context_prefix) and self.wrapper_context_prefix or prefix
            if prefix is None:
                res.append(arg)
                continue
            # end ignore non-wrapper args

            narg = arg[len(prefix):]
            # Allow consuming the entire argument - if so, pass it on
            if not narg:
                res.append(arg)
                continue
            # end assume empty args are for user, like single @

            # if the next character looks like yet another piece of the prefix, take it as an escape
            # ----foo -> ---foo
            # @@bar -> @bar
            if prefix[0] == narg[0]:
                res.append(arg[1:])
                continue
            # end escape argument
            
            arg = narg
            if arg == 'help':
                raise DisplayHelpException(self._wrapper_arg_help)
            elif arg == 'dry-run':
                self._dry_run = True
            elif arg in self.wrapper_logging_levels:
                self._logging_override = getattr(logging, arg.upper())
                set_log_level(logging.root, self._logging_override)
                if arg == 'debug':
                    self._debug_mode = True
                # end set state
            elif self.wrapper_arg_kvsep in arg:
                # interpret argument as key in context
                key_value = arg
                assert len(key_value) > 2 and self.wrapper_arg_kvsep in key_value, "expected k=v string at the very least, got '%s'" % key_value
                k, v = key_value.split(self.wrapper_arg_kvsep)
                if v.startswith('['):
                    try:
                        v = eval(v)
                    except Exception:
                        raise ValueError("Failed to parse '%s' as a list for key '%s'" % (v, k))
                    # end handle conversion
                # end handle lists
                kvstore_overrides.set_value(k, self._parse_value(v))
                log.debug("CONTEXT VALUE OVERRIDE: %s", key_value)
            elif arg == 'debug-context':
                # Just ignore these, they are handled elsewhere
                self._next_exception = DisplayContextException
            elif arg == 'debug-settings':
                self._next_exception = DisplaySettingsException
            elif arg == 'debug-yaml':
                self._next_exception = DisplayLoadedYamlException
            elif prefix == self.wrapper_arg_prefix:
                raise ValueError("Argument named '%s' unknown to wrapping engine, escape arguments by prepending a dash, like ----escaped-arg" % arg)
            else:
                # it could be a context
                new_cwd = Path(arg)
                # if it looks like a file, make it a directory
                if new_cwd.ext():
                    new_cwd = new_cwd.dirname()
                # end

                if not new_cwd.isdir():
                    raise ValueError("Context directory at '%s' was inaccessible" % new_cwd)
                # end set cwd

                cwd = new_cwd
            # end handle arg
        # end for each arg
        
        # set overrides
        if kvstore_overrides.keys():
            ctx = _ProcessControlCommandlineOverridesContext('commandline overrides', kvstore_overrides)
            ControlledProcessInformation.store_commandline_overrides(self._environ, kvstore_overrides.data())
        #end handle overrides

        return res, cwd, ctx
        
    @classmethod
    def _resolve_package_alias(cls, package, fpackage_by_name):
        """@return alias_package for the given package. alias_package may be package
        @param fpackage_by_name f(n) -> ProcessControllerPackageSpecification for n"""
        # recursively resolve the alias
        seen = set()
        while package.data().alias:
            if package.data().alias in seen:
                raise AssertionError("hit loop at '%s' when trying to resolve %s" % (package.data().alias, ', '.join(seen)))
            # end raise assertion
            seen.add(package.data().alias)
            package = fpackage_by_name(package.data().alias)
        # end handle alias executable
        return package
        
    def _setup_execution_context(self):
        """Initialize the context in which the process will be executed to the point right before it will actually
        be launched. This is called automaticlaly by during __init__() and must be called exactly once.
        
        This implementation will add an application-specific configuration file, if possible, to a new environment
        and try to apply our schema to a data structure stored at a key matching the application basename.
        
        Then we will execute all operations as indicated by the data in the current context
        
        @return self
        """
        def root_package_and_executable_provider():
            root_package = self._package(program)
            return root_package, self._resolve_package_alias(root_package, self._package)
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

        # Have to get our arguments of the list here, to be able to respond to it properly
        orig_args = self._args
        self._args, self._cwd, overrides_context = self._handle_arguments(self._args)

        # In any case, setup our own App to be absolutely fresh, to not interfere with other implementations
        if self._prebuilt_app:
            self._app = app = self._prebuilt_app
        else:
            self._app = app = self.ApplicationType.new(
                                    settings_trees=   self._filter_application_directories((bootstrap_dir, 
                                                      self._cwd)),
                                                      settings_hierarchy=self.traverse_process_path_hierachy,
                                                      user_settings=self.load_user_settings,
                                                      setup_logging=False)
        # end initialize application
        app.context().push(_ProcessControllerContext(program, self._boot_executable, bootstrap_dir, orig_args))

        # place overrides to affect gathering configuration
        if overrides_context:
            app.context().push(overrides_context)
        # end add context prior to delegate work

        # now setup the logging - we delay it as much as possible, as we want the overrides to catch on
        # We restore the logging level if there is an override set on the commandline (for process control)
        LogConfigurator.initialize(self._logging_override)

        # Add global package manager settings. We put it onto the stack right away, as this allows others 
        # to offload their program configuraiton to a seemingly unrelated location
        # NOTE: We do it just once, which implies behaviour might be undefined if the delegate choses to 
        # change these particular values.
        # See issue https://github.com/Byron/bcore/issues/12
        pm = self._app.context().settings().value_by_schema(package_manager_schema, resolve=True)
        if pm.include:
            dirs, files = by_existing_dirs_and_files(pm.include)
            # we do something very special here, after all, this should be the foundation of everything we do
            pre_ctx = self.StackAwareHierarchicalContextType(dirs,
                                                config_files=files,
                                                traverse_settings_hierarchy=self.traverse_additional_path_hierachies)
            # have to make this more public in kvstore, I think it's valid to do that, sometimes
            # NOTE: this flexibility needs a full rebuild !
            app.context().insert(0, pre_ctx)
            # as the context was inserted, the overrides are still last (and will be re-applied)
        # end handle package manager configuration

        external_configuration_context = self._gather_external_configuration(program)
        if external_configuration_context and external_configuration_context.settings().data():
            if overrides_context:
                app.context().pop()
            app.context().push(external_configuration_context)
            if overrides_context:
                app.context().push(overrides_context)
            self._clear_package_data_cache()
        else:
            # Mark it as unset so we don't try to remove it later, possibly
            external_configuration_context = None
        # end add external configuration

        # Evaluate Program Database
        ############################
        platform = OSContext.platform_service_type()
        ld_env_var = platform.search_path_variable(platform.SEARCH_DYNLOAD)
        exec_env_var = platform.search_path_variable(platform.SEARCH_EXECUTABLES)
        
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
            root_package, alias_package = root_package_and_executable_provider()
            
            # delegate could be set in constructor - keep this one as long as possible
            self._delegate = self._delegate_override # may be None
            if self._delegate is None:
                self.set_delegate(self._find_delegate(root_package, alias_package))
            # end use delegate overrides
            
            self._executable_path = alias_package.executable(self._environ)
            prev_len = len(app.context())


            self.delegate().prepare_context(self._executable_path, self._environ, self._args, self._cwd)


            # If there were changes to the contxt, which means we have to refresh all our data so far
            if len(app.context()) != prev_len:
                # As the settings changed, our cache needs update too
                self._clear_package_data_cache()

                root_package, alias_package = root_package_and_executable_provider()

                # Now we have to load exernal dependencies again, as our entire configuration could have changed
                # We try to prevent needless work though by
                # * only rebuidling if something changed
                # * removing the previous context to make rebuilding faster
                def remove_previous_configuration():
                    assert external_configuration_context
                    app.context().remove(external_configuration_context)
                # end

                def reapply_commandline_overrides():
                    if overrides_context:
                        app.context().remove(overrides_context)
                        app.context().push(overrides_context)
                    # end only if there are overrides
                # end 

                # now commandline overrides have been overidden by the delegate, and we can't have that
                reapply_commandline_overrides()
                    
                # NOTE: all the following code tries hard not to push or pop a context without having 
                # the need for it. The latter will invalidate our cache, which is expensive to redo
                new_external_configuration_context = self._gather_external_configuration(program)
                if new_external_configuration_context:
                    new_data = new_external_configuration_context.settings().data()
                    if external_configuration_context:
                        # As the stack-aware context won't have any contents if there are no new files, 
                        # it might end up empty. In that case, there is no need to do anything
                        if new_data and new_data != external_configuration_context.settings().data():
                            # the configuration changed, remove previous one, and add this one
                            # the removal is kind of sneaky, but thanks to the addition, the cache will be 
                            # invalidated anyway
                            remove_previous_configuration()
                            app.context().push(new_external_configuration_context)
                            reapply_commandline_overrides()
                        else:
                            # there is no change, don't do anything
                            pass
                        # end remove previous on mismatch
                    else:
                        # there is just a new one, add it
                        if new_data:
                            app.context().push(new_external_configuration_context)
                            reapply_commandline_overrides()
                        # end
                    # end handle previous external context
                elif external_configuration_context:
                    # there is an old, but no new one. Delete previous one
                    remove_previous_configuration()
                # end handle new configuration context

                self._executable_path = alias_package.executable(self._environ)
                
                # If the delegate put on an additional environment, we have to reload everything
                log.debug('reloading data after delegate altered environment')
                # Reload plugins, delegate configuration could have changed
                self._load_plugins("process-controller-stage-2")
                # delgate from context can be None, but future access will be delegate() only, which deals 
                # with that
                self.set_delegate(self._find_delegate(root_package, alias_package))
            # end update data
            
            if root_package.data().environment.inherit:
                # this is useful if we are started from another wrapper, or if 
                # Always copy the environment, never write it directly to assure we can do in-process launches
                self._environ.update(os.environ)
            # end reuse full parent environment
            
            # PREPARE PROCESS ENVIRONMENT
            ##############################
            delegate = self.delegate()
            log.log(TRACE, "Using delegate of type '%s'", type(delegate).__name__)

            # In order to allow skipping particular packages, we keep an ignore list
            # It is just implemented here as this is the only place where it should be required
            exclude_packages = set()

            # A dictionary holding all variables we set - paths use a list, everything 
            # else a simple key-value pair 
            debug = dict()
            cwd_handled = False # Will be True if a package altered the current working dir

            normpath = lambda p: pm.environment.normalize_paths and p.normpath() or p
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
                exclude_packages |= set(package.data().ignore)
                if package.data().ignore:
                    log.debug('%s: added exclude packages %s', package_name, ', '.join(package.data().ignore))
                # end handle logging
                
                # Adjust arguments
                ####################
                pargs = package.data().arguments
                self._args = pargs.prepend + self._args
                self._args.extend(pargs.append)
                self._resolve_args |= pargs.resolve

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
                resolve_evars = package.data().environment.resolve
                for evar, paths in ((ld_env_var, package.data().environment.linker_search_paths),
                                    (exec_env_var, package.data().environment.executable_search_paths)):
                    for path in paths:
                        if resolve_evars:
                            path = delegate.resolve_value(path, self._environ)
                        # end 
                        path = delegate.verify_path(evar, package.to_abs_path(path))
                        if path is not None:
                            path = normpath(path)
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
                        if resolve_evars:
                            value = delegate.resolve_value(value, self._environ)
                        # end
                        if evar_is_path:
                            value = delegate.verify_path(evar, package.to_abs_path(value))
                            if value is None:
                                continue
                            # end handle invalid path
                        # end prepare path's value
                        
                        if evar_is_path and delegate.variable_is_appendable(evar, value):
                            value = normpath(value)
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

        # Obtain the executable path one more time, after all, it may be dependent on environment 
        # variables that want to be resolved now
        self._executable_path = alias_package.executable(self._environ)

        # We also have to resolve all values, unconditionally.
        for evar, value in self._environ.iteritems():
            if '$' not in value:
                continue
            self._environ[evar] = delegate.resolve_value(value, self._environ)
        # end for each variable to subsitiute
        

        # DEBUGGING
        ############
        if self.is_debug_mode():
            # print out all files participating in environment stack
            log.debug("EFFECTIVE WRAPPER ENVIRONMENT VARIABLES (with possibly unresolved $VARIABLE_SUBSTITUTIONS)")
            log.debug(pformat(debug))
            log.debug("ENTIRE ENVIRONMENT (INCLUDING $VARIABLE_SUBSTITUTIONS)")
            from butility import OrderedDict
            log.debug(OrderedDict(self._environ))
        # end show debug information

        # Check if we shuold stop for debugging
        if self._next_exception:
            raise self._next_exception()
        # end 
        
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
        # Prepare EXECUTABLE
        #####################
        # Its not required to have a valid root unless the executable or one of the  is relative
        delegate = self.delegate()
        executable, env, args, cwd = delegate.pre_start(self._executable_path, self._environ, self._args, self._cwd, self._resolve_args)
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
        ControlledProcessInformation.store(env, self._app.context())
        
        
        should_spawn = delegate.should_spawn_process()
        if self._spawn_override is not None:
            should_spawn = self._spawn_override
        # end handle spawn override

        log.log(TRACE, "%s%s %s (%s)", self._dry_run and "WOULD RUN " or "",
                                       executable,
                                       ' '.join(args), 
                                       should_spawn and 'child process' or 'replace process')
        
        # Make sure arg[0] is always an executable
        # And be sure we have a list, in case people return tuples
        args = list(args)
        args.insert(0, str(executable))
        
        if not self._dry_run:
            
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

    def application(self):
        """@return application object which keeps the context of the to-be-started program"""
        assert self._app
        return self._app
        
    def is_debug_mode(self):
        """@return True if we are in debug mode"""
        return self._debug_mode or self._next_exception

    ## -- End Interface -- @}

# end class ProcessController


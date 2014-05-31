#-*-coding:utf-8-*-
"""
@package bprocess
@brief implementations of the interfaces related to process control

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from minifuture import str

__all__ = ['ProcessControllerDelegate', 'DelegateContextOverride', 'ControlledProcessInformation', 
           'MayaProcessControllerDelegate', 'KatanaControllerDelegate',
           'ProcessControllerDelegateProxy', 'MariControllerDelegate']

import os
import sys
import re
import logging
import subprocess

import bapp
# This yaml import is save, as bkvstore will place it's own yaml module there just in case there is no 
# installed one 
import yaml

import binascii
import zlib

from pickle import (loads,
                     dumps)

import logging

from bapp import StackAwareHierarchicalContext
from bkvstore import ( RootKey,
                       KeyValueStoreProvider,
                       KeyValueStoreModifier )
from bdiff import ( NoValue,
                    TwoWayDiff,
                    ApplyDifferenceMergeDelegate )

from bcontext import Context
from .interfaces import ( IProcessControllerDelegate,
                          IControlledProcessInformation )

from butility import ( update_env_path,
                       DictObject,
                       Singleton,
                       LazyMixin,
                       StringChunker )

from .actions import ActionDelegateMixin

from .schema import ( controller_schema,
                      process_schema,
                      package_manager_schema,
                      NamedServiceProcessControllerDelegate )

from butility import ( Path,
                       OrderedDict )

log = logging.getLogger('bprocess.delegate')


#ocio ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

class ProcessControllerDelegateProxy(object):
    """A simple proxy which behaves differently based on its input channel arguments"""
    __slots__ = (
                    '_delegate', # delegate we are proxying
                    '_channels',  # a list of channels
                    '_communicate_orig', # delegate implementation of communicate
                    '_launch_mode' # the launch mode to enforce, in any way
                )
    
    def __init__(self, delegate, launch_mode, *channels):
        """Intialize ourselves with a delegate that we are to proxy/override, and stdin, stdout, stderr 
        channels"""
        self._delegate = delegate
        self._channels = channels
        self._launch_mode = launch_mode
        
    def __getattr__(self, name):
        return getattr(self._delegate, name)
        
    # -------------------------
    ## @name Overrides
    # @{
    
    def process_filedescriptors(self):
        """@return our channels"""
        return self._channels

    def launch_mode(self):
        """@return preset launch_mode"""
        return self._launch_mode
        
    def communicate(self, process):
        """@return process without having communicated if any of our channels was set"""
        if any(self._channels):
            return process
        return self._communicate_orig(process)

    def start(self, args, cwd, env, spawn):
        self._communicate_orig = self._delegate.communicate
        # self._delegate.__dict__['communicate'] = self.communicate
        self._delegate.communicate = self.communicate
        self._delegate.process_filedescriptors = self.process_filedescriptors

        return self._delegate.start(args, cwd, env, spawn)
    ## -- End Overrides -- @}
    
    
# end class ProcessControllerDelegateProxy
        


class DelegateContextOverride(Context):
    """A context specifically designed to be used by a delegate to override particular values of our 
    kvstore.
    It knows our base schema and uses it to obtain the unresolved datablock, for being changed by the 
    delegate in a relatively save manner. It will then be written into the contexts kvstore
    @note This context puts itself on the stack to take that burden off the caller !"""
    _category = 'DelegateOverride'
    
    class DifferenceDelegate(ApplyDifferenceMergeDelegate):
        """Handle special types"""
        __slots__ = ()
    
        def _resolve_conflict(self, key, left_value, right_value):
            if isinstance(right_value, NamedServiceProcessControllerDelegate):
                return NoValue
            return super(DelegateContextOverride.DifferenceDelegate, self)._resolve_conflict(key, left_value, right_value)
    
    # end class DifferenceDelegate
    
    def setup(self, kvstore, value_provider, schema, *args, **kwargs):
        """Configure a value override, storing only changes done accoridng to a given schema
        @param kvstore from which to retrieve values by schema
        @param value_provider a function f(schema, current_value, *args, **kwargs), which changes current_value 
        according to it's own needs. Only the changed values will make it into this Context's kvstore
        @param schema the schema to use for the override
        @param args arguments to be passed to value_provider()
        @param kwargs kwargs to be passed to value_provider()
        @return self """
        new_value = kvstore.value(schema.key(), schema)
        value_provider(schema, new_value, *args, **kwargs)
        
        # find only the changed values and write them as kvstore
        prev_value = kvstore.value(schema.key(), schema)
        diff_delegate = self.DifferenceDelegate()
        TwoWayDiff().diff(diff_delegate, prev_value, new_value)
        
        self._kvstore.set_value(schema.key(), diff_delegate.result())
        return self
        
# end class ProcessControllerEnvironment


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
        # make sure we pickle with protocol 2, to allow running python3 for bootstrap, which launches
        # python2
        return binascii.b2a_base64(zlib.compress(dumps(data, 2), 9))
        
    @classmethod
    def _decode(cls, data_string):
        """@return decoded version of the previously encoded data_string"""
        if sys.version_info[0] < 3:
            return loads(zlib.decompress(binascii.a2b_base64(data_string)))
        else:
            return loads(zlib.decompress(binascii.a2b_base64(data_string)), encoding='utf-8')
        # end

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

## -- End Utilities -- @}


# ==============================================================================
## @name Interface Implementation
# ------------------------------------------------------------------------------
## @{


class ProcessControllerDelegate(IProcessControllerDelegate, ActionDelegateMixin, bapp.plugin_type()):
    """Implements the controller's delegate
    
    Wrapper Arguments
    =================
    
    It is possible to provide arguments that are interpreted only by the wrappers delegate. Those arguments
    start with a triple-dash ('---') and can be the following
    """
    __slots__ = ('_controller_settings')
    
    ## if True, configuration will be parsed from paths given as commandline argument. This is useful
    # to extract context based on passed files (for instance, for rendering)
    context_from_path_arguments = False
    
    ## A regular expression to check if we have a path
    re_find_path = re.compile(r"^.+[/\\][^/\\]+$")

    def __init__(self, application):
        super(ProcessControllerDelegate, self).__init__(application)
        self._controller_settings = \
            self._app.context().settings().value_by_schema(package_manager_schema, resolve=True).environment.variables

    # -------------------------
    ## @name Configuration
    # @{
    
    ## Type used when instanating an environment to keep delegate configuration overrides
    DelegateContextOverrideType = DelegateContextOverride
    
    ## -- End Configuration -- @}

    def environment_storage_chunk_size(self):
        """@return chunk size in bytes, defining how many characters an environment variable value may help in total"""
        # Linux max-chunk size is actually not set, but now we chunk everything
        # chunk_size = sys.platform == 'win32' and 1024 * 32 - 2 or 1024*1024
        return sys.platform == 'win32' and 1024 * 32 - 2 or 1024*1024
    
    def prepare_context(self, executable, env, args, cwd):
        """We will parse paths from the given commandline and use them in the context we build.
        Additionaly, we will provide a per-arg handler with the opportunity to inject kvstore overrides
        """
        # Will be a kvstore if there have been overrides
        kvstore_overrides = KeyValueStoreModifier(dict())
        for arg in args:
            # by default, we use paths as as context provider (configurable)
            path = self._extract_path(arg)
            if path:
                # ignore args that are not paths
                path = Path(path)
                if path.dirname().isdir():
                    self._app.context()(StackAwareHierarchicalContext(path.dirname()))
                # end handle valid directory
            # end handle path
            self.handle_argument(arg, kvstore_overrides)
        # end for each arg to check
        
        # set overrides
        if list(kvstore_overrides.keys()):
            self._app.context().push(Context('delegate overrides', kvstore_overrides))
        #end handle overrides
        return super(ProcessControllerDelegate, self).prepare_context(executable, env, args, cwd)
        
    def variable_is_path(self, environment_variable):
        """Base implementation uses the process manager settings and the regex defined there 
        to determine what is a considered a path.
        """
        return bool(self._controller_settings.regex.is_path.match(environment_variable))
        
    def variable_is_appendable(self, environment_variable, value):
        """Default implementation considers paths appendable if they match a regular expression
        as defined in the package manager settings."""
        return bool(self._controller_settings.regex.path_is_appendable.match(environment_variable))
        
    def verify_path(self, environment_variable, path):
        """@return allow everything that is an existing path, otherwise drop it, and log the incident
        @note we assume that variables will be substituted later, and must let it pass"""
        if path.containsvars():
            return path
        if not path.exists():
            log.warn("%s: '%s' dropped as it could not be read", environment_variable, path)
            return None
        return path

    def resolve_arg(self, arg, env):
        """@return the argument without any environment variables
        @note this method exists primarly for interception by subclasses"""
        return str(Path._expandvars_deep(arg, env))

    def resolve_value(self, value, env):
        """Our base implementation just substitutes environment variables"""
        return self.resolve_arg(value, env)

    def pre_start(self, executable, env, args, cwd, resolve):
        """@return env unchanged, but assure that X-Specific variables are copied from our current environment
        if they exist. We will not override existing values either.
        Additionally it will apply the transaction to prepare the process launch.
        We will resolve environment variables, if desired
        @note also removed custom wrapper arguments, which are identified by their '---' prefix"""
        self.update_from_os_environment(env)
        # remove wrapper args
        new_args = list()
        for arg in args:
            if resolve and '$' in arg:
                # we really just want the resolver engine
                arg = self.resolve_arg(arg, env)
            # end handle argument substitution
            new_args.append(arg)
        # end for arg in args

        if self.has_transaction():
            if self.transaction().apply().failed():
                raise self.transaction().exception()
        # end handle transaction

        return (executable, env, new_args, cwd)

    def launch_mode(self):
        """@return fork by default, or spawn if required"""
        if self.has_transaction():
            return any(op.delegate_must_spawn is not None and op.delegate_must_spawn or False for op in self.transaction()) and self.LAUNCH_MODE_CHILD or None
        # end 
        return self.LAUNCH_MODE_REPLACE
        
    def process_filedescriptors(self):
        """Default implementation uses no stdin, and connects the parent processes stderr and stdout to the
        respective channels in the child process"""
        return (None, sys.__stdout__, sys.__stderr__)
        
    def communicate(self, process):
        """retrieve all outputs until the process is done"""
        process.communicate()
        return process
        
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    def _extract_path(self, arg):
        """@return the path this argument seems to refer to, or None if it doesn't contain a path
        @param arg any argumment provided to the starting process, as parsed during prepare_context() and
        after wrapper specific arguments where extracted"""
        if not self.context_from_path_arguments:
            return None
        #end early bailout
        match = self.re_find_path.match(arg)
        if not match:
            return None
        return match.group(0)
    
    def update_from_os_environment(self, env, append = False):
        """Update all variables in the given env from their counterpart in os.environ.
        This allows to selectively inherit from your parent environment
        @param env the environment to store the values from os.environ in
        @param append if True, and if the environment variable is a path, it will be appended.
        Otherwise it will be prepended.
        @note this is just a utility, you could easily implement it yourself"""
        for evar in self._controller_settings.inherit:
            if evar not in os.environ:
                continue
            # end ignore un-inheritable ones
            value = os.environ[evar]
            if self.variable_is_path(evar):
                update_env_path(evar, value, append = append, environment = env)
                log.debug("Setting %s = %s, append = %i", evar, value, append) 
            else:
                log.debug('Setting %s = %s', evar, value)
                env[evar] = value
            # end handle path variables
        # end for each xvar

    def resolve_arguments(self, args):
        """Resolve all environment variables, recursively"""
        
    def set_context_override(self, schema, value, *args, **kwargs):
        """Use the given ProcessController schema to safely alter the given context value.
        @note only called by the utility type, DelegateContextOverride .
        @param schema defined by the ProcessController who is driving the process
        @param value obtained from the global context, matching the schema, with entirely unresolved values.
        @param args defined by the caller
        @param kwargs defined by the caller"""
        raise NotImplementedError("To be defined by subclass")
    
    def new_environment_override(self, *args, **kwargs):
        """Initialize a DelegateContextOverride instance to allow making selective version overrides. The
        schema used is the one of the ProcessController, allowing full access to all package data
        @note Must be called during prepare_context() to have an effect
        @param args passed to set_context_override()
        @param kwargs passed to set_context_override()
        @return newly created DelegateContextOverride instance"""
        ctx = self.DelegateContextOverrideType(type(self).__name__ + ' Override').setup(self._app.context().settings(),
                                                                                        self.set_context_override,
                                                                                        controller_schema,
                                                                                        *args, **kwargs)
        return self._app.context().push(ctx)
        
    def handle_argument(self, arg, kvstore):
        """Method called whenver an argument seen by the delegate is to be evaluated.
        Subtypes can use it to implement custom argument parsing and interpretation
        @param arg as seen on the commandline. Might contain unresolved environment variables
        @param kvstore a kvstore that can be used to store values in an overrride context
        @note you will have a chance to modify the arguments, and more, in pre_start()
        @throws AssertionError if the argument cannot be handled"""

    def _pre_execve(self):
        """Called before replacing the current process with an execve call.
        It must release all system-resources we are still holding, like open file handles 
        (might include stdin/out/err), network connections, X resources thanks to graphical interface
        @note especially gui launchers should override this method and close their GUI accordingly
        @todo close file handles
        """
        # Its unbuffered, be sure we see whats part of our process before replacement
        sys.__stdout__.flush()

    def start(self, args, cwd, env, launch_mode):
        """Called to actually launch the process using the given arguments. Unless launch_mode is 'replace, this 
        method will not return. Otherwise it returns the Subprocess.popen process
        @param args all arguments we figured out so far, first argument is the executable itself
        @param cwd the current working directory to use for the newly started process
        @param env dict with environment variables to set
        @param launch_mode one of the standard LAUNCH_MODE_* constants in the IProcessControllerDelegate interface"""
        if os.name == 'nt' and launch_mode == self.LAUNCH_MODE_REPLACE:
            # TODO: recheck this - only tested on a VM with python 2.7 !
            log.warn("On windows, execve seems to crash python and is disabled in favor of spawn")
            launch_mode = self.LAUNCH_MODE_CHILD
        # end windows special handling
        

        if launch_mode == self.LAUNCH_MODE_CHILD:
            stdin, stdout, stderr = self.process_filedescriptors()
            process = subprocess.Popen( args, shell=False, 
                                        stdin = stdin, stdout = stdout, stderr = stderr,
                                        cwd = cwd, env = env)
            
            return self.communicate(process)
        elif launch_mode == self.LAUNCH_MODE_SIBLING:
            if sys.platform.startswith('linux'):
                args.append('&')
            elif sys.platform == 'darwin':
                executable, app_args = args[0], args[1:]
                args = ['open', '-n', '-a'] + [executable]
                if app_args:
                    args.append('--args')
                    args.extend(app_args)
                # end handle app_args
            elif sys.platform == 'win32':
                args = ['start', '/B'] + args
            # end handle shell based forking

            # on posix, the shell behaviour is special, as such as args passed to the shell.
            # For that reason, we have to convert into a string, but at least want to do it properly 
            # in case of whitespace.
            # NOTE: for now, we don't expect or support special shell characters
            cmd = ''
            for arg in args:
                if ' ' in arg:
                    arg = '"%s"' % arg
                cmd += arg + ' '
            # end for each arg to sanitize

            log.log(logging.TRACE, cmd)
            return self.communicate(subprocess.Popen(cmd.strip(), shell=True, cwd = cwd, env=env))
        elif launch_mode == self.LAUNCH_MODE_REPLACE:
            # Cleanup our existing process - close file-handles, bring down user interface
            # We would need a callback here, ideally using some sort of event system
            self._pre_execve()
            os.chdir(cwd)
            ##############################################
            os.execve(args[0], args, env)
            ##############################################
        else:
            raise NotImplementedError("Unknown launch mode: %s" % launch_mode)
        # end 
        
        
    
    ## -- End Subclass Interface -- @}
# end class ProcessControllerDelegate


class MayaProcessControllerDelegate(ProcessControllerDelegate):
    """Customize behaviour to deal better with path-related variables used in maya"""
    __slots__ = ()
    
    context_from_path_arguments = True

    def verify_path(self, environment_variable, path):
        """Deals properly with icon-paths, those are only relevant on linux"""
        if not path.endswith('%B'):
            return super(MayaProcessControllerDelegate, self).verify_path(environment_variable, path)
        # end see if path is a linux iconpath
        
        # If the base does not exist, its invalid. Otherwise we just return it unchanged
        checked_path = super(MayaProcessControllerDelegate, self).verify_path(environment_variable, path.dirname())
        if checked_path is None:
            return None
        return path

# end class MayaProcessControllerDelegate


class KatanaControllerDelegate(ProcessControllerDelegate):
    """Assure we understand the Katana Resource Path as path"""
    __slots__ = ()
    
    def variable_is_path(self, environment_variable):
        """Handle Katana Resources """
        if environment_variable in ('KATANA_RESOURCES', 'KATANA_RESOLUTIONS'):
            return True
        return super(KatanaControllerDelegate, self).variable_is_path(environment_variable)
        
    def variable_is_appendable(self, environment_variable, value):
        """Implements Katana specific special cases"""
        res = super(KatanaControllerDelegate, self).variable_is_appendable(environment_variable, value)
        return environment_variable != 'KATANA_RESOLUTIONS' and res

# end class KatanaControllerDelegate


class MariControllerDelegate(ProcessControllerDelegate):
    """A controller to ease starting Mari with all it's peculiarities"""
    __slots__ = ()

    def pre_start(self, executable, env, args, cwd, resolve):
        """Prevent the browser to be shown"""
        args.insert(0, '--nobrowser')
        return super(MariControllerDelegate, self).pre_start(executable, env, args, cwd, resolve)

# end class MariControllerDelegate


class ThreeDEqualizerControllerDelegate(ProcessControllerDelegate):
    """Make sure custom path variables are handled correctly"""
    __slots__ = ()

    def variable_is_path(self, environment_variable):
        res = super(ThreeDEqualizerControllerDelegate, self).variable_is_path(environment_variable)
        if res:
            return res
        evar = environment_variable.lower()
        return 'python_custom' in evar or evar.endswith('_dir')

# end class ThreeDEqualizerControllerDelegate

## -- End Interface Implementation -- @}

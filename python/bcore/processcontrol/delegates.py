#-*-coding:utf-8-*-
"""
@package bcore.processcontrol
@brief implementations of the interfaces related to process control

@copyright 2012 Sebastian Thiel
"""
__all__ = ['ProcessControllerDelegate', 'DelegateEnvironmentOverride', 'PostLaunchProcessInformation', 
           'MayaProcessControllerDelegate', 'KatanaControllerDelegate', 'DisplayHelpException',
           'ProcessControllerDelegateProxy', 'DisplayContextException', 'MariControllerDelegate']

import os
import sys
import re

import bcore
import yaml

import binascii
import zlib
from cPickle import (
                        loads, 
                        dumps
                    )

import logging

import bcore.core.logging
from bcore.core.environ import ConfigHierarchyEnvironment
from bcore.core.kvstore import (
                                RootKey,
                                KeyValueStoreProvider,
                                KeyValueStoreModifier
                            )
from bcore.core.diff import (
                        NoValue,
                        TwoWayDiff,
                        ApplyDifferenceMergeDelegate
                    )

from bcore.core.component import Environment
from .interfaces import (
                            IProcessControllerDelegate,
                            IPostLaunchProcessInformation
                       )

from bcore.utility import (
                            update_env_path,
                            DictObject,
                            Singleton,
                            LazyMixin,
                            StringChunker
                        )

from .actions import ActionDelegateMixin

from .schema import (
                        controller_schema,
                        process_schema,
                        NamedServiceProcessControllerDelegate
                    )

from bcore.path import Path

log = bcore.core.logging.module_logger('bcore.processcontrol.delegate')


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

class ProcessControllerDelegateProxy(object):
    """A simple proxy which behaves differently based on its input channel arguments"""
    __slots__ = (
                    '_delegate', # delegate we are proxying
                    '_channels'  # a list of channels
                )
    
    def __init__(self, delegate, *channels):
        """Intialize ourselves with a delegate that we are to proxy/override, and stdin, stdout, stderr 
        channels"""
        self._delegate = delegate
        self._channels = channels
        
    def __getattr__(self, name):
        return getattr(self._delegate, name)
        
    # -------------------------
    ## @name Overrides
    # @{
    
    def process_filedescriptors(self):
        """@return our channels"""
        return self._channels
        
    def communicate(self, process):
        """@return process without having communicated if any of our channels was set"""
        if any(self._channels):
            return process
        return self._delegate.communicate(process)
    
    ## -- End Overrides -- @}
    
    
# end class ProcessControllerDelegateProxy
        


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


class DelegateCommandlineOverridesEnvironment(Environment):
    """An environment with a custom initializer to allow storing an arbitrary dict as kvstore override"""
    __slots__ = ()
    
    def __init__(self, name, data = None):
        """Intiailize ourselves and set our kvstore to the given data dictionary, if set
        @param name of environment
        @param data if set, it may be a dictionary or a KeyValueStoreProvider instance. In the former case,
        it will be converted accordingly"""
        super(DelegateCommandlineOverridesEnvironment, self).__init__(name)
        if isinstance(data, KeyValueStoreProvider):
            self._kvstore = data
        elif data:
            # assume dict
            self._kvstore = KeyValueStoreProvider(data)
        # end handle 

# end class DelegateCommandlineOverridesEnvironment


class DelegateEnvironmentOverride(Environment):
    """An environment specifically designed to be used by a delegate to override particular values of our 
    kvstore.
    It knows our base schema and uses it to obtain the unresolved datablock, for being changed by the 
    delegate in a relatively save manner. It will then be written into the environments kvstore
    @note This environment puts itself on the stack to take that burden off the caller !"""
    _category = 'DelegateOverride'
    
    class DifferenceDelegate(ApplyDifferenceMergeDelegate):
        """Handle special types"""
        __slots__ = ()
    
        def _resolve_conflict(self, key, left_value, right_value):
            if isinstance(right_value, NamedServiceProcessControllerDelegate):
                return NoValue
            return super(DelegateEnvironmentOverride.DifferenceDelegate, self)._resolve_conflict(key, left_value, right_value)
    
    # end class DifferenceDelegate
    
    def setup(self, delegate, schema, *args, **kwargs):
        """Initialize this instance with the delegate itself - it will not be stored permanently, but is 
        uesd for callbacks
        @param delegate the one who has instantiated this instance.
        @param schema the schema to use for the override
        @param args arguments to be passed to set_context_override()
        @param kwargs kwargs to be passed to set_context_override()
        @return self
        @note we will put ourselves onto the environment stack for convenience"""
        new_value = bcore.environment.context().value(schema.key(), schema)
        delegate.set_context_override(schema, new_value, *args, **kwargs)
        
        # find only the changed values and write them as kvstore
        prev_value = bcore.environment.context().value(schema.key(), schema)
        delegate = self.DifferenceDelegate()
        TwoWayDiff().diff(delegate, prev_value, new_value)
        
        self._kvstore.set_value(schema.key(), delegate.result())
        return bcore.environment.push(self)
        
# end class ProcessControllerEnvironment


class PostLaunchProcessInformation(IPostLaunchProcessInformation, Singleton, LazyMixin, Plugin):
    """Store the entire kvstore (after cleanup) in a data string in the environment and allow to retrieve it
    @note this class uses a cache to assure we don't get data more often than necessary. It is all static and 
    will not change"""
    __slots__ = (
                     '_data',       # all used as cache
                     '_kvstore',     
                     '_procdata',
                     '_cmdline_overrides',
                     '_hash_map'
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
            self._data = self._decode(''.join(os.environ[k] for k in keys))
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
                self._hash_map = self._decode(os.environ[self.config_file_hash_map_environment_variable])
            # end decode value if present
        else:
            return super(PostLaunchProcessInformation, self)._set_cache_(name)
        # end handle cached attributes
        
    def _yaml_data(self, evar):
        """@return object as loaded from the yaml string retrieved from the given environment variable,
        or None if it was unset
        @note sibling of _store_yaml_data()"""
        yaml_string = os.environ.get(evar, None)
        if yaml_string is None:
            return None
        # end handle uncontrolled process
        return yaml.load(yaml_string)
        
    def _store_yaml_data(self, evar, env, data):
        """Store the given piece of yaml data in the given environment dictionary
        @param evar environment variable
        @param env environment dict
        @param data structure to store
        @note sibling of _yaml_data()"""
        env[evar] = yaml.dump(data)

    @classmethod
    def _encode(cls, data):
        """@return encoded version of data, suitable to be stored in the environment"""
        return binascii.b2a_base64(zlib.compress(dumps(data), 9))
        
    @classmethod
    def _decode(cls, data_string):
        """@return decoded version of the previously encoded data_string"""
        return loads(zlib.decompress(binascii.a2b_base64(data_string)))

    # -------------------------
    ## @name Interface
    # @{
    
    def data(self):
        return self._data
        
    def has_data(self):
        return self.storage_environment_variable in os.environ

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
        
    def store(self, env):
        """Store the data within the environment for later retrieval
        @param env the environment dict to be used for the soon-to-be-started process
        @return self"""
        source = self._encode(bcore.environment.context().data())

        if source:
            # Linux max-chunk size is actually not set, but now we chunk everything
            chunk_size = sys.platform == 'win32' and 1024 * 32 - 2 or 1024*1024
            sc = StringChunker()

            keys = sc.split(source, chunk_size, env)
            env[self.storage_environment_variable] = self.key_sep.join(keys)
        # end handle source too big to be stored
        
        # store process data as well
        self._store_yaml_data(self.process_information_environment_variable, env, bcore.environment.context().value_by_schema(process_schema))

        # Store ConfigHierarchy hashmap for restoring it later
        # merge and store
        hash_map = dict()
        for einstance in bcore.environment.stack():
            if isinstance(einstance, ConfigHierarchyEnvironment):
                hash_map.update(einstance.hash_map())
            # end update hash_map
        # end for each env on stack

        # Always store it, even if empty
        env[self.config_file_hash_map_environment_variable] = self._encode(hash_map)
        return self
        
    def store_commandline_overrides(self, env, data):
        """Store the information in the given kvstore for the process that is about to be launched. He can 
        retrieve the stored information.
        @param env dict to store the data in
        @param data a dictionary or data structure with the commandline overrides, compatible to the 
        main kvstore's schema
        @return self"""
        self._store_yaml_data(self.commandline_overrides_environment_variable, env, data)
        return self
        
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

# end class PostLaunchProcessInformation

## -- End Utilities -- @}


# ==============================================================================
## @name Interface Implementation
# ------------------------------------------------------------------------------
## @{


class ProcessControllerDelegate(IProcessControllerDelegate, ActionDelegateMixin, Plugin):
    """Implements the controller's delegate
    
    Wrapper Arguments
    =================
    
    It is possible to provide arguments that are interpreted only by the wrappers delegate. Those arguments
    start with a triple-dash ('---') and can be the following
    
    See 
    """
    __slots__ = ()
    
    ## This is just to get less surprises when setting up new wrappers ... even though some of this could 
    ## really be controlled by inherited delegates
    _inherit_those_variables = ['PATH',         # Actually to allow other wrapper scripts to work, i.e. maya
                                'HOME',         # used by some software to find local configuration
                               ]
    if sys.platform == 'win32':
        _inherit_those_variables.extend((
                                        'USERNAME',	    # required to have user information (simple)
                                        'SystemRoot'	# required for most APIs to work !
                                ))
    else:
        _inherit_those_variables.extend(('XAUTHORITY',   # just here as a precaution 
                                         'DISPLAY',      # To allow GUIs
                                         'USER',         # Some programs need it, like 3de
                                       ))
    # end handle platforms
    
    ## For the sake of simplicity, we keep a few special cases in the base class implementation, until
    # those packages have their own delegate, that is
    _unappendable_variables = ('OCIO', 'RMANTREE')
    
    ## if True, configuration will be parsed from paths given as commandline argument. This is useful
    # to extract context based on passed files (for instance, for rendering)
    context_from_path_arguments = False
    
    ## A regular expression to check if we have a path
    re_find_path = re.compile(r"^.+[/\\][^/\\]+$")
    
    ## A prefex we use to determine if the argument is destined to be used for the wrapper
    _wrapper_arg_prefix = '---'
    
    ## Separator for key-value pairs
    _wrapper_arg_kvsep = '='
    
    ## adjustable wrap-time logging levels
    _wrapper_logging_levels = ('trace', 'debug')
    
    ## Help for how to use the custom wrapper args
    _wrapper_arg_help = \
    """usage: <wrapper> [---option ...]
    ---<variables>=<value>
        A variable in the kvstore that is to receive the given value, like ---logging.verbosity=DEBUG or
       ---packages.maya.version=2013.2.0
    ---trace|debug
        Set logging verbosity at wrap time to either TRACE or DEBUG
    ---debug-context
        Print the entire context to stderr and abort program execution. Useful to learn about the contet at 
        wrap time.
    ---help
        Prints this help and exits.
        
    Set the BCORE_STARTUP_LOG_LEVEL=DEBUG variable to see even more output from the startup time of the entire
    framework.
    """
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Type used when instanating an environment to keep delegate configuration overrides
    DelegateEnvironmentOverrideType = DelegateEnvironmentOverride
    
    ## -- End Configuration -- @}
    
    def prepare_environment(self, executable, env, args, cwd):
        """Interprets wrapper arguments as identified by their '---' prefix and if required, sets those overrides
        in a custom environment.
        Additionally we will parse paths from the given commandline and use them in the context we build.
        This assumes that the application will also setup this context once the respective scene was loaded.
        """
        # Will be a kvstore if there have been overrides
        kvstore_overrides = KeyValueStoreModifier(dict())
        for arg in args:
            if not arg.startswith(self._wrapper_arg_prefix):
                # For now only find direct, single argument paths.
                path = self._extract_path(arg)
                if not path:
                    continue
                # ignore args that are not paths
                path = Path(path)
                if path.dirname().isdir():
                    bcore.environment.push(ConfigHierarchyEnvironment(path.dirname()))
                # end handle valid directory
                continue
            # end ignore non-wrapper args
            self.handle_argument(arg[len(self._wrapper_arg_prefix):], kvstore_overrides)
        # end for each arg to check
        
        # set overrides
        if kvstore_overrides.keys():
            environment = bcore.environment.push(DelegateCommandlineOverridesEnvironment('wrapper commandline overrides', 
                                                                                      kvstore_overrides))
            PostLaunchProcessInformation().store_commandline_overrides(env, kvstore_overrides.data())
        #end handle overrides
        return super(ProcessControllerDelegate, self).prepare_environment(executable, env, args, cwd)
        
    def variable_is_path(self, environment_variable):
        """base implementation considers those ending with PATH as path variables, or those ending with TREE.
        Arguably, this is a bit fat for a base implementation, but its okay as long as it doesn't match too many
        variables
        Variables ending with home and location are interpreted as paths as well.
        """
        evar = environment_variable.lower()
        return  (evar.endswith('path') or 
                 evar.endswith('paths') or
                (evar != 'home' and evar.endswith('home')) or
                 # Should be done in their own delegate !
                 evar.endswith('tree') or 
                 evar.endswith('LOCATION') or
                 evar == 'OCIO') 
        
    def variable_is_appendable(self, environment_variable, value):
        """Default implementation always assumes paths are appendable, except for a custom set 
        of variables we know (until the respective packages implement their own delegate)"""
        if environment_variable in self._unappendable_variables:
            return False
        return True
        
    def verify_path(self, environment_variable, path):
        """@return allow everything that is an existing path, otherwise drop it, and log the incident"""
        if not path.exists():
            log.warn("%s: '%s' dropped as it could not be read", environment_variable, path)
            return None
        return path

    def pre_start(self, executable, env, args, cwd):
        """@return env unchanged, but assure that X-Specific variables are copied from our current environment
        if they exist. We will not override existing values either.
        Additionally it will apply the transaction to prepare the process launch.
        @note also removed custom wrapper arguments, which are identified by their '---' prefix"""
        self.update_from_os_environment(self._inherit_those_variables, env)
        # remove wrapper args
        new_args = [arg for arg in args if not arg.startswith(self._wrapper_arg_prefix)]

        if self.has_transaction():
            if self.transaction().apply().failed():
                raise self.transaction().exception()
        # end handle transaction

        return (executable, env, new_args, cwd)

    def should_spawn_process(self):
        """@return False"""
        if self.has_transaction():
            return any(op.delegate_must_spawn is not None and op.delegate_must_spawn or False for op in self.transaction())
        # end 
        return False
        
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
        @param arg any argumment provided to the starting process, as parsed during prepare_environment() and
        after wrapper specific arguments where extracted"""
        if not self.context_from_path_arguments:
            return None
        #end early bailout
        match = self.re_find_path.match(arg)
        if not match:
            return None
        return match.group(0)
    
    def update_from_os_environment(self, variables, env, append = False):
        """Update all variables in the given env from their counterpart in os.environ.
        This allows to selectively inherit from your parent environment
        @param variables iterable of environment variables to inherit
        @param env the environment to store the values from os.environ in
        @param append if True, and if the environment variable is a path, it will be appended.
        Otherwise it will be prepended.
        @note this is just a utility, you could easily implement it yourself"""
        for evar in variables:
            if evar in os.environ:
                value = os.environ[evar]
                if self.variable_is_path(evar):
                    update_env_path(evar, value, append = append, environment = env)
                    log.debug("Setting %s = %s, append = %i", evar, value, append) 
                else:
                    log.debug('Setting %s = %s', evar, value)
                    env[evar] = value
                #end handle path variables
            # end if evar is in envrionment
        # end for each xvar
        
    def set_context_override(self, schema, value, *args, **kwargs):
        """Use the given ProcessController schema to safely alter the given context value.
        @note only called by the utility type, DelegateEnvironmentOverride .
        @param schema defined by the ProcessController who is driving the process
        @param value obtained from the global context, matching the schema, with entirely unresolved values.
        @param args defined by the caller
        @param kwargs defined by the caller"""
        raise NotImplementedError("To be defined by subclass")
    
    def new_environment_override(self, *args, **kwargs):
        """Initialize a DelegateEnvironmentOverride instance to allow making selective version overrides. The
        schema used is the one of the ProcessController, allowing full access to all package data
        @note Must be called during prepare_environment() to have an effect
        @param args passed to set_context_override()
        @param kwargs passed to set_context_override()
        @return newly created DelegateEnvironmentOverride instance"""
        return self.DelegateEnvironmentOverrideType(type(self).__name__ + ' Override').setup(self, controller_schema, *args, **kwargs)
        
    def handle_argument(self, arg, kvstore):
        """Method called whenver an argument destined for the wrapper is to be evaluated.
        Subtypes can use it to implement custom argument parsing, based on arguments with the --- prefix.
        The base implementation handles the standard cases
        @param arg argument without the wrapper specific prefix
        @param kvstore a kvstore that can be used to store values that are to be used as overrides
        @throws AssertionError if the argument cannot be handled"""
        if arg == 'help':
            raise DisplayHelpException(self._wrapper_arg_help)
        elif arg in self._wrapper_logging_levels:
            bcore.core.logging.set_log_level(logging.root, getattr(logging, arg.upper()))
            
            if arg == 'debug':
                # print out all files participating in environment stack
                log.debug("CONFIGURATION FILES IN LOADING ORDER")
                for env in bcore.environment.stack():
                    if not isinstance(env, ConfigHierarchyEnvironment):
                        continue
                    #end ignore non configuration items
                    for path in env.config_files():
                        log.debug(path)
                    # end for each path
                # end for each environment
            # end print loaded files
        elif self._wrapper_arg_kvsep in arg:
            # interpret argument as key in context
            key_value = arg
            assert len(key_value) > 2 and self._wrapper_arg_kvsep in key_value, "expected k=v string at the very least, got '%s'" % key_value
            kvstore.set_value(*key_value.split(self._wrapper_arg_kvsep))
            log.debug("CONTEXT VALUE OVERRIDE: %s", key_value)
        elif arg == 'debug-context':
            # We assume environment stack is printed to stderr
            log.info('commandline override kvstore so far:')
            log.info('%s', kvstore)
            raise DisplayContextException("Stopping program to debug context")
        else:
            raise AssertionError("Argument named '%s' unknown to wrapping engine" % arg)
        # end handle arg
    
    ## -- End Subclass Interface -- @}
# end class ProcessControllerDelegate


class MayaProcessControllerDelegate(ProcessControllerDelegate):
    """Customize behaviour to deal better with path-related variables used in maya"""
    __slots__ = ()
    
    context_from_path_arguments = True

    _unappendable_variables = ProcessControllerDelegate._unappendable_variables + ('BCORE_PIPELINE_BASE_PATH', )
    
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

    def pre_start(self, executable, env, args, cwd):
        """Prevent the browser to be shown"""
        args.insert(0, '--nobrowser')
        return super(MariControllerDelegate, self).pre_start(executable, env, args, cwd)

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

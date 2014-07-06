#-*-coding:utf-8-*-
"""
@package bprocess
@brief implementations of the interfaces related to process control

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import (str,
                             PY2,
                             PY3,
                             with_metaclass)

__all__ = ['ProcessControllerDelegate', 'ApplyChangeContext', 'ProxyProcessControllerDelegate']

import os
import sys
import re
import logging
import subprocess

import bapp

import logging

from bapp import StackAwareHierarchicalContext
from bkvstore import ( RootKey,
                       KeyValueStoreModifier )
from bdiff import ( NoValue,
                    TwoWayDiff )

from bcontext import (Context, 
                      PluginMeta,
                      ApplyChangeContext)
from .interfaces import IProcessControllerDelegate

from butility import ( update_env_path,
                       DEFAULT_ENCODING )

from .actions import ActionDelegateMixin

from .schema import ( controller_schema,
                      process_schema,
                      package_manager_schema,
                      proxy_delegate_package_schema,
                      NamedServiceProcessControllerDelegate )

from .utility import PackageDataIteratorMixin
from butility import ( Path,
                       ProxyMeta )

log = logging.getLogger('bprocess.delegate')


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

class SimpleProxyProcessControllerDelegate(object):
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
        # Actually, as the delegate makes these calls on itself, we have to override the instance implementation
        # Currently we do this in a permanent fashion
        self._communicate_orig = self._delegate.communicate
        self._delegate.communicate = self.communicate

        file_descriptors_orig = self._delegate.process_filedescriptors
        self._delegate.process_filedescriptors = self.process_filedescriptors

        try:
            return self._delegate.start(args, cwd, env, spawn)
        finally:
            # restore preview delegate state
            self._delegate.communicate = self._communicate_orig
            self._delegate.process_filedescriptors = file_descriptors_orig
        # end
    ## -- End Overrides -- @}
    
    
# end class SimpleProxyProcessControllerDelegate


class DelegateAwareApplyChangeContext(ApplyChangeContext):
    """@todo documentation"""
    __slots__ = ()

    class DifferenceDelegateType(ApplyChangeContext.DifferenceDelegateType):
        """Handle special types"""
        __slots__ = ()
    
        def _resolve_conflict(self, key, left_value, right_value):
            if isinstance(right_value, NamedServiceProcessControllerDelegate):
                return NoValue
            return ApplyChangeContext.DifferenceDelegateType._resolve_conflict(self, key, left_value, right_value)
    
    # end class DifferenceDelegate

# end class DelegateAwareApplyChangeContext

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
    __slots__ = ('_controller_settings', '_package_name')
    
    ## if True, configuration will be parsed from paths given as commandline argument. This is useful
    # to extract context based on passed files (for instance, for rendering)
    context_from_path_arguments = False
    
    ## A regular expression to check if we have a path
    re_find_path = re.compile(r"^.+[/\\][^/\\\n\t]+$")

    def __init__(self, application, package_name):
        super(ProcessControllerDelegate, self).__init__(application, package_name)
        self._package_name = package_name
        self._controller_settings = \
            self._app.context().settings().value_by_schema(package_manager_schema, resolve=True).environment.variables

    # -------------------------
    ## @name Configuration
    # @{
    
    ## Type used when instanating an environment to keep delegate configuration overrides
    ApplyChangeContextType = DelegateAwareApplyChangeContext

    ## The type we use when instantiating our own context types
    StackAwareHierarchicalContextType = StackAwareHierarchicalContext
    
    ## -- End Configuration -- @}

    def environment_storage_chunk_size(self):
        """@return chunk size in bytes, defining how many characters an environment variable value may help in total"""
        # Linux max-chunk size is actually not set, but now we chunk everything
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
                    self._app.context().push(self.StackAwareHierarchicalContextType(path.dirname()))
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
            if PY2:
                # we operate in unicode, and have to be sure we don't get hit by the ascii default enoding !
                # We just want to get it done, and hope the default encoding does it !
                # Replace should mark characters that we can't do, which might help later debugging
                if isinstance(value, bytes):
                    value = value.decode(DEFAULT_ENCODING, 'replace').encode('ascii', 'replace')
                # end
            # end handle unicode
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
        @note only called by the utility type, ApplyChangeContext .
        @param schema defined by the ProcessController who is driving the process
        @param value obtained from the global context, matching the schema, with entirely unresolved values.
        @param args defined by the caller
        @param kwargs defined by the caller"""
        raise NotImplementedError("To be defined by subclass")
    
    def new_environment_override(self, *args, **kwargs):
        """Initialize a ApplyChangeContext instance to allow making selective version overrides. The
        schema used is the one of the ProcessController, allowing full access to all package data
        @note Must be called during prepare_context() to have an effect
        @param args passed to set_context_override()
        @param kwargs passed to set_context_override()
        @return newly created ApplyChangeContext instance"""
        return self.ApplyChangeContextType(type(self).__name__ + ' Override').setup(self._app.context(),
                                                                                         self.set_context_override,
                                                                                         controller_schema,
                                                                                         *args, **kwargs)
        
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

    def _sanitize_environment(self, env):
        """When in py2/3 compatibility mode, unicode can easily sneak into the env dict keys.
        For some reason, this is forbidden on windows on PY2, but totally fine on posix.
        """
        if os.name != 'nt' or PY3:
            return env
        # end

        new_env = dict()
        for k, v in env.items():
            new_env[k.encode(DEFAULT_ENCODING)] = v.encode(DEFAULT_ENCODING)
        # end for each value to convert

        return new_env

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
        
        env = self._sanitize_environment(env)

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
                args = ['start', '/B', '"App"'] + args
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


class _DelegateProxyMeta(ProxyMeta, PluginMeta):
    """Allows us to use the ProxyMeta with Plugin types, which use a meta-class on their own"""
    __slots__ = ()

# end class _DelegateProxyMeta


class ProxyProcessControllerDelegate(with_metaclass(_DelegateProxyMeta, ProcessControllerDelegate)):
    """A standard delegate, which is general enough to proxy any other delegate as configured by the respective
    package we are used in.

    This is especially useful if you want to have a special delegate implementation for use in task-management,
    which overrides the way the application is launched and communicated to, without losing any special implementation
    by customized delegates that usually do the job.

    This proxy mechanism can be seen as a way to partially override existing implementations, in a configurable 
    fashion.
    """
    __slots__ = ('_proxy')

    # -------------------------
    ## @name Configuration
    # @{
    

    ## Instance attribute at which we will keep our the delegate we are proxying
    _proxy_attr = '_proxy'

    ## The schema used for our root package
    proxy_delegate_package_schema = proxy_delegate_package_schema

    ## -- End Configuration -- @}


    def __init__(self, application, package_name):
        super(ProxyProcessControllerDelegate, self).__init__(application, package_name)
        try:
            self._proxy = self._find_proxy_delegate(package_name)
        except AssertionError:
            raise
        except Exception as err:
            msg = "Couldn't find valid proxy package delegate for package '%s' with error: %s" % (package_name, err)
            raise ValueError(msg)
        # end handle everything else as critical error

    # -------------------------
    ## @name Utilities
    # @{

    def _new_iterator(self, package_name, schema = None):
        """@return an iterator yieliding all packages in standard order as (data, name) tuples, starting 
        at and including the given package_name
        @param schema if not None, it will be used instead of our standard proxy_delegate_package_schema"""
        return PackageDataIteratorMixin()._iter_package_data_by_schema(self._app.context().settings(),
                                                                       package_name, 
                                                                       schema or self.proxy_delegate_package_schema)

    def _find_proxy_delegate(self, package_name):
        """brief docs"""
        for data, name in self._new_iterator(package_name):
            if not data.proxy:
                continue
            # end

            # now within the proxy package chain, search for a package that has a delegate, which in turn is used as
            # proxy
            for pdata, pname in self._new_iterator(data.proxy):
                delegate = pdata.delegate.instance(self._app.context(), self._app, pname)
                if delegate is None:
                    continue
                # end
                return delegate
            # end for each proxy to look for
            msg = "Couldn't find a single delegate in proxy package '%s' (found in '%s')" % (pname, name)
            raise AssertionError(msg)
        # end for each package to iterate

        msg = "Didn't find a proxy delegate for package '%s' as" % package_name
        msg +=" no 'proxy' package was configured - defaulting to ProcessControllerDelegate"
        log.log(logging.TRACE, msg)
        return ProcessControllerDelegate(self._app, package_name)
    
    ## -- End Utilities -- @}

# end class ProcessController

## -- End Interface Implementation -- @}

#-*-coding:utf-8-*-
"""
@package bprocess.components
@brief Provides implementations of certain components that benefit from working together with process control

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from minifuture import str
__all__ = ['ProcessControlContextController', 'ProcessConfigurationIncompatibleError']

import bapp
from .delegates import ControlledProcessInformation
from .schema import ( process_schema,
                      package_schema )

from .utility import (FlatteningPackageDataIteratorMixin,
                      PythonPackageIterator,
                      CommandlineOverridesContext)
from bapp import ( ApplicationSettingsMixin,
                   IContextController,
                   StackAwareHierarchicalContext )
from bkvstore import ( KeyValueStoreSchema,
                       AnyKey )
from bdiff import ( TwoWayDiff,
                    DiffIndexDelegate )
from butility import ( Version,
                       OrderedDict, 
                       abstractmethod )

import logging

log = logging.getLogger('bprocess.components')


class ProcessConfigurationIncompatibleError(IContextController.ContextIncompatible):
    """Thrown to indicate the current process configuration cannot be used in another context"""
    __slots__ = (
                    'index' ## A DiffIndex record containing the exact changes
                )
    
    def __init__(self, msg, index):
        super(ProcessConfigurationIncompatibleError, self).__init__(msg)
        self.index = index
    

# end class ProcessConfigurationIncompatibleError


class ProcessControlContextController(IContextController, ApplicationSettingsMixin,
                                          FlatteningPackageDataIteratorMixin, bapp.plugin_type()):
    """Basic implementation which uses the basic ProcessController implementation to implement 
    simple context tracking for the _before_scene_save() as well as 
    _after_scene_save() methods"""
    __slots__ = (
                    '_initial_stack_len',   ## Length of the stack when this instance was initialized
                    '_context_stack'        ## The context stack we should manipulate
                )
    
    
    ## Describes the data we want to compare within the package data. Add more fields here if required
    _schema = FlatteningPackageDataIteratorMixin.new_controller_schema({
                                                                        'version' : package_schema.version,
                                                                        'requires' : package_schema.requires
                                                                        }) 
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Environment used to load configuration and plugins
    HierarchicalContextType = StackAwareHierarchicalContext
    
    ## If True, plugins will be loaded recursively from all environments we create, i.e. for executable 
    ## and scene contexts)
    load_plugins = False
    
    ## This variable should be False if the _after_scene_save and _after_scene_open callbacks are used
    ## Otherwise the context, even though we changed the scene, will be the one of the previous scene
    restore_stack_if_new_context_is_incompatible = True
    
    ## -- End Configuration -- @}
    
    def __init__(self, context_stack, *args, **kwargs):
        """Intialize our initial stack len with a default value - its just a marker indicating its not set
        to something specific
        @param context_stack usually self._context_stack"""
        super(ProcessControlContextController, self).__init__()
        self._initial_stack_len = None
        self._context_stack = context_stack
        
    
    # -------------------------
    ## @name Overridable Methods
    # Methods subclasses can adapt to their needs, even though it shouldn't be necessary
    # @{
    
    def _push_configuration(self, dirname):
        """Push all configuration found at the given directory and parent folders, loading plugins on the way.
        @return the newly pushed environment of type HierarchicalContextType
        @note subclasses can override it for special handling"""
        env = self._context_stack.push(self.HierarchicalContextType(dirname))
        # Make sure we apply commandline overrides last
        self._context_stack.push(CommandlineOverridesContext())
        if self.load_plugins:
            env.load_plugins()
        # end handle plugin loading
        return env
        
    def _check_process_compatibility(self, kvstore, current_process_kvstore = None, program = None):
        """Verifiy that this process instance is started the way the given context requires it.
        
        This will not be the case if
        
        - Package version changed
        - if packages were added or removed
        
        @param kvstore representing the context that we are supposed to test against
        @param current_process_kvstore kvstore representing the current process's configuration
        Mainly useful during testing. If None, the one obtained from our own process, which obviously
        needs to be wrapped to work
        @param program name of our program, mainly useful for testing. If unset, it will be obtained from the 
        current_process_kvstore
        @throws Exception if converted to string, it describes the issues precisely
        """
        if current_process_kvstore is None:
            if not ControlledProcessInformation.has_data():
                log.debug('skipping process compatability check as we were not launched using process control')
                return
            # check for info
            current_process_kvstore = ControlledProcessInformation().as_kvstore()
        # end handle overrides
        
        program = program or current_process_kvstore.value(process_schema.key(), process_schema, resolve=True).id
        
        current_process_package_configuration = self._flattened_package_tree(program, current_process_kvstore)
        new_process_configuration = self._flattened_package_tree(program, kvstore)
        delegate = DiffIndexDelegate()
        TwoWayDiff().diff(delegate, current_process_package_configuration, new_process_configuration)
        
        index = delegate.result()
        if not index:
            return
        # end no change is the desired state
        
        # Otherwise, prepare an exception message using the diff index
        index_str = '\n'.join(str(rec) for rec in index.values())
        msg = "Process configuration changed - application restart required\n\n%s" % index_str
        log.error(msg)
        raise ProcessConfigurationIncompatibleError(msg, index)
        
    def pop_asset_context(self):
        """Remove all environments pushed onto the stack if they belong to the scene context.
        This is determined just by the number of environments on the stack before we started dealing with
        the scene context
        @return list of popped environments in natural order
        @note needs _initial_stack_len() to be called beforehand"""
        assert self._initial_stack_len is not None, 'call set_static_stack_len at the end of your init()'
        # get rid of previous scene stack
        log.debug("popping scene context")
        return self._context_stack.pop(until_size = self._initial_stack_len)
    
    ## -- End Overridable Methods -- @}
    
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    @abstractmethod
    def _setup_scene_callbacks(self):
        """Set up an application callback to assure this instance is notified before the scene changes
        or after the scene has changed (depending on the capabilities).
        It should adapt the application interface to the change_asset_context() method, which should be
        called.
        """
        
    ## -- End Subclass Interface -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def set_static_stack_len(self, length = None):
        """Set the length of the stack to which it will be considered static, whereas everything else pushed onto
        it is considered dynamic and volatile. Doing so assures that different scene contexts will not affect each other.
        
        @note This function should be called at the end of your init() method, once all of your default and static
        environments have been pushed.
        @param length If None, The length set will be the current length of the stack. Otherwise the given
        length will be used
        @note its valid to call it multiple times, to re-adjust the are of the static context accordingly"""
        self._initial_stack_len = length or len(self._context_stack)
    
    ## -- End Interface -- @}
    
    # -------------------------
    ## @name Interface Implementation
    # @{
    
    def init(self):
        """Initialize our executable and hook up callbacks
        @note convenince method, this way only _setup_scene_callbacks has to be implemented by the host-application
        @return this instance"""
        self._setup_scene_callbacks()
        self.set_static_stack_len()
        return self
        
    def change_asset_context(self, filepath):
        """Change our context from the previous one the to one indicated by the given file.
        This will load configuration and plugins starting at the given filepath, upwards the directory
        tree.
        
        It will also check if the ProcessController configuration is still compatible with the configuration
        this process was launched with. The latter operation is only performed if this process was started
        using the process controller.
        
        @note should be called by subclasses from their respective callbacks
        @param filepath bapp.path.Path instance of filename to change the context to in one way or another
        """
        log.debug("changing scene context to '%s'", filepath)
        
        res = self.pop_asset_context()
        self._push_configuration(filepath.dirname())
        try:
            self._check_process_compatibility(self._context_stack.settings())
            # if this worked, load plugins
            PythonPackageIterator().import_modules()
        except ProcessConfigurationIncompatibleError:
            # If this method fails, we have to undo the previous stack changes, as we are (supposed) to remain
            # in the context of the given file
            if self.restore_stack_if_new_context_is_incompatible:
                for env in res:
                    self._context_stack.push(env)
                # end for each env to put back
            # end should we restore the stack ?
            raise
        # end exception handling
        
        
    ## -- End Interface Implementation -- @}

# end class ContextController

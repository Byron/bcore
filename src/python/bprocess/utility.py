#-*-coding:utf-8-*-
"""
@package bprocess.utility
@brief Misc utilities for use with the package system of process control

@copyright 2013 Sebastian Thiel
"""
__all__ = ['PackageMetaDataChangeTracker', 'FlatteningPackageDataIteratorMixin']

from contextlib import contextmanager
import logging

import bcore
from .controller import PackageDataIteratorMixin
from .schema import (package_meta_data_schema,
                     controller_schema)
from bcore.environ import PersistentSettingsContextStackContextClient
from bkvstore import (KeyValueStoreModifier,
                      PathList)
from butility import OrderedDict

log = logging.getLogger('bprocess.utility')

from bcore import HierarchicalContext
from bprocess import ControlledProcessEnvironment



# ==============================================================================
## @name Context Managers
# ------------------------------------------------------------------------------
## @{

@contextmanager
def file_environment(*paths, **kwargs):
    """A context manager which sets up a a context based on the given file paths. To achieve that, it will 
    alter the current global context as defined in bcore.app().context() to contain all environments obtained when
    creating HierarchicalContext instances for all the given paths.
    @return returned value is the altered bcore.app().context() instance, just for convenience
    @note this will temporarily change the bcore.app().context(), which is a rather expensive operation both in terms
    of IO and CPU
    @param paths any path that should be used to define the future context. If empty, the current 
    environment will not be altered. Each path should be a directory !
    @param kwargs valid keys are 
    + load_plugins default False, if True, plugins will be loaded for all given paths.
    @note usage: file_environment(scene, executable, cwd) as env: env.context() ..."""
    if not paths:
        yield bcore.app().context()
        raise StopIteration
    # end handle empty paths
    
    # This is potentially dangerous, but we only assume to find the pipeline base environment which is 
    # supposed to hold the main pipeline configuration, and which must exist. We will keep this one, 
    # but recreate all others based on the input paths
    size = -1
    for index, env in enumerate(bcore.app().context().stack()):
        if isinstance(env, ControlledProcessEnvironment):
            size = index + 1
            break
        # end check for special environment
    # end for each env
    assert size > -1, "Didn't find ControlledProcessEnvironment on stack"
    
    popped_environments = list()
    try:
        while len(bcore.app().context()) > size:
            popped_environments.append(bcore.app().context().pop())
        # end pop environments
        for path in paths:
            env = bcore.app().context().push(HierarchicalContext(path))
            if kwargs.get('load_plugins', False):
                env.load_plugins()
            # end handle plugins
        # end for each path
        yield bcore.app().context()
    finally:
        if len(bcore.app().context()) > size:
            bcore.app().context().pop(until_size = size)
        # end only pop if it makes sense
        
        # put all environments back, after removing previous ones
        for env in reversed(popped_environments):
            bcore.app().context().push(env)
        # end for each env

## -- End Context Managers -- @}



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


class PackageMetaDataChangeTracker( PersistentSettingsContextStackContextClient, 
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
    
    @todo what we really want is the code to get a path on disk in the user directory, and access to a 
    kvstore with changes applied. Everything else we inherit is adjusted to work for us.
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
        return self._flattened_package_tree(self._package_name, bcore.app().context().context())
    
    def settings_id(self):
        """@return our settings id
        @note this type is already 'asset' aware, which might not be the right spot for it. Should be 
        in derivd type"""
        return self.settings_prefix + '%s.%s' % (service(bcore.IProjectService).id(), self._package_name)
    
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
                except Exception, err:
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

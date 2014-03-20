#-*-coding:utf-8-*-
"""
@package bcore.environ.settings
@brief A module with a user-settings implementation

@copyright 2013 Sebastian Thiel
"""
__all__ = ['PersistentSettings', 'PersistentSettingsEnvironmentStackContextClient']

import bcore
from copy import deepcopy
from bkvstore import (
                                ChangeTrackingJSONKeyValueStoreModifier,
                                KeyValueStoreProvider
                            )
from bcore.component import EnvironmentStackContextClient
from bdiff import (
                            merge_data,
                            AutoResolveAdditiveMergeDelegate
                         )
from bcore.utility import LazyMixin
from .base import PipelineBaseEnvironment


class _PersistentSettingsMergeDelegate(AutoResolveAdditiveMergeDelegate):
    """Makes sure that lists are not concatenated"""
    __slots__ = ()

    def _resolve_conflict(self, key, left_value, right_value):
        """just allow rhs to overwrite lhs"""
        return right_value or left_value

# end class _PersistentSettingsMergeDelegate


class PersistentSettings(ChangeTrackingJSONKeyValueStoreModifier):
    """A utility type to access settings from a read-only kvstore, and and possibly write changes to it to a file 
    containing only the changed values.
    
    When initializing this instance again with similar read-only values, the changes will be re-applied to 
    restore them.
    
    This makes the type particularly useful for keeping user settings and possibly serve as file-database.
    @note all this type does is to facilitate setting up your base data for comparison. Changes still need
    to be written back using the save_changes()
    """
    __slots__ = ()
    
    
    def __init__(self, data, settings_path_or_stream, take_ownership = True):
        """Initialize this instance to write its changes to the given path
        @param data dict-like objectwe should initialize our underlying kvstore with
        @param take_ownership if True, we will assume no one will change the 'data' from the outside
        @param settings_path_or_stream a file-like object to read from. If None, there are no changes applied to the base provided
        by 'data'. Can also be a path to the settings file to read.
        @note we do not support input paths, as we fill ourselves with the given data"""
        super(PersistentSettings, self).__init__(settings_path_or_stream and [settings_path_or_stream] or list(),
                                                 take_ownership)
        
        # now we will have loaded the data at target path, if there was something stored already
        # It shouldn't be the value_data, but the base data
        if self._data():
            # target file was read and contained data 
            # The base data must data, the current_value must be data|target_data,
            if not take_ownership:
                data = deepcopy(data)
            # end handle data copy
            self._base_value_dict = data
            self._value_dict = merge_data(self._value_dict, data, delegate_type = _PersistentSettingsMergeDelegate)
        else:
            # just set the new data directly
            self._set_data(data, take_ownership = take_ownership)
        # end handle data ordering
        
        
    def settings_data(self, stream):
        """@return the deserialized data structure we use as settings.
        @param stream stream with the serialized settings
        @note normally, you would not directly see them as they are merged into a copy of the data this instance
        was initialized with to server as changes"""
        return self.StreamSerializerType().deserialize(stream)
        

# end class PersistentSettings


class PersistentSettingsEnvironmentStackContextClient(EnvironmentStackContextClient, LazyMixin):
    """A type that facilitates the use of settings data for reading and writing.
    
    It will read your information form the global context according to your schema, and provide simple
    means of writing the changes. This allows you to define defaults with all the neatness of the environment
    context and overrides, while storing custom settings transparently.
    
    To be sure your changes are properly tracked, it will keep a Settings instance for you accordingly.
    """
    __slots__ = (
                    '_settings_kvstore',      # our PersistentSettings instance
                    '_settings_data' # our setting data dictionary
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Type of settings to use
    SettingsType = PersistentSettings
    
    ## -- End Configuration -- @}
    
    # -------------------------
    ## @name Subclass Configuration
    # @{
    
    ## Your schema which is used to read data from the kvstore initially. It must be set, and is repeated
    ## here just for documentation. See EnvironmentStackContextClient for more information
    _schema = None
    
    ## -- End Subclass Configuration -- @}
    
    def _settings_path(self):
        """@return the target path to write settings to"""
        return PipelineBaseEnvironment.user_config_directory() / self.settings_id() + PersistentSettings.StreamSerializerType.file_extension
        
    def _initial_settings_value(self):
        """@return nested value to initialize the SettingsType instance with"""
        return self.context_value()
    
    def _set_cache_(self, name):
        if name == '_settings_data':
            self._settings_data = self._settings_kvstore.value_by_schema(self._schema)
        elif name == '_settings_kvstore':
            self._settings_kvstore = self.SettingsType(self._initial_settings_value(), self._settings_path())  
        else:
            return super(PersistentSettingsEnvironmentStackContextClient, self)._set_cache_(name)
        #end handle name
    
    # -------------------------
    ## @name Interface
    # @{
    
    def reset(self):
        """Reset our internal state to cause our settings to be reloaded next time we access them
        @return self
        @note this is similar to re-creating this instance"""
        for attr in self.__slots__:
            try:
                delattr(self, attr)
            except AttributeError:
                pass
            # end ignore exceptions
        #end for each attribute
        return self
    
    @bcore.abstractmethod
    def settings_id(self):
        """@return string id to identify our settings
        A unique id to be used when dealing with settings of all instances of your type
        If settings overlap but use a different schema, the same storage will be used, which is still 
        fine. Therefore it is possible to share the same settings file for multiple subtypes, depending on
        your preference."""
        
    def settings_kvstore(self):
        """@return kvstore that manages our settings underneath. Its useful to obtain just the changed values
        for instance.
        You can also use it to save changes explicitly, but you should only do so to once you have written
        back your data"""
        return self._settings_kvstore
    
    def settings(self):
        """@return a DictObject ready for reading and writing, matching your schema.
        @note this instance keeps ownership of the data
        @note will be evaluated only when requested, thus you will see the most recent data"""
        return self._settings_data
    
    def save_settings(self, output_stream = None, sparse = True):
        """Writes changes done to structure returned by settings() back to its respective store 
        @note should be called before your instance goes out of scope or is deallocated in some way.
        @param output_stream if not None, it will be used instead of the built-in target path, allowing
        you to redirect it
        @param sparse if False, we will write a complete kvstore which includes the changes, effectively
        overriding everything when reading it back.
        @return self"""
        self._settings_kvstore.set_value_by_schema(self._schema, self._settings_data)
        ostream = output_stream or open(self._settings_path(), 'w') 
        self._settings_kvstore.save_changes(ostream, sparse = sparse)
        return self
        
    ## -- End Interface -- @}

# end class PersistentSettingsEnvironmentStackContextClient


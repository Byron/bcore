#-*-coding:utf-8-*-
"""
@package bkvstore.serialize
@brief Contains file type agnostic implementations of value providers and modifiers to allow serialization

@note Read more about
[the YAML language specification](http://en.wikipedia.org/wiki/YAML#Language_elements)
@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['ChangeTrackingSerializingKeyValueStoreModifierBase', 'SerializingKeyValueStoreModifierBase']

import logging


from butility import (Path,
                      InterfaceBase,
                      abstractmethod)

from bdiff import (NoValue,
                   AutoResolveAdditiveMergeDelegate)

from .base import (KeyValueStoreModifier,
                   ChangeTrackingKeyValueStoreModifier)

from .schema import KVPath



# ==============================================================================
## @name Interfaces
# ------------------------------------------------------------------------------
## @{

class IStreamSerializer(InterfaceBase):
    """An interface to allow serialization of objects to a stream
    @todo these classes are so general, they should move somewhere more general too !"""
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{
    
    ## the extension of files we can read or write
    # Can be None if we don't have a specific extension, for instance because we are only writing
    # to sockets
    file_extension = None
    
    ## -- End Configuration -- @}

    @abstractmethod
    def deserialize(self, stream):
        """Produce the originally serialized data structure from the given stream
        @param stream an object providing the read() method
        @return deserialized data structure"""
        return yaml.load(stream, Loader=OrderedDictYAMLLoader) or dict()
    
    @abstractmethod
    def serialize(self, data, stream):
        """Serialize the given data structure into the given stream
        @param data the structure to serialize
        @param stream a stream object providing the 'write' method"""

# end class YAMLKeyValueStoreModifier


## -- End Interfaces -- @}



# NOTE: unfortunately, we cannot make an absolute import here due to cyclic dependencies
class _SerializingKeyValueStoreModifierMixin(object):
    """A base to share common functionality between the base that tracks changes, and the one that doesn't"""
    # Slots don't work anymore, as this type is used in multi-inheritance scenarios
    #__slots__ = (
    #                '_input_paths', # a tuple of input paths
    #            )

    # -------------------------
    ## @name Subclass Configuration
    # @{
    
    ## A delegate taking care of merging multiple read files into one dataset
    SerializingKeyValueStoreModifierDiffDelegateType = AutoResolveAdditiveMergeDelegate
    
    ## A type to use for serialization
    ## To be set by subclass
    StreamSerializerType = None


    ## A key under which all loaded settings files will be stored in the kvstore
    # If None or empty, no setting files will be stored
    settings_key='settings-files'
    
    ## -- End Subclass Configuration -- @}

    ## our logging instance
    log = logging.getLogger("bkvstore.serializer")

    def __init__(self, input_paths, take_ownership = True):
        """Initialize this instance with a set of paths from which to read values and to which to write the
        changed values.

        @param input_paths iterable to paths pointing to files which will be read in order and merged
        into one value store. The merge algorithm will overwrite previous values with new ones.
        The iterable may also yield file-like object which provides a read() method.
        It may be empty, which is when you will have an empty KVStore.
        @param take_ownership has no effect, we always have ownership
        """
        assert self.StreamSerializerType and self.SerializingKeyValueStoreModifierDiffDelegateType
        
        # init with empty dict
        super(_SerializingKeyValueStoreModifierMixin, self).__init__(self.KeyValueStoreModifierDiffDelegateType.DictType())
        self._set_input_paths(input_paths)
        
        # force updating our data
        self.reload()

    def _set_input_paths(self, input_paths):
        """Sets our input paths to the given value"""
        self._input_paths = list()
        for path_or_stream in input_paths:
            if not hasattr(path_or_stream, 'read'):
                # assume its a path
                path_or_stream = Path(path_or_stream)
            # end handle type
            self._input_paths.append(path_or_stream)
        #end for each path
        
    # -------------------------
    ## @name Serialization Interface
    # Functionality to control reading and writing of value data
    # @{

    def reload(self, input_paths=None):
        """Reload all stored values from the paths we were initialized, loosing all changes so far.

        @param input_paths if not None, it is an iterable with new paths to use as input.
        This allows you to reload the storage with a changed set of input files, without having to exchange
        this actual instance. The input_paths iterable may also yield file-like objects which support 
        a 'read' method.
        @note input streams will be closed after rading if possible
        @return this instance
        @note the implementation will catch and log errors that occur while trying to load the files. It will
        not fail though
        @note changes will only be reapplied if our subclass also derives from KeyValueStoreChangeTrackerMixin.
        Otherwise, we will just reload from disk without any special handling
        """
        if input_paths is not None:
            self._set_input_paths(input_paths)
        #end change input paths

        # merge all the data into one base

        ##! [additive example]
        delegate = self.SerializingKeyValueStoreModifierDiffDelegateType()
        streamer = self.StreamSerializerType()

        def load_and_merge_safely(path_or_stream):
            """Load a file and merge the result using our delegate"""
            try:
                # YES: THEY RETURN NONE IF THERE WAS NOTHING, INSTEAD OF DICT. GOD DAMNED ! Interface change !
                stream = path_or_stream
                stream_path = None
                if not hasattr(path_or_stream, 'read'):
                    stream_path = path_or_stream
                    stream = open(path_or_stream)
                # end open stream as needed
                data = streamer.deserialize(stream)
                if hasattr(stream, 'close'):
                    stream.close()
                # end handle stream close

                # Add the path of the loaded configuration to allow referencing it in configuration.
                # This allows configuration to be relative to the configuration file !
                if stream_path and self.settings_key:
                    data.setdefault(self.settings_key, dict())[stream_path.basename().split('.')[0]] = KVPath(stream_path)
                # end place anchor
            except (OSError, IOError):
                self.log.error("Could not load %s file at '%s'", streamer.file_extension, path_or_stream, exc_info=True)
                return
            except Exception:
                self.log.error("Invalid %s file at '%s'", streamer.file_extension, path_or_stream, exc_info=True)
                return
            #end handle exceptions
            # only in the first run, we have no result as basis yet
            self.log.debug("loaded and merged %s file '%s'", streamer.file_extension, path_or_stream)
            base = delegate.result()
            if base is NoValue:
                base = self.KeyValueStoreModifierDiffDelegateType.DictType()
            #end set base
            self.TwoWayDiffAlgorithmType().diff(delegate, base, data)
        #end load_and_merge_safely
        for path_or_stream in self._input_paths:
            load_and_merge_safely(path_or_stream)
        #end for each input path

        # tell our base class to non-destructively update with the new data
        res = delegate.result()
        if res is NoValue:
            # happens if we had no input, and no valid file to read from, just be empty then
            res = self.KeyValueStoreModifierDiffDelegateType.DictType()
        # end handle no value
        
        self._set_data(res)
        return self
        ##! [additive example]
        
    ## -- End Serialization Interface -- @}

    # -------------------------
    ## @name Query Interface
    # Allow to access some of the state of the modifier
    # @{

    def input_paths(self):
        """@return tuple of input paths that we use to read the documentation from"""
        return self._input_paths

    ## -- End Query Interface -- @}
# end class _SerializingKeyValueStoreModifierMixin



# NOTE: unfortunately, we cannot make an absolute import here due to cyclic dependencies
class SerializingKeyValueStoreModifierBase(_SerializingKeyValueStoreModifierMixin, KeyValueStoreModifier):
    """From an iterable of files, merge all obtained documentation into one.
    
    The idea is that the storage can be decomposed into multiple files, which are provided conditionally
    by the owner of this instance. We will merge the resulting data structures into one and provide that to clients.

    As we keep the paths of the source files, we are able to reload them on request while keeping the changes
    that might have been applied in the meanwhile.

    The serialization algorithm is implemented by subclasses, allowing to read and write any type of data
    """
    __slots__ = ()


# end class SerializingKeyValueStoreModifierBase



# NOTE: unfortunately, we cannot make an absolute import here due to cyclic dependencies
class ChangeTrackingSerializingKeyValueStoreModifierBase(_SerializingKeyValueStoreModifierMixin, 
                                                         ChangeTrackingKeyValueStoreModifier):
    """Similar to the SerializingKeyValueStoreModifierBase, but additionally it will track changes (duplicating
    the required amount of memory), and allow you to write back just the changed values.
    """
    __slots__ = ()

    # -------------------------
    ## @name Serialization Interface
    # Functionality to control reading and writing of value data
    # @{

    def save_changes(self, output_stream, sparse = True):
        """Save changed values to the given stream.

        @param output_stream if set to a stream like object (having a write method).
        @param sparse if True, we will only write changed values. If you want to permeate all values
        and override everything once you read them back, sparse should be False
        @throws ValueError if we don't have a target to write to
        @note if there are no changes, nothing will be written
        @note Will catch and log errors when opening the target file automatically
        @return this instance
        @note for performance reasons, this will only work if the subclass also derives from
        KeyValueStoreChangeTrackerMixin. 
        """
        if sparse:
            changes = self.changes()
        else:
            changes = self._data()
        # end handle sparse
        
        if not changes:
            return self
        #end handle unchanged changes
        
        self.StreamSerializerType().serialize(changes, output_stream)
        return self
        
    def load_changes(self, input_stream):
        """Load changes previously saved using save_changes(), so another call to save_changes() will 
        save exactly what you have just loaded
        @param input_stream a stream to deserialize data from
        @return self"""
        return self.set_changes(self.StreamSerializerType().deserialize(input_stream)) 

    ## -- End Serialization Interface -- @}

# end class SerializingKeyValueStoreModifierBase


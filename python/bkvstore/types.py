#-*-coding:utf-8-*-
"""
@package bcore.kvstore.types
@brief Implements a few types based on our base classes

@copyright 2013 Sebastian Thiel
"""
__all__ = ['YAMLKeyValueStoreModifier', 'ChangeTrackingJSONKeyValueStoreModifier', 
           'JSONStreamSerializer', 'YAMLStreamSerializer', 'JSONKeyValueStoreModifier']

import yaml
import json

import bcore
from .persistence import OrderedDictYAMLLoader
from bdiff import AutoResolveAdditiveMergeDelegate
from .serialize import (
                            SerializingKeyValueStoreModifierBase,
                            ChangeTrackingSerializingKeyValueStoreModifierBase
                       )
from bcore.utility import OrderedDict




class YAMLStreamSerializer(bcore.IStreamSerializer):
    """Serialize from and to yaml"""
    __slots__ = ()

    ## the extension of files we can read
    file_extension = '.yaml'


    def deserialize(self, stream):
        """@note can throw yaml.YAMLError, currently we don't use this information specifically"""
        return yaml.load(stream, Loader=OrderedDictYAMLLoader) or dict()
    
    def serialize(self, data, stream):
        yaml.dump(data, stream)

# end class YAMLStreamSerializer


class YAMLKeyValueStoreModifier(SerializingKeyValueStoreModifierBase):
    """Implemnetation for yaml-based stores"""
    __slots__ = ()

    ## the extension of files we can read
    StreamSerializerType = YAMLStreamSerializer

# end class YAMLKeyValueStoreModifier



class JSONStreamSerializer(bcore.IStreamSerializer):
    """Serialize to and from json """
    __slots__ = ()
    
    file_extension = '.json'
    
    def deserialize(self, stream):
        """@note can throw yaml.YAMLError, currently we don't use this information specifically
        @todo can use object_pairs_hook = OrderedDict to load ordered dicts. But it made a test fail because
        suddenly there were different values. Hints at a bug somewhere, but didn't look into it yet"""
        return json.load(stream) or dict()
    
    def serialize(self, data, stream):
        """Makes sure it is human readable
        @note for now, we convert everything to a string, brutally. The KVStore would have to deal with
        converting the string versions back, and it might not work for everything"""
        json.dump(data, stream, indent=4, separators=(',', ': '), default=str)

    

# end class ChangeTrackingJSONKeyValueStoreModifier


class JSONKeyValueStoreModifier(SerializingKeyValueStoreModifierBase):
    """A modifier with change tracking and JSon serialization
    
    @note no support for OrderedDicts just yet
    """
    __slots__ = ()
    
    StreamSerializerType = JSONStreamSerializer

# end class JSONKeyValueStoreModifier


class ChangeTrackingJSONKeyValueStoreModifier(ChangeTrackingSerializingKeyValueStoreModifierBase):
    """A modifier with change tracking and JSon serialization
    
    @note no support for OrderedDicts just yet
    """
    __slots__ = ()
    
    StreamSerializerType = JSONStreamSerializer

# end class ChangeTrackingJSONKeyValueStoreModifier

#-*-coding:utf-8-*-
"""
@package bcore.kvstore.base
@brief Base classes and most fundamental utilities for key value store handling

@copyright 2012 Sebastian Thiel
"""
__all__ = ['KeyValueStoreProvider', 'KeyValueStoreModifier', 'Error', 'NoValueForKeyError', 
           'UnorderedKeyValueStoreModifier', 'ChangeTrackingKeyValueStoreModifier']

import copy


import bcore

from bcore.log import module_logger
from bdiff import (
                            ApplyDifferenceMergeDelegate,
                            TwoWayDiff,
                            RootKey,
                            NoValue,
                            merge_data
                         )
from .diff import (
                    KeyValueStoreProviderDiffDelegate,
                    KeyValueStoreModifierDiffDelegate,
                    KeyValueStoreModifierBaseSwapDelegate
                  )
from bcore.utility import  (
                            OrderedDict,
                            smart_deepcopy
                        )

# ==============================================================================
## \name Exceptions
# ------------------------------------------------------------------------------
# Basic exceptions thrown by the configuration system
## \{

class Error(bcore.Error):
    """Base Type for all exceptions of the configuration system"""
    __slots__ = ()

# end class Error


class NoValueForKeyError(Error, KeyError):
    """Thrown if a value is missing for a given key"""

    def __init__(self, key):
        """Initialze this instance with a key for which there was no value"""
        Error.__init__(self, key)
        KeyError.__init__(self)
        self.args = (key, )

    def key(self):
        """@return key for which there was no value"""
        return self.args[0]

    def __str__(self):
        return "No value for key '%s'" % self.key()

#end class NoDefaultValueForKeyError

## -- End Exceptions -- \}


# ==============================================================================
## \name Base Implementation
# ------------------------------------------------------------------------------
# A foundational implementation which operates on simple nested data-structures
## \{

class KeyValueStoreProvider(object):
    """Implements the KeyValueStoreProviderInterface to read nested values from some storage location.

    These values are assumed to live in a key-value based structure, where the
    value may be a complex nested data structure of built-in types.

    Its designed to be as tolerant to errors as possible without hiding the fact
    that one occurred.

    Simplified Type-Checked Access
    ------------------------------
    The access mode is simplified and type-checked. This means that whenever
    a key is queried, an expected (possibly complex) default value needs to be
    provided as well.

    The value that would be returned is type-checked against the default.
    If the value doesn't exist, it will return the respective default value,
    after a possibly necessary conversion to the default-values type.

    Access a key's value by providing its name. The name may be hierarchical,
    such as `section.option`
    """
    __slots__ = ('_value_dict')
    __metaclass__ = bcore.MetaBase

    ## Our class-wide logging facility
    log = module_logger("bcore.kvstore.base")

    ## our default key separator
    key_separator = KeyValueStoreProviderDiffDelegate.key_separator

    ## The algorithm we use to diff trees
    TwoWayDiffAlgorithmType = TwoWayDiff

    ## The delegate for the diff algorithm
    DiffProviderDelegateType = KeyValueStoreProviderDiffDelegate

    def __init__(self, value_dict, take_ownership=True):
        """Initialize this instance with the value_dict which contains the
        values to be retrieved or modified
        @param value_dict (nested) dictionary of built-in types or custom
        types which can be serialized and deserialized
        @param take_ownership if True, we will assume the dict will only be handled by us, so we assume ownership.
        This is the default. Otherwise we will copy the dicts contents."""
        for attr in ('__getitem__', 'keys'):
            assert hasattr(value_dict, attr), "Dictionary type (%s) needs to implement %s" % (value_dict, attr)    
        #end for each attr
        self._value_dict = NoValue
        self._set_data(value_dict, take_ownership)
              
    def __str__(self, path = [], indention = 0):
        import yaml
        return yaml.dump(self._value_dict)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self._value_dict))

    # -------------------------
    ## @name Interface Implementation
    # @{

    def value(self, key, default, resolve=False):
        """Query the value for the given key

        @param key a name string which may be made up of multiple names, each
        separated by a period, e.g. `simpleoption` or `section.option`.
        You may also retrieve whole sections, like 'section' or section.subsection.
        @param default the desired default value of the appropriate type.
        It may be a complex nested type as well.

        If you don't expect any default, set it to an empty dict, e.g. dict()
        @param resolve if True, format specifications within the value string will be resolved using all
        data available within this kvstore.
        
        For example, this allows to resolve formats like {site.name}, and many more.
        See http://docs.python.org/2/library/string.html#formatstrings for more information.
        @return a deep copy of the stored value or a read-only deep copy
        of the default value.

        The default value will be returned if there was no value
        at the given key, or if the value's type(s) did not match and could not be
        converted to the respective default value.

        As the value may be complex, parts of the value might be converted to
        their respective default value, others may not.

        In any way its to be assured that changes to the returned value are not
        affecting the in-memory representation of the original values.
        @throw If no default value is provided, as it is None, a `NoValueForKeyError` is thrown"""
        # value can be None - we diff against it anyway
        value = self._resolve_value(key, self._value_dict)
        args = [key, self.log]
        if resolve:
            args.append(self._value_dict)
        # end handle resolver
        
        delegate = self.DiffProviderDelegateType(*args)
        self.TwoWayDiffAlgorithmType().diff(delegate, value, default)

        value = delegate.result()
        if value is NoValue:
            # neither the default nor the stored value provided a value
            raise NoValueForKeyError(key)
        #end handle no value
        return value
        
    def value_by_schema(self, schema, resolve=False):
        """Similar to value(), but a single schema is enough to obain the value
        @return a deep copy of data conforming to the given schema"""
        return self.value(schema.key(), schema, resolve=resolve)
        
    def has_value(self, key):
        """@return true if there is a value stored for the given key"""
        return self._resolve_value(key, self._value_dict) is not NoValue
        
    def keys(self, base_key=RootKey):
        """@return a list of key-names available under the given base. If the base didn't exist, the returned
        list is empty.
        @param base_key if
        RootKey, you will receive all top-level keys. Otherwise it is a string of tokens
        separated by the `key_separator`, e.g. 'hello.world'
        """
        base_dict = self._value_dict
        if base_key is not RootKey:
            base_dict = self._resolve_value(base_key, base_dict)
        #end resolve base
        if base_dict is NoValue:
            return list()
        #end handle missing key
        return base_dict.keys()
        
    def data(self):
        """@return a copy of our data dictionary
        @note the copy is required only to prevent modifications
        """
        return copy.deepcopy(self._data())

    ## -- End Interface Implementation -- @}

    # -------------------------
    ## @name Subclass Utilities
    # @{

    @classmethod
    def _split_key(cls, key):
        """@return key split into tokens, separator is '.'"""
        return key.split(cls.key_separator)

    @classmethod
    def _resolve_value(cls, key, value_dict):
        """@return value_at_key or None
        Resolve the key recursively and query the respective value in the
        nested value dict.
        None is returned if there was no corresponding value in the value dict.
        Either one of the value or default value may be None
        @param cls this type (doxygen wants it)
        @param key either a dot separated key string, or RootKe
        @param value_dict dictionary with nested values"""
        if key is RootKey:
            return value_dict
        # end handle root key
        tokens = key.split(cls.key_separator)
        for token in tokens:
            try:
                value_dict = value_dict[token]
            except KeyError:
                return NoValue
            #end handle missing key
        #end while there are tokens to resolve
        return value_dict
        
    def _set_data(self, data_dict, take_ownership=True):
        """Set ourselves to represent the given data
        @param data_dict a dictionary type keeping our data
        @param take_ownership if True, there is no need to make a copy
        """
        value_dict = data_dict
        if not take_ownership:
            value_dict = copy.deepcopy(value_dict)
        # end handle take ownership
        self._value_dict = value_dict
        return self

    ## -- End Subclass Utilities -- @}

    # -------------------------
    ## @name Subclass Interface
    # @{

    def _data(self):
        """@return our internal data dictionary

        It may be useful for serialization purposes
        """
        return self._value_dict

    ## -- End Subclass Interface -- @}
# end class KeyValueStoreProvider


class KeyValueStoreModifier(KeyValueStoreProvider):
    """Allows to change existing storage by setting values or removing them
    entirely.

    Type-Checked Data Modifications
    -------------------------------
    The interface is supposed to assure data consistency, therefore each value
    change is checked with the possibly complex data type of the existing value.

    Details
    -------
    Implements the  KeyValueStoreModifierInterface such that we can change a nested stored value using a
    two-way merge algorithm.

    Generally, we will keep two trees, one is the base value, one is a copy which will actually be modified.
    Whenever there is the need to determine changes, we can just diff the two trees accordingly.

    @note we are also value provider as it is common to have read access when you have write-access too.
    """
    __slots__ = ()

    KeyValueStoreModifierDiffDelegateType = KeyValueStoreModifierDiffDelegate

    @classmethod
    def copy(cls, kvstoremodifier):
        """ copy constructor """
        return cls(kvstoremodifier.data())

    def _resolve_value_with_dict(self, key, initial_tree_value):
        """Given the fully qualified key, find the parent tree in self._value_dict or create it if required.

        Iterate through the dicts at key-tokens of initial_tree_value until we reach the parent part of the
        leaf portion of the fully qualified key, creating missing parents on the way.

        @param key fully qualified key
        @param initial_tree_value tree-like value that will be used initially .
        It will be changed, as new children of the same type will be added
        @return tuple(parent_tree, leaf_key)
        @note if a key 'section.option' is given, you receive the tree for 'section' and the leaf-key 'option'.
        """
        if key is RootKey:
            return initial_tree_value, RootKey
        tokens = key.split(self.key_separator)
        value = initial_tree_value
        while len(tokens) > 1:
            value = value.setdefault(tokens.pop(0), type(initial_tree_value)())
        #end while we have n - 1 tokens
        return value, tokens[0]

    # -------------------------
    ## @name Interface Implementation
    # @{

    def set_value(self, key, new_value):
        """Set the value associated with the given key to a new value in a
        type-safe fashion

        @param key a name which may be composed of multiple dot-separated names,
        such as `simpleoption` or `section.option`. Can also be the special instance RootKey, to indicate
        new value should be interpreted relative to the root of the dictionary.
        If no value exists at the given key, it will be created.
        @param new_value a possibly complex value.

        It will be checked against the existing value to verify the types of the
        corresponding entries are correct or convertible.

        If a port of the new value is not of the correct type.
        @return this instance, allowing chained calls.
        """
        # get existing value, which may be None
        value = self._resolve_value(key, self._value_dict)
        delegate = self.KeyValueStoreModifierDiffDelegateType(key, self.log)
        self.TwoWayDiffAlgorithmType().diff(delegate, value, new_value)

        # find the spot for the new value to be placed - its technically the parent of value
        # ignore what value was (could be None), and start searching the parent from the root tree
        value, leaf_key = self._resolve_value_with_dict(key, self._value_dict)
        if leaf_key is RootKey:
            # NOTE: Should be use _set_data() here ?
            self._value_dict = delegate.result()
        else:
            value[leaf_key] = delegate.result()

        return self
        
    def set_value_by_schema(self, schema, new_value):
        """Similar to set_value, but the key will be taken from the given schema directly using schema.key().
        @note counterpart of value_by_schema
        @param schema whose key to use
        @param new_value the possibly nested value to set
        @return this instance"""
        return self.set_value(schema.key(), new_value)

    def delete_value(self, key):
        """Delete the value associated with the given key from the storage
        @param key a name which may be composed of multiple, dot-separated names.
        Its not an error if the key does not have a value (i.e. it doesn't exist)
        as this is exactly what the caller intends.
        @return this instance, allowing chained calls
        """
        # only delete it if the key exists
        value = self._resolve_value(key, self._value_dict)
        if value is NoValue:
            # just ignore cases where the key doesn't exist as this is what the user wants anyway
            self.log.debug("Value at key '%s' didn't exist for deletion - ignoring it", key)
            return self
        #end if there is no value
        value, leaf_key = self._resolve_value_with_dict(key, self._value_dict)
        del(value[leaf_key])

        return self

    ## -- End Interface Implementation -- @}

# end class KeyValueStoreModifier


class ChangeTrackingKeyValueStoreModifier(KeyValueStoreModifier):
    """A base tracking changes to allow to query and re-apply them if the underlying data changes
    
    @note Make sure it is listed before the KeyValueStore base in your base class array
    """
    __slots__ = (
                    '_base_value_dict'          # copy of the _value_dict
                )
    
    ## A delegate to pick up changes and re-apply them to a different base data structure
    KeyValueStoreModifierBaseSwapDiffDelegateType = KeyValueStoreModifierBaseSwapDelegate
    ## A delegate to find differences between a base and actual values, which is used to find changes
    KeyValueStoreModifierApplyDifferenceDelegateType = ApplyDifferenceMergeDelegate
    
    
    def __init__(self, value_dict, take_ownership=True):
        """Initialize this instance and keep a copy of the original value for later comparison"""
        # need initialization here as super call will call our set-data
        self._base_value_dict = NoValue
        super(ChangeTrackingKeyValueStoreModifier, self).__init__(value_dict, take_ownership=take_ownership)
        assert self.KeyValueStoreModifierApplyDifferenceDelegateType
        
        # We must not call our base, otherwise python detects a chain and doesn't get back here
        self._set_data(self._value_dict, take_ownership = take_ownership)

    # -------------------------
    ## @name Subclass Interface
    # Subclasses may use this to update the data contained in the modifier
    # @{

    def _set_data(self, data_dict, take_ownership=True):
        """Substitute our base value with the given data dictionary.

        The operation will be such that we will

        1. Diff our value with the previously stored base value
        2. Exchange the base value with the provided data dict
        3. Reapply the differences

        All this is done to assure consistency with previous changes
        We expect our delegate type to perform all this at once.
        @param data_dict a dictionary whose type matches our data dictionary. The data dictionary will be copied
        to assure we do not keep links to the outside world (in case it is changed), unless take_ownership is True
        @param take_ownership if True, the input dict will not be copied. This is the default
        @return this instance
        """
        if not isinstance(data_dict, self.KeyValueStoreModifierDiffDelegateType.DictType):
            raise TypeError("Input data was of type %s, we expected %s"
                            % (type(data_dict), self.KeyValueStoreModifierDiffDelegateType.DictType))
        #end instance type check
        
        if self._value_dict is NoValue:
            super(ChangeTrackingKeyValueStoreModifier, self)._set_data(data_dict, take_ownership)
        # end initialize value dict
        
        if not take_ownership or data_dict is self._value_dict:
            # The data_dict check has to be done in case someone feeds us our own data dict to make an update
            data_dict = copy.deepcopy(data_dict)
        # end handle ownership
        
        # initial value ? Then we don't have to diff anything
        if self._base_value_dict is NoValue:
            # Need to copy here, as this dict is already owned by our provider - thus is a requirement
            self._base_value_dict = data_dict
        else:
            # otherwise, diff base and current value and apply the changes to a copy of data dict
            # This copy will be our new current value, whereas a copy of the original input dict
            # will be the new base
            delegate = self.KeyValueStoreModifierBaseSwapDiffDelegateType(data_dict)
            self.TwoWayDiffAlgorithmType().diff(delegate, self._base_value_dict, self._value_dict)

            self._base_value_dict = data_dict
            self._value_dict = delegate.result()
        #end handle base value dict
        assert self._value_dict is not self._base_value_dict
        
        return self
    
    ## -- End Subclass Interface -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def changes(self):
        """@return a dictionary which contains all added and changed values
        @note deleted values are, for obvious reasons, not included
        """
        delegate = self.KeyValueStoreModifierApplyDifferenceDelegateType()
        assert self._base_value_dict is not NoValue and self._value_dict is not NoValue
        self.TwoWayDiffAlgorithmType().diff(delegate, self._base_value_dict, self._value_dict)
        return delegate.result()
    
    def set_changes(self, data):
        """Set the given data structure as changes, so that changes() would return that exact structure
        This will also discard any previous changes that might currently exist.
        @return self"""
        if data:
            self._value_dict = merge_data(data, self._value_dict)
        # end handle re-apply changes
        return self
    
    ## -- End Interface -- @}
    
# end class ChangeTrackingKeyValueStoreModifier


class UnorderedKeyValueStoreModifier(KeyValueStoreModifier):
    """Same as KeyValueStoreModifier, but uses without an ordered dictionary type.
    @note its just a utility type for now, it requires quite a bit of boiler plate to change the dictionary
    type, which might want to be improved."""
    __slots__ = ()
    
    class DiffDelegate(KeyValueStoreModifierDiffDelegate):
        """Uses an unordered Dict"""
        __slots__ = ()
    
        DictType = dict
    # end class DiffDelegate
    
    KeyValueStoreModifierDiffDelegateType = DiffDelegate 
    
# end class UnorderedKeyValueStoreModifier
    


## -- End Yaml Implementation -- \}



#-*-coding:utf-8-*i-
"""
@package bcore.kvstore.schema
@brief A module with implementations to help to show and verify the current storage schema

@copyright 2012 Sebastian Thiel
"""
__all__ = [ 'KeyValueStoreSchema', 'ValidatedKeyValueStoreSchema', 'KeyValueStoreSchemaValidator', 'SchemaError',
            'InvalidSchema', 'RootKey', 'StringList', 'IntList', 'FloatList', 'PathList', 'TypedList', 
            'ValidateSchemaMergeDelegate', 'ValidatedKeyValueStoreSchema']

from bcore.path import Path

from bcore.log import module_logger
from bdiff import (
                            DiffRecord,
                            DiffIndexDelegate,
                            AdditiveMergeDelegate,
                            TwoWayDiff,
                            NoValue,
                            RootKey
                         )

from .diff import transform_value

from bcore.kvstore.base import (
                                    Error,
                                    KeyValueStoreProvider
                                )

from bcore.utility import DictObject

log = module_logger('bcore.kvstore.schema')

# ==============================================================================
## \name Exceptions
# ------------------------------------------------------------------------------
## \{

class SchemaError(Error):
    """Base for all schema errors"""
    __slots__ = ()
    
# end class Error


class InvalidSchema(SchemaError):
    """Thrown if the schema used for validation is invalid"""

## -- End Exceptions -- @}


# ==============================================================================
## \name Utility Structures
# ------------------------------------------------------------------------------
## \{

class SchemaDiffRecord(DiffRecord):
    """A simple structure containing additional information about why the schema is not correct in this case"""
    __slots__ = (
                    '_message'          # a message describing the issue - for now its just for the end-user
                )

    # R0913 too many arguments - its okay here I believe
    # pylint: disable-msg=R0913
    def __init__(self, key, value_left, value_right, change_type, message):
        """Initialize the instance """
        super(SchemaDiffRecord, self).__init__(key, value_left, value_right, change_type)
        self._message = message

    # -------------------------
    ## @name Interface
    # @{

    def message(self):
        """@return a message indicating the nature of the schema issue"""
        return self._message

    ## -- End Interface -- @}

# end class SchemaDiffRecord

class TypedList(list):
    """A list which only allows objects of a specific type, or of a list-subtype.
    If the conversion failed, the failed value will be represented by a default-constructed instance of the
    desired type
    @note meant to be used within a KeyValueStoreSchema"""
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # documentation
    # @{
    
    ## Type each member of the list should have
    MemberType = None
    
    ## -- End Configuration -- @}
    
    def __new__(cls, *args):
        assert cls.MemberType is not None
        if args:
            args = (transform_value(args[0], cls._transform),)
        return list.__new__(cls, *args)
        
    @classmethod
    def _is_valid_member(cls, value):
        """@return True if the given value would be a valid member"""
        return isinstance(value, cls.MemberType)
    
    @classmethod
    def _transform(cls, value):
        if cls._is_valid_member(value):
            return value
        # end handle value is valid already
        try:
            return cls.MemberType(value)
        except Exception, err:
            msg = "Conversion of '%s' to type %s failed with error: %s"
            log.error(msg, value, cls.MemberType.__name__, str(err))
            return cls.MemberType()
        # end handle conversion
        
    def append(self, value):
        """Append a type-checked value
        @return actually added value"""
        value = transform_value(value, self._transform)
        list.append(self, value)
        return value
        
# end class TypedList


class StringList(TypedList):
    """A list just for Strings - for use in KeyValueStoreSchema instances only"""
    __slots__ = ()
    
    MemberType = str
        
# end class StringList


class IntList(TypedList):
    """A list just for Integers - for use in KeyValueStoreSchema instances only"""
    __slots__ = ()
    
    MemberType = int
        
# end class IntList


class FloatList(TypedList):
    """A list just for floats - for use in KeyValueStoreSchema instances only"""
    __slots__ = ()
    
    MemberType = float
    
    
class PathList(TypedList):
    """A list just for Paths - for use in KeyValueStoreSchema instances only"""
    __slots__ = ()
    
    MemberType = Path
    
# end class IntList

## -- End Utility Structures -- @}


# ==============================================================================
## \name Schema Diff Delegates
# ------------------------------------------------------------------------------
# Custom Delegates to help verifying the schema in various ways.
## \{

# W0703 catch exception is bad - we don't know it more precisely though, its intended !
# pylint: disable-msg=W0703
class ValidateSchemaMergeDelegate(AdditiveMergeDelegate):
    """Records clashes, and builds up a merged value of individual schemas"""
    __slots__ = (
                    '_clashing_keys'         # list of qualified keys which happen to clash with existing keys
                )

    def reset(self):
        super(ValidateSchemaMergeDelegate, self).reset()
        self._clashing_keys = list()

    def _resolve_conflict(self, key, left_value, right_value):
        """Return the newest value and record the key which clashed"""
        self._clashing_keys.append(self._qualified_key(self._to_string_key(key)))
        return right_value

    def clashing_keys(self):
        """@return the list of clashing keys
        @note its modifiable"""
        return self._clashing_keys

# end class ValidateSchemaMergeDelegate


class ValidateKeyValueStoreDiffIndexDelegate(DiffIndexDelegate):
    """Records issues found when diffing the information in a KeyValueStore provider with a collected schema"""
    __slots__ = ()

    DiffRecordType = SchemaDiffRecord

    def register_change(self, key, left_value, right_value, change_type):
        """Record only problematic keys
        @param key unqualified key, suitable for the current tree level
        @param left_value value from value store
        @param right_value value in schema
        @param change_type respective change type"""
        msg = None
        qualified_key = self._qualified_key(self._to_string_key(key))
        if change_type is self.added:
            msg = "Schema value at key '%s' doesn't have a corresponding value in the store" % qualified_key
        elif change_type is self.modified:
            try:
                type(right_value)(left_value)
            except Exception:
                msg = "Stored value %s('%s') at key '%s' could not be converted to the desired schema type %s"
                msg %= (type(left_value), left_value, qualified_key, type(right_value))
            #end test conversion
        #end handle change_type

        if msg is not None:
            record = self.DiffRecordType(qualified_key, left_value, right_value, change_type, msg)
            self._diff_index[qualified_key] = record
        #end handle record creation

# end class ValidateKeyValueStoreDiffIndexDelegate
## -- End Schema Diff Delegates -- @}


# ==============================================================================
## \name Base Classes
# ------------------------------------------------------------------------------
## \{

class KeyValueStoreSchemaValidator(list):
    """collects a bunch of schemas when they are created, which allows them to be verified"""
    __slots__ = (
                    '_key_separator'        # separator between the keys
                )
    
    ValidateSchemaMergeDelegateType = ValidateSchemaMergeDelegate
    
    def __new__(cls, *args, **kwargs):
        """Initialize a new instance with an optional provider type.
        @param cls
        @param args any args that a list takes
        @param kwargs - only one allowed argument: *key_separator*, which is a key-value argument, and defines
        the separator for nested keys
        """
        instance = list.__new__(cls, *args)
        instance._key_separator = kwargs.get('key_separator', KeyValueStoreProvider.key_separator)
        return instance

    def validate_schema(self):
        """Merges all contained schemas into one and tests for duplicate key assignments.
        @return tuple((data, list(key,...))) a tuple of the merged schema as a data dict
        and a list of fully qualified keys which are clashing.
        If this list is empty, there are no clashes and the schema is generally correct.
        @note you may initialize a KeyValueStoreProvider with the data in order to access the merged data
        at the clashing keys
        """
        delegate = self.ValidateSchemaMergeDelegateType()
        make_dict = delegate.DictType

        for schema in self:
            base = delegate.result()
            if base is NoValue:
                base = make_dict()
            #end handle base
            # put the schema temporarily to the right spot in the hierarchy according to its key information
            if schema.key() is not RootKey:
                root_tree = parent_tree = make_dict()
                tokens = schema.key().split(self._key_separator)
                while len(tokens) > 1:
                    child_tree = make_dict()
                    parent_tree[tokens.pop(0)] = child_tree
                    parent_tree = child_tree
                #end while we have tokens
                parent_tree[tokens[0]] = schema
            else:
                root_tree = schema
            #end require parent
            TwoWayDiff().diff(delegate, base, root_tree)
        # end for each schema
        return (delegate.result(), delegate.clashing_keys())

    def validate_provider(self, kvs_provider):
        """Assure that the stored value in the given provider matches this schema. This means
        that:

        - **Every** key in the schema must have a corresponding value in the value provider
        - **Every** value in the kvs_provider must be equivalent or convertible to the respective
          one in the schema.

        @param kvs_provider a `KeyValueStoreProvider` instance.
        @return @ref bdiff.delegates.DiffIndex "DiffIndex" with SchemaDiffRecord instances. If its empty,
        there are no errors.
        @throws InvalidSchema when this schema is not valid by itself. When validating the provider,
        the schema will be validated automatically, and cause this error if its not valid
        """
        schema_data, clashing_keys = self.validate_schema()
        if clashing_keys:
            raise InvalidSchema(clashing_keys)
        # end assure valid schema
        delegate = ValidateKeyValueStoreDiffIndexDelegate()
        TwoWayDiff().diff(delegate, kvs_provider._data(), schema_data)

        return delegate.result()
        
    @classmethod
    def merge_schemas(cls, schemas, merge_root_keys = True):
        """@return a merged schema, being a combination of all given schemas.
        @param cls
        @param schemas a tuple or list of schema
        @param merge_root_keys if True, and if all schema's have the same root key, the new schema will
        have that root key. Otherwise the new schema's root key will be RootKey, no matter what
        @throws AssertionError of there are overlapping keys, which would mean you have specified the same
        key multiple times, with different types. Thus, this can be configured a save merge."""
        all_roots = set(s.key() for s in schemas)
        self = cls(schemas)
        merged_schema, clashing_keys = self.validate_schema()
        if clashing_keys:
            raise AssertionError("Schema's have overlapping keys with different types at keys: %s" % ', '.join(clashing_keys))
        # end check for clashes
        
        
        if merge_root_keys and len(all_roots) == 1:
            root_key = schemas[0].key()
            return KeyValueStoreSchema(root_key, merged_schema[root_key])
        else:
            return KeyValueStoreSchema(RootKey, merged_schema)
        # end re-obtain Root Key
        
        
# end class KeyValueStoreSchemaValidator


class KeyValueStoreSchema(DictObject, dict):
    """Defines the default types and values of dictionaries to be used as default value when querying
    stored values.

    Each schema consists of the key at which it resides, and represents the actual and possibly nested value.

    Instances will be collected at instantiation and will be merged against the accumulation of all previous
    instances. If there is one value that already exists, an exception will be thrown right away.

    You should assign your schemas to a variable that can be used as default when querying the your actual
    stored value. It will be used as template to verify the stored value against.
    
    @attention the `dict` base is unused, it merely serves as a marker to allow the diffing engine to work 
    with it more natively.
    """
    __slots__ = (
                    '_key'  # key at which our data is positioned
                )

    def __init__(self, key, in_dict):
        """Initialize this instance with the given key and data

        @param key the key identifying the location of the given dictionary. May be RootKey to indicate
        that all data keys should be imported directly into the root namespace. This can be useful for single
        values for instance
        @param in_dict a dictionary with keys and values representing the actual stored data
        """
        super(KeyValueStoreSchema, self).__init__(in_dict)
        self._key = key

    # -------------------------
    ## @name Interface
    # @{

    def key(self):
        """@return the schema's key"""
        return self._key

    ## -- End Interface -- @}

# end class KeyValueStoreSchema


class ValidatedKeyValueStoreSchema(KeyValueStoreSchema):
    """Similar to KeyValueStoreSchema, but is tied to a validator instance to simplifiy validation"""
    __slots__ = ()
    
    ## Shared instance of the current validator, used by all instances of this type
    _validator = None

    def __init__(self, key, in_dict, validator = None):
        """Initialize this instance with the given key and data

        Additionally it will register ourselves with the currently set collector
        @param validator if not None, it must be an instance of type KeyValueStoreSchemaValidator . It will override
        the validator currently set, see `set_validator(...)`
        @param key
        @param in_dict"""
        super(ValidatedKeyValueStoreSchema, self).__init__(key, in_dict)
        
        if validator is None:
            validator = self._validator
        #end handle validator instance
        assert validator is not None, "no validator set - use KeyValueStoreSchema.set_validator(...) to do that"
        validator.append(self)
        
    # -------------------------
    ## @name Class Interface
    # Methods to configure all schemas at once
    # @{

    @classmethod
    def set_validator(cls, collector):
        """Make the given collector the one to be used for each following instantiation of a schema
        @param collector an instance of type KeyValueStoreSchemaValidator
        @param cls our class, for doxygen
        @return this type
        """
        cls._validator = collector
        return cls

    @classmethod
    def collector(cls):
        """@return the collector which is currently set. Can be None if it was not yet set"""
        return cls._validator

    ## -- End Class Interface -- @}


    

# end class ValidatedKeyValueStoreSchema

## -- End Base Classes -- @}

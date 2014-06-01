#-*-coding:utf-8-*-
"""
@package bkvstore.diff
@brief Contains our diff implementation

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str

__all__ = [ 'KeyValueStoreProviderDiffDelegate', 'KeyValueStoreModifierDiffDelegate', 
            'KeyValueStoreModifierBaseSwapDelegate', 'AnyKey', 'RelaxedKeyValueStoreProviderDiffDelegate']

import copy
from functools import partial

from bdiff import ( NoValue,
                    TreeItem,
                    MergeDelegate,
                    ApplyDifferenceMergeDelegate )

from butility import ( smart_deepcopy,
                       OrderedDict )

from .utility import KVStringFormatter


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

## Amount of iterations when resolving values in kvstore
MAX_ITERATIONS = 6

class AnyKey(object):
    """A marker key that will match any key.
    
    = Constraints =
    
    * may only be used once per hierarchy level
    * may not be mixed with other types of keys
    
    Use this type to allow a schema to be used for multiple similar structures in a kvtree """
    __slots__ = ()
    
# end class AnyKey


def transform_value(value, transformator):
    """Transforms the given value using the given transformator recursively.
    @param value (nested) list or scalar value
    @param transformator function(value) => transformed_value
    """
    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = transform_value(item, transformator)
        # end for each value
    else:
        value = transformator(value)
    # end handle list recursion
    return value
# end recursor


## -- End Utilities -- @}


# ==============================================================================
## \name Base Types
# ------------------------------------------------------------------------------
## \{

class _KeyValueStoreDiffDelegateBase(MergeDelegate):
    """Common base class for all of our merge-delegate implementations which require a log
    
    If it received a data object/dictionary (expected to have getattr access for keys), it will be used
    to resolve values based on python's built-in string.format() function"""
    __slots__ = (
                    '_log',                      # logger instance
                    '_base_key',                 # base key at which value resides
                    '_data',                     # optional reference to our parent's data
                    'delete_empty_trees'         # per instance value of the respective class value
                )

    ## we use dots a separator
    key_separator = '.'

    # We really need an ordered dict
    assert issubclass(MergeDelegate.DictType, OrderedDict), "We are expecting an OrderedDict as Dictionary"

    def __init__(self, base_key, log, data=None):
        """Initialize the instance
        @param log logger instance to use to provide information
        @param base_key root portion of the key at which the left value is located
        @param data an optional data dict to use when resolving keys
        """
        super(_KeyValueStoreDiffDelegateBase, self).__init__()
        self._base_key = base_key
        self._log = log
        self._data = data
        self.delete_empty_trees = type(self).delete_empty_trees

    def should_resolve_values(self):
        """@return True if we should resolve string values from a data source"""
        return self._data is not None

    def _qualified_key(self, key):
        """Prepend our own key base to the default algorithm"""
        key_suffix = super(_KeyValueStoreDiffDelegateBase, self)._qualified_key(key)
        if key_suffix:
            return "%s%s%s" % (self._base_key, self.key_separator, key_suffix)
        else:
            return self._base_key
        #end handle suffix
       
    @staticmethod
    def _has_any_key(key_list):
        return any(isinstance(key, type) and issubclass(key, AnyKey) for key in key_list)
        
    def subtract_key_lists(self, l_keys, r_keys):
        """r-keys is allowed to have AnyKey instances, which are used to expand and match l_keys, in order.
        Remaining keys will be used as-is"""
        l_keys_with_any = self._has_any_key(l_keys)
        r_keys_with_any = self._has_any_key(r_keys)
        
        assert not (l_keys_with_any and r_keys_with_any), 'cannot handle AnyKey on both sides'
        def assert_keys(has_any, keys):
            if has_any and len(keys) > 1:
                raise AssertionError("cannot have more than one AnyKey per hierarchy level")
        # end assert utility
        assert_keys(l_keys_with_any, l_keys)
        assert_keys(r_keys_with_any, r_keys)
            
        # substractions are always without results, as we match anything
        if l_keys_with_any or r_keys_with_any:
            return tuple()
        # end handle fast-path
        
        # otherwise, do normal substraction
        return super(_KeyValueStoreDiffDelegateBase, self).subtract_key_lists(l_keys, r_keys)
        
    def possibly_modified_keys(self, left_keys, right_keys, keys_added_to_right):
        """if there are markers, return all left keys to implement "all_keys"""
        if self._has_any_key(right_keys):
            assert not self._has_any_key(left_keys), "cannot have AnyKey on both sides"
            return left_keys
        # end handle anykey
        return super(_KeyValueStoreDiffDelegateBase, self).possibly_modified_keys(left_keys, right_keys, 
                                                                                            keys_added_to_right)
        # end handle anykey
        
    def value_by_key(self, tree, key):
        """@return key by value, handle AnyKey
        @note the algorithm will only ask for values that it thinks we have. If we don't have it, it must 
        be AnyKeys doing, and we return the only value there is"""
        try:
            return super(_KeyValueStoreDiffDelegateBase, self).value_by_key(tree, key)
        except (KeyError, TypeError):
            # must be AnyKey !
            # Either we don't have the string-key in question, or it tries to use AnyKey as key during 
            # recursive removals
            assert len(tree) == 1, "should have only one key/value pair"
            assert list(tree.keys())[0] == AnyKey, "single key must be AnyKey"
            return list(tree.values())[0]
        # end handle anykey
        
# end class _KeyValueStoreDiffDelegateBase


## -- End Base Types -- @}



# ==============================================================================
## \name Delegates
# ------------------------------------------------------------------------------
## \{

class KeyValueStoreProviderDiffDelegate(_KeyValueStoreDiffDelegateBase):
    """Implements a delegate which builds a new value which mixes defaults and stored values.

    A diff algorithm is used to feed us with diff information. We use it to rebuild a possibly nested value
    composed of defaults and values from a stored value structure (as read from YAML for instance).

    The structure we create will only use values from the respective sources, never the trees/dicts that contained
    them. Mutable values will be copied into this structure to prevent any change to the value they originate
    from."""    
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## If True, values which are not know to the schema will be dropped, Otherwise they will be left
    ## in the returned dataset
    keep_values_not_in_schema = False

    ## The type used for formatting strings
    StringFormatterType = KVStringFormatter
    
    ## -- End Configuration -- @}

    # -------------------------
    ## @name TwoWayDiff Interface
    # @{

    def register_change(self, key, left_value, right_value, change_type):
        """Pick either a default value (right-hand side value) or the stored value (left-hand side)
        @note handles AnyKey"""
        if isinstance(key, type) and issubclass(key, AnyKey):
            # AnyKeys and their values are ignored if we get to the point where were are supposed to merge
            # them. This happens if it is indirectly removed or added, when whole branches are missing
            # in our data.
            # In that case, we just don't want to see it, the one who usees AnyKey needs to handle no keys
            # underneath AnyKeys parent tree anyway.
            
            # Change instance attribute, now AnyKey will map to an empty dict, which needs to be kept
            # to help clients to deal with it nicely
            self.delete_empty_trees = False
            return
        #end ignore everything underneath AnyKeys
        
        actual_value = NoValue
        qkey = self._qualified_key(self._to_string_key(key))
        
        # assure we have an instance for our assignments
        right_value_inst = right_value
        if isinstance(right_value, type) and right_value not in (TreeItem, NoValue):
            right_value_inst = right_value()
        # assure we have an instance for our assignments

        if change_type is self.added:
            actual_value = right_value_inst
        elif change_type is self.deleted:
            if self.keep_values_not_in_schema:
                # msg_prefix = 'Using'
                actual_value = left_value
            else:
                # msg_prefix = 'Dropped'
                actual_value = NoValue
            # end handle schema
        elif change_type is self.modified:
            try:
                if left_value is NoValue:
                    raise TypeError("NoValue is not a valid value")
                #end handle missing keys in storage
                # In case of a type conversion, we must assure the value is already 
                # 'final' and substituted. Otherwise the type conversion can fail prematurely.

                if right_value is None:
                    actual_value = left_value
                elif left_value is None:
                    actual_value = right_value_inst
                else:

                    if isinstance(right_value_inst, list) and not isinstance(left_value, list):
                        if self.should_resolve_values():
                            # have to assure we copy the nested value, otherwise the resolved value
                            # shows up in our source date-structure. We do this here, just to prevent
                            # unnecessary work in the resolver
                            right_value_inst = self._resolve_value(key, smart_deepcopy(right_value_inst))
                        actual_value = type(right_value_inst)()
                        actual_value.append(left_value)
                    elif isinstance(right_value, type):
                        # handle types
                        if self.should_resolve_values():
                            left_value = self._resolve_value(key, smart_deepcopy(left_value))
                        actual_value = right_value(left_value)
                    else:
                        # handle instances - only convert the type if this is necesary.
                        # Not all types are primitive, and invoking their constructor might just not work
                        if isinstance(left_value, type(right_value)):
                            actual_value = left_value
                        else:
                            if self.should_resolve_values():
                                left_value = self._resolve_value(key, left_value)
                            actual_value = type(right_value)(left_value)
                    # end handle list packing
                # handle value type - special handling for None
            except Exception as err:
                # Assure we have a real value for error printing and value handling
                actual_value = right_value_inst
                
                if self.should_resolve_values():
                    msg = "Could not convert value type %s of value '%s' at key '%s' "
                    msg += "to the desired type %s one of the default value with error: %s"
                    msg += ", using default value instead"
                    self._log.warn(msg, type(left_value), str(left_value), qkey, type(right_value_inst), str(err))
                # end handle logging
            #end handle type conversion
        else:
            # both values are equal - just use it
            assert change_type is self.unchanged
            actual_value = left_value
        #end handle change type

        # always perform a smart-copy here, value could be a nested list with mutable values
        if actual_value is not NoValue:
            self._set_merged_value(key, smart_deepcopy(actual_value))

    def _resolve_scalar_value(self, key, value):
        """@return a resolved single scalar string value"""
        # Actually, all of the values we see should be strings
        # however, the caller is and may be 'stupid', so we handle it here
        if not isinstance(value, str):
            return value
        # end ignore non-string types

        formatter = self.StringFormatterType()
        try:
            last_value = ''
            count = 0
            while last_value != value:
                count += 1
                last_value = value
                new_value = formatter.vformat(value, [], self._data)
                # we could have string-like types, and format degenerates them to just strings
                if type(new_value) is not type(value):
                    new_value = type(value)(new_value)
                value = new_value
                if count > MAX_ITERATIONS:
                    raise AssertionError("Value at '%s' could not be resolved after %i iterations - recursive values detected, last value was '%s', new value was '%s'" % (key, count, last_value, new_value))
                # end 
            # end recursive resolution
            return value
        except (KeyError, AttributeError, ValueError, TypeError) as err:
            msg = "Failed to resolve value '%s' at key '%s' with error: %s"
            self._log.warn(msg, value, key, str(err))
            # if we can't resolve, we have to resolve substitute to an empty value. Otherwise
            # the application might continue using a format string, which it can't check for
            # validity at all. Default values (like empty strings) can though
            return type(value)()
        # end handle exception

    def _resolve_value(self, key, value):
        """@return the resolved string value.
        It is able unpack/pack values to handle lists accordingly"""
        return transform_value(value, partial(self._resolve_scalar_value, key))
        
    def _set_merged_value(self, key, value):
        """try to resolve the value with our data"""
        if self.should_resolve_values():
            value = self._resolve_value(key, value)
        # handle substitution
        
        super(KeyValueStoreProviderDiffDelegate, self)._set_merged_value(key, value)

    ## -- End TwoWayDiff Interface -- @}
# end class KeyValueStoreProviderDiffDelegate


class RelaxedKeyValueStoreProviderDiffDelegate(KeyValueStoreProviderDiffDelegate):
    """Similar to KeyValueStoreProviderDiffDelegate, but less strict as it will return values not known 
    to your schema"""
    __slots__ = ()
    
    keep_values_not_in_schema = True

    

# end class KeyValueStoreProviderDiffDelegate


class KeyValueStoreModifierDiffDelegate(_KeyValueStoreDiffDelegateBase):
    """A delegate which is suitable for verifying the type of members of the base state with the ones that are
    to be set.
    """
    __slots__ = ()

    # -------------------------
    ## @name TwoWayDiff Interface
    # @{

    def _resolve_conflict(self, key, left_value, right_value):
        """ check type - just try conversion, don't be smart"""
        if left_value is NoValue:
            # no left ? Just use the right one
            return  right_value
        #end if no left value

        try:
            # As left can be None (if it is a singular None value), we treat it
            # specifically and don't try conversions
            if left_value is None:
                return right_value
            else:
                return type(left_value)(right_value)
        except Exception as err:
            # ignore this one - for now we just suck it up
            # NOTE: is it worth having an external handler for this to allow throwing exceptions ?
            msg = "Could not convert new value '%s' at key '%s' of type %s to the desired type %s, with error: %s"
            msg += "ignoring value"
            self._log.error(msg, right_value, self._qualified_key(self._to_string_key(key)),
                                type(right_value), type(left_value), str(err))
        #end handle value conversion

    ## -- End TwoWayDiff Interface -- @}
# end class KeyValueStoreModifierDiffDelegate


class KeyValueStoreModifierBaseSwapDelegate(ApplyDifferenceMergeDelegate):
    """A diff implementation which gathers differences between two states and applies the changes to a third.

    We perform all changes on the fly, and thus have no unnecessary memory overhead.

    @note the only reason we are deriving from a QualifiedKeyDiffDelegate is that its nice to have tracking
    for fully qualified keys, for debugging and the user. We don't technically require this feature though.

    @note we cannot really be reset, as the value will only be written once."""
    __slots__ = ()

    def __init__(self, initial_value):
        """Initialize ourselves with the base value to apply the changes to.
        We will copy the value to be sure - this needs to be done !"""
        super(KeyValueStoreModifierBaseSwapDelegate, self).__init__()
        self._merged_value = copy.deepcopy(initial_value)

# end class KeyValueStoreModifierBaseSwapDelegate


## -- End Delegates -- \}



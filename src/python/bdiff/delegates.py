#-*-coding:utf-8-*-
"""
@package bdiff.delegates
@brief a module with different generic delegate implementations

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from future.builtins import str
from future.builtins import object
__all__ = [ 'DiffRecord', 'DiffIndex', 'DiffIndexDelegate', 'QualifiedKeyDiffDelegate', 'MergeDelegate',
            'AdditiveMergeDelegate', 'ApplyDifferenceMergeDelegate', 'AutoResolveAdditiveMergeDelegate']

from .base import (TwoWayDiffDelegateInterface,
                   RootKey,
                   NoValue)
from butility import (OrderedDict,
                      smart_deepcopy)

# ==============================================================================
## \name Structures
# ------------------------------------------------------------------------------
# Simple datatypes which are merely keeping information, providing some access
# utilities for ease of use
## \{

class DiffRecord(object):
    """A simple Structure which associates a key with diff information indicating
    whether, when two sides A and B are compared, the respective item was
    
    - Added
    - Removed
    - Modified
    
    The key is able to identify the item uniquely, and it may contain separators
    which provide information about the hierarchical structure.
    
    This type is by itself usable as an item of a diff, which is identified
    by its key, and value compared by its change and destination(right) value.
    """
    __slots__ = ('_key', '_value_left', '_value_right', '_change_type')
    

    def __init__(self, key, value_left, value_right, change_type):
        """Initialize this instance completely"""
        self._key = key
        self._value_left = value_left
        self._value_right = value_right
        self._change_type = change_type
    
    # -------------------------
    ## @name Protocol Methods
    # @{
    
    def __hash__(self):
        return hash(self._key)
        
    def __eq__(self, rhs):
        return self._value_right == rhs.value_right()
    
    def __str__(self):
        return "%s : %s" % (self._key, self._change_type)
        
    def __repr__(self):
        return '%s(%s, %s, %s, "%s")' % (type(self).__name__, 
                                        self._key, self._value_left, 
                                        self._value_right, self._change_type)
    ## -- End Protocol Methods -- @}
    
    # -------------------------
    ## @name Access Interface
    # Read-Only accessor Methods
    # @{
    
    def key(self):
        """@return key identifying the stored values"""
        return self.key
        
    def value_left(self):
        """@return our left-hand side value, representing the previous state"""
        return self._value_left
        
    def value_right(self):
        """@return our right-hand side value, representing the current state"""
        return self._value_right
        
    def change_type(self):
        """@return a change type identifier"""
        return self._change_type    
    
    ## -- End Access Interface -- @}
    
# end class DiffRecord


class DiffIndex(OrderedDict):
    """An index of DiffRecord instances, which allows to query and organize the 
    DiffRecords more conveniently.
    
    This instance is an ordered mapping of key-value pairs, where each key is a
    hierarchical string, which separates each level using a separation character.
    
    The associated value is DiffRecord compatible item."""
    __slots__ = ()
    
    
    # -------------------------
    ## @name Predicate Generators
    # Genreators for redicates to be used by the `iterate()` method
    # @{
    
    @classmethod
    def by_change_type(cls, change_type):
        """@return a predicate which will return true if the given change_type matches"""
        def by_change_type_predicate(record):
            """Filter by stored change type"""
            return record.change_type() == change_type
        #end predicate definition
        return by_change_type_predicate
    
    ## -- End Predicate Generators -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def iterate(self, predicate):
        """@return iterator which yields all stored DiffRecord instances for which
        predicate returns True
        @param predicate `fun(record)` returning True for each record which matches"""
        for record in self.values():
            if predicate(record):
                yield record
            #end if predicate matches
        #end for each key and record
    
    ## -- End Interface -- @}
    

# end class DiffIndex

## -- End Structures -- \}


# ==============================================================================
## \name Base Types
# ------------------------------------------------------------------------------
## \{

class QualifiedKeyDiffDelegate(TwoWayDiffDelegateInterface):
    """A base class which provides utilities for dealing with keys that can be fully qualified.
    
    To achieve this, it keeps a stack of keys and from which it can generate a fully qualified 
    key, joining them with a certain separator.
    """
    __slots__ = (
                    '_key_stack'    # a stack of keys use to form fully qualified keys 
                )
    
    ## A separator between different key levels, i.e. key<separator>subkey
    key_separator = '/'
    
    def __init__(self):
        """Initialize this instance"""
        super(QualifiedKeyDiffDelegate, self).__init__()
        self.reset()
    
    def reset(self):
        """reset our internal state"""
        self._key_stack = list()
        return self
        
    def push_tree_level(self, key, left_tree, right_tree):
        if key is RootKey:
            if len(self._key_stack) > 0:
                raise AssertionError("RootKey should always be the first key we get")
            #end assert root key
        #end only verify non-None keys
        self._key_stack.append(self._to_string_key(key))
    
    def pop_tree_level(self):
        self._key_stack.pop()
        
    @classmethod
    def _to_string_key(cls, key):
        """Assure the key is not mal-formed, convert None to ''"""
        if key is RootKey:
            return str()
        #end convert None to ''
        assert isinstance(key, str) and cls.key_separator not in key
        return key
        
    def _qualified_key(self, key):
        """Append the given key to the key obtained by the key_stack, to make it
        fully qualified
        @param key a string key, make sure it is verified"""
        return self.key_separator.join(self._key_stack + [self._to_string_key(key)])[len(self.key_separator):]

## -- End Base Types -- @}


# ==============================================================================
## \name Delegates
# ------------------------------------------------------------------------------
# Types which contain the basic diff implementation
## \{

class DiffIndexDelegate(QualifiedKeyDiffDelegate):
    """A diff delegate which builds up a generic DiffIndex.
    
    It requires all keys to be strings which do not contain the separator
    """
    __slots__ = (
                    '_diff_index',  # the diff index we build 
                )

    # -------------------------
    ## @name Types and Constants
    # The types we use as DiffRecord and DiffIndex, can be overridden by subtype
    # @{
    
    DiffRecordType = DiffRecord
    DiffIndexType = DiffIndex
    
    ## -- End Types and Constants -- @}
    
    # -------------------------
    ## @name Interface Implementation
    # @{
    
    def result(self):
        """@return our diff index"""
        return self._diff_index
        
    def reset(self):
        """reset our internal state to support a clean plate"""
        self._diff_index = self.DiffIndexType()
        return super(DiffIndexDelegate, self).reset()
        
    def register_change(self, key, left_leaf, right_leaf, change_type):
        if change_type is self.unchanged:
            return
        #end ignore unchanged values
        qualified_key = self._qualified_key(key)
        self._diff_index[qualified_key] = self.DiffRecordType(qualified_key, left_leaf, right_leaf, change_type)
        
    ## -- End Interface Implementation -- @}

# end class DiffIndexDelegate


class MergeDelegate(QualifiedKeyDiffDelegate):
    """A delegate which builds a new structure from the difference information it obtains.
    
    The subclass will implement the `_resolve_conflict` method and determine which of the two values to use
    for the merged value.
    
    It is possible to only apply actual differences, or to take unchanged values into account which is useful
    if you want to build up similar structures, or alter them as you go.
    
    @note currently tested via its subclasses
    
    @note Technically we don't need the QualifiedKeyDiffDelegate as a base, however, for now its 
    easier and more useful to have it maintained automatically. If this should be problematic, it can be changed.
    """
    __slots__ = (   
                    '_merged_value',  # the final composed value
                    '_tree_stack',    # a stack of DictType instances, whose top-level 
                                      # dict is the merged value if it exists
                )


    ## The type of dict we will create when building the tree structure
    DictType = OrderedDict
    
    ## If True, empty trees/dictionaries will be deleted
    delete_empty_trees = True
    
    # -------------------------
    ## @name Interface
    # @{
    
    def result(self):
        """@return our merged value, or NoValue if the diff didn't yet run"""
        assert not self._tree_stack, "Tree stack should be empty (unless there is a bug)"
        return self._merged_value
        
    def reset(self):
        self._merged_value = NoValue
        self._tree_stack = list()
        
        return super(MergeDelegate, self).reset()
        
    ## -- End Interface -- @}
    
    # -------------------------
    ## @name TwoWayDiff Interface
    # @{
    
    def push_tree_level(self, key, left_tree, right_tree):
        """Update the value pointer accordingly, building a tree structure on the fly."""
        # keep merged value uptodate even during pushes
        if key is RootKey:
            assert len(self._tree_stack) == 0, "Should have empty tree stack"
            if self._merged_value is NoValue:
                self._merged_value = self.DictType()
            #end assure we reuse root-level values if we had one
            self._tree_stack.append(self._merged_value)
        else:
            assert self._tree_stack, "Should have at least one tree already"
            # connect parents - we can run through the hierarchy multiple times
            self._merged_value = self._tree_stack[-1].setdefault(key, self.DictType())
            # If or left tree is actually not a tree, but a scalar (which is when it is NoValue)
            # We want to be sure that the merged_value can hold the values which might be coming in
            # Therefore we enforce a dict
            if left_tree is NoValue and not isinstance(self._merged_value, self.DictType):
                self._merged_value = self.DictType()
                self._tree_stack[-1][key] = self._merged_value
            # end assure dicts override scalars
            self._tree_stack.append(self._merged_value)
        #end handle root key
        super(MergeDelegate, self).push_tree_level(key, left_tree, right_tree)

    def pop_tree_level(self):
        """Set the parent dict as new value"""
        
        popped_value = self._tree_stack.pop()

        # If this is not the top-level (and thus, last) value, we will prune empty trees
        if self.delete_empty_trees and not popped_value and self._tree_stack: 
            # disconnect value from parent - current level is parent level, as we popped the child value
            child_key = self._key_stack[-1]
            del(self._tree_stack[-1][child_key])
        #end prune empty values
            
        if self._tree_stack:
            # if the tree stack is empty, we still have to remember the merged value as it
            # is what is returned as a result...
            self._merged_value = self._tree_stack[-1]
        else:
            # in the previous run, we already grabbed the last remaining entry on the tree stack
            assert self._merged_value is popped_value
            pass
        # end handle merged value
            
        super(MergeDelegate, self).pop_tree_level()
        
    def register_change(self, key, left_value, right_value, change_type):
        """Assuming that left_value is the base state and the right value is the value to be set, we assure that
        
        - Modifications
          + Modified values will be passed on to the resolver, which will merge them or pick a side
        - Deletions
          + right values which are missing will be missing in the value we produce
        - Additions
          + right values which are where added will be added to the data structure unchecked
        - Unchanged
          + Unchanged values will be taken right away.
          
        We will copy right values to assure they are independent.
        """
        value_to_set = NoValue
        if change_type is self.added:
            value_to_set = self._handle_added(key, left_value, right_value)
        elif change_type is self.modified:
            value_to_set = self._resolve_conflict(key, left_value, right_value)
        elif change_type is self.unchanged:
            value_to_set = self._handle_unchanged(key, right_value)
        elif change_type is self.deleted:
            # If there was no change made to our current merge_value (tree) yet, we might have it still 
            # at the initial value, NoValue.
            # However, the _handle_deleted method requires parent_tree to be a tree-like objects, and asserts for it
            # We assure this now
            parent_tree = self._merged_value
            if parent_tree is NoValue:
                parent_tree = self.DictType()
            # handle possiblity of having NoValue as merged_value
            self._handle_deleted(key, parent_tree, left_value)
        #end handle change type

        if value_to_set is not NoValue:
            self._set_merged_value(key, smart_deepcopy(value_to_set))
        #end set value is possible
    ## -- End TwoWayDiff Interface -- @}
    
    # -------------------------
    ## @name Subclass Interface
    # Methods to be implemented by subclasses
    # @{
    
    def _resolve_conflict(self, key, left_value, right_value):
        """Called by `register_change()` when there are two modified values, and you have to decide for one.
        
        This method must pick either side or create a new value which corresponds to the combined value of both.
        It may also cause this value to be discarded by returning `NoValue` as value.
        @param key at which left and right values are found
        @param left_value value representing the previous state
        @param right_value value representing the current state
        @return the value to use, or `NoValue` to discard the value entirely
        @note the base implementation discards the value
        """
        return NoValue
        
    def _handle_unchanged(self, key, value):
        """Called whenever an unchanged value is encountered which you should return if it should be included
        in the resulting merged value. If you want to discard it, return NoValue
        @param key at which value is located in the parent tree
        @param value the unchanged value to handle
        @return value or NoValue
        @note default implementation just returns value
        """
        return value
        
    def _handle_deleted(self, key, parent_tree, previous_value):
        """Called to handle the given key which was deleted from the given parent tree
        
        The parent tree might still contain the key, and its this methods duty to determine how to deal with it.
        If you are applying the change to the destination of the merged (which is the parent tree), you would 
        delete the key from it.
        
        @note the base implementation deletes the key from parent_tree
        @param parent_tree the tree which might still contain the key. Its the destination of the merge, to which
        all changes are being applied
        @param key which points to the possibly existing value in parent tree
        @param previous_value is the value that was at the key location previously
        """
        # forget about this value, but be sure it is deleted in case the merged-value was initialized
        # We basically apply all the changes
        assert parent_tree is not NoValue
        try:
            del(parent_tree[key])
        except KeyError:
            pass
        #end ignore missing keys
        
    def _handle_added(self, key, left_value, right_value):
        """Called to indicate that the right_value was added
        
        This method will return the value that should in fact be used in the merged result.
        @param key key at which the value was added
        @param left_value either NoValue or TreeItem
        @param right_value the actually added value
        @return the value to use in the merged result
        @note the base implementation returns the added (i.e. right) value
        """
        return right_value
    
    def _set_merged_value(self, key, value):
        """To be invoked from the register_change method when you have figured out how you like to set the
        merged value for the given key.
        
        Our _merged_value can be assumed to be a tree or NoValue, or a non-tree value 
        @note This method is called by `register_change()`, which you might want to do too in case you 
        have reimplemented it.
        @param key a key qualified enough to be unique on the current tree level
        @param value the value you have determined
        """
        assert value is not NoValue, "value should not be a marker"

        # We might not have a parent tree (which is when we compare two non-trees)
        # The underlying algorithm may go up and down multiple times, therefore we might have
        # a tree value here already when another value comes in.
        # Deal with it
        if self.is_tree(self._merged_value) and key is not RootKey:
            # just overwrite possibly existing values, subclasses might have initialized our merge-base with
            # something non-empty. Otherwise, we could assert that the key is not yet in current_parent
            # Don't allow overwriting complex values with non-complex ones. If value would be a dict, 
            # we wouldn't be here either !
            if key not in self._merged_value or not isinstance(self._merged_value[key], self.DictType):
                self._merged_value[key] = value
            # end ignore overwriting trees with scalars
        else:
            self._merged_value = value
        #end handle merged value specialty
        
    ## -- End Subclass Interface -- @}


class AdditiveMergeDelegate(MergeDelegate):
    """Build up a value from scratch and, for each diff(...) call of the algorithm, merge add, modified and 
    unchanged items into the merge result.
    
    An example usage is the following, which creates a delegate of a derived type, and fills it with information
    consecutively.
    @note Will concatenate lists !
    @snippet bapp/core/kvstore/serialize.py additive example
    """
    __slots__ = ()
    
    def _resolve_conflict(self, key, left_value, right_value):
        """Choose the newer (right) value
        @note merges lists as well, prepending overriding items"""
        if isinstance(left_value, list) and isinstance(right_value, list):
            return right_value + left_value
        return right_value
        
    def _handle_deleted(self, key, parent_tree, previous_value):
        """Keep 'deletions', we are something like an additive merge"""
        # to do that, we have to put the key into the parent_tree
        # Drop the value if it is at the root key - this indicates that a scalar value now is a tree
        # We should only keep it though if there is no other, more complex value already.
        # This may happen as addition events are sent before deletion events.
        if key is not RootKey and key not in parent_tree:
            parent_tree[key] = previous_value
        # handle key type
        
# end class AdditiveMergeDelegate


class ApplyDifferenceMergeDelegate(MergeDelegate):
    """A merge delegate which applies only the difference between left and right to its merged result.
    
    Unchanged values will be discarded, and in case both values where modified (i.e. a conflict situation), 
    it will choose the newer, i.e. right, value."""
    __slots__ = ()
    
    def _resolve_conflict(self, key, left_value, right_value):
        """Always use our our value (right)"""
        return right_value
        
    def _handle_unchanged(self, key, value):
        """We only want to keep different values, so unchanged ones will just be dropped"""
        return NoValue
        
# end class ApplyDifferenceMergeDelegate


class AutoResolveAdditiveMergeDelegate(AdditiveMergeDelegate):
    """Build up a value from scratch and merge in multiple trees one after another.

    Conflicts will be resolved by using the newer value."""
    __slots__ = ()
    
    def _resolve_conflict(self, key, left_value, right_value):
        """Makes sure that None rhs values never overwrite existing ones"""
        if right_value is None:
            return left_value
        return super(AutoResolveAdditiveMergeDelegate, self)._resolve_conflict(key, left_value, right_value)

# end class AutoResolveAdditiveMergeDelegate

## -- End Delegates -- \}


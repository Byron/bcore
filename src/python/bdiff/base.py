#-*-coding:utf-8-*-
"""
@package bdiff.base
@brief Contains most fundamental types and interfaces

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals

from minifuture import with_metaclass
__all__ = ['NoValue', 'TreeItem', 'RootKey', 'TwoWayDiffDelegateInterface']

from butility import  (NonInstantiatable,
                       abstractmethod,
                       Meta,
                       DictObject)

# ==============================================================================
## \name Value Constants
# ------------------------------------------------------------------------------
# specific singleton constants with a similar meaning as 'None'
## \{

class NoValue(NonInstantiatable):
    """A type denoting no particular value, which allows values in a tree
    to be None (without indicating no-value)"""
    
# end class NoValue


class TreeItem(NoValue):
    """Indicates that the previous value at a key was a tree (which is not a value as well)"""
    __slots__ = ()

# end class TreeItem


class RootKey(NonInstantiatable):
    """Identifies the root key"""
    
# end class RootKey

## -- End Value Constants -- \}


# ==============================================================================
## \name Interfaces
# ------------------------------------------------------------------------------
## \{

class TwoWayDiffDelegateInterface(with_metaclass(Meta, object)):
    """Defines the interface of a delegate to be used by the TwoWayDiff.
    
    Its used to inform the client about events when diffing two trees, allowing
    it to build up its own data structures exactly as desired.
    
    It must treat all input arguments as being read-only, and may thus not change
    the structure of its inputs at all.
    
    Between each usage by the two-way diff, you should call the `reset()` method
    to start the next diff with a clean delegate without knowledge about previous diff runs.
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Change Types
    # Identifier for our differnt types of states a diff result can be in.
    # These types are constants with names suitable for user reviews
    # @{
    
    added = 'added'
    deleted = 'deleted'
    modified = 'modified'
    unchanged = 'unchanged'
    
    change_types = (added, deleted, modified, unchanged)
    
    ## -- End Change Types -- @}
    

    # -------------------------
    ## @name Interface
    # Interface for use by everyone
    # @{
    
    @abstractmethod
    def result(self):
        """@return the resulting data structure of the diff operation.
        Please refer to the documentation of the respective implementation for 
        information on the actual type
        """
        
    @abstractmethod
    def reset(self):
        """Reset the internal state and clean internal caches to assure the next
        diff run will be performed without interfering with the last.
        Users should call this method if they want to reuse the same delegate 
        for another diff
        @return this instance"""
    
    ## -- End Interface -- @}
    
    # -------------------------
    ## @name Base Implementation
    # Basic implementation useful for built-in types
    # @{
    
    def is_tree(self, item):
        """@return true if the given item is a tree-like object, i.e. it contains
        key-value pairs that we can iterate.
        The item's type may be an actual value, or the TreeItem or NoValue class."""
        return isinstance(item, (dict, DictObject))
        
    def keys(self, tree):
        """@return a list or tuple of keys of all children in the 
        given tree-like structure, which may be empty if there are none.
        @note override this methods if you want to support custom mappings."""
        assert self.is_tree(tree)
        return list(tree.keys())
        
    def value_by_key(self, tree, key):
        """@return the value corresponding to the given key in the tree"""
        return tree[key]
        
    def subtract_key_lists(self, left_keys, right_keys):
        """Subtract left keys from right keys, such as in 
        `left_keys - right_keys`.
        The keys are provided in a type returned by the `keys()` method which are unique on the current
        tree level **or** an empty tuple().
        
        To the implementation ordering doesn't matter.
        
        This default implementation will subtract them fast, but change the order
        as well.
        @return iterable of subtraction result
        """
        return set(left_keys) - set(right_keys)
        
    def possibly_modified_keys(self, left_keys, right_keys, keys_added_to_right):
        """A very specific callbacks to help allowing to fake the modified keys to check.
        @note this was easier than to override the algorithm, however, its dirties up the interface
        @todo remove this one and implement proper Globbed keys based on just the default methods.
        This can work, but is somewhat difficult."""
        return self.subtract_key_lists(right_keys, keys_added_to_right)
        
    def equal_values(self, left_value, right_value):
        """@return True if the left and right value are equal.
        The default implementation used compares for equality
        @note should be overridden by subclass if other behavior is desired
        """
        return left_value == right_value
    
    ## -- End Base Implementation -- @}
    
    # -------------------------
    ## @name TwoWayDiff Interface
    # Used by the TwoWayDiff instance only, and relevant for determining the diff
    # @{
        
    @abstractmethod
    def push_tree_level(self, key, left_tree, right_tree):
        """Informs the delegate that we enter a new level of recursion into one or
        two tree-like structures which are known under the given partial key.
        
        Either one of the trees may be as subclass of NoValue to indicate it is or was not a tree.
        
        @param key a key which is unique only on its level. It may be RootKey if 
        its the root trees.
        @param left_tree a tree like structure or subclass of NoValue if it was not a tree
        in the previous state.
        @param right_tree a tree like structure or subclass of NoValue if it is not a tree
        anymore in the current state.
        """
        
    @abstractmethod
    def pop_tree_level(self):
        """Informs the delegate that we left a level of recursion into the tree-like
        structure.
        """
        
    @abstractmethod
    def register_change(self, key, left_value, right_value, change_type):
        """register a change of the given change type that was found when comparing
        the left_value and the right_value.
        
        Depending on the change-type, one of the two items may be subclass of NoValue, which 
        is to be compared like: `if subclass(left_value, NoValue)` .
        
        @param key under which both sides, left and right, can be found. It may be
        RootKey if it involves the root tree, which must be handled as well.
        In case it is the RootKey, no tree level will have been pushed, because
        both items are not tree-like
        @param left_value actual item or subclass of NoValue
        @param right_value actual item or subclass of NoValue
        @param change_type one of our `change_types`. It relates to the left and 
        right value as follows:
        
        - modified
          + left and right leafs are set
        - added
          + left_value is NoValue
          + if left was a tree, value is TreeItem
        - deleted
          + right_value is NoValue
          + if right was a tree, value is TreeItem
        - unchanged
          + left_value equals right_value
        """
        
    ## -- End TwoWayDiff Interface -- @}
    
# end class TwoWayDiffDelegateInterface

## -- End Interfaces -- \}

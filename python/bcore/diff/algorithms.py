#-*-coding:utf-8-*-
"""
@package bcore.core.diff.algorithms
@brief A module with diffing algorithms

@copyright 2012 Sebastian Thiel
"""
__all__ = ['TwoWayDiff']

import bcore

from bcore.core.diff.base import (
                                    RootKey,
                                    NoValue,
                                    TreeItem
                              )

# too many arguments is okay as well, I have nearly no state and don't want to pack it into
# a struct just for that. However, I agree the _register_recursive_change() method call is difficult with 
# that many args !
# pylint: disable-msg=R0913

class TwoWayDiff(object):
    """A type implementing an two-way diff algorithm.
    
    It receives two tree-like structures and compares their leaf nodes with each
    other. Its findings will be forwarded to the `TwoWayDiffDelegateInterface` compatible delegate, who will 
    implement some sort of functionality.
    
    @note the algorithm works in an unordered fashion, such that additions and deletion events will be send
    in a particular order determined by the code, and not by the underlying data. This means that after a merge,
    your order of keys might be different"""
    __slots__ = ( )
    __metaclass__ = bcore.MetaBase
    
    # -------------------------
    ## @name Interface
    # @{
    
    def diff(self, delegate, left, right, _key=RootKey):
        """Compare the left and right nested tree with each other by recursively
        walking their children and comparing them one by one.
        
        A tree itself is not considered a value, it contains sub-trees or values. Empty trees
        are not treated as values either. Please note that *everything* is a value but a tree.
        
        A tree is a mapping of a name and an item, usually represented by a (nested)
        dict. A value can be anything that can be compared by the delgate's
        `equal_values` method.
        
        The diff algorithm can be seen as someone comparing the previous (left) and current (right) state
        of something with each other.
        
        @param delegate a delegate implementing the TwoWayDiffDelegateInterface
        @param left a tree-like or value instance, which can also be seen as the **previous** state
        of something.
        @param right a tree-like or value instance, which can also be regarded as **current** state
        of something.
        @param _key the actual key for the current left and right items.
        On first invocation, this is always RootKey to indicate there is no actual key.
        For subsequent invocations, the actual key will be used accordingly.
        The caller should not change this value.
        @return this instance"""
        l_is_tree = delegate.is_tree(left)
        r_is_tree = delegate.is_tree(right)
        l_keys = r_keys = tuple()

        if l_is_tree:
            l_keys = delegate.keys(left)
        #end have l tree
        if r_is_tree:
            r_keys = delegate.keys(right)
        #end have r tree
        if l_is_tree or r_is_tree: 
            # diff child key-value pairs to find added and deleted ones
            # If an added one was a tree, all children are added recursively
            # If a deleted one was a tree, all children are deleted recursively
            # added = current - previous
            keys_added_to_right = delegate.subtract_key_lists(r_keys, l_keys)
            self._register_recursive_change(delegate, _key, right,  keys_added_to_right, False, delegate.added)
            
            # deleted = previous - current
            keys_deleted_from_right = delegate.subtract_key_lists(l_keys, r_keys)
            self._register_recursive_change(delegate, _key, left, keys_deleted_from_right, True, delegate.deleted)

            if l_is_tree and r_is_tree:
                # possibly_modified = current - added need two trees for this
                keys_to_check_for_modifications = delegate.possibly_modified_keys(l_keys, r_keys, keys_added_to_right)
                delegate.push_tree_level(_key, left, right)
                for child_key in keys_to_check_for_modifications:
                    self.diff(delegate, delegate.value_by_key(left, child_key), 
                                delegate.value_by_key(right, child_key), _key=child_key)
                #end for each key to check
                delegate.pop_tree_level()
            # register changes created by type changes from tree to value and vice versa
            elif l_is_tree:
                # the following entries are not within the parent tree anymore
                # as they are the items that where in some way replaced by a tree.
                # current state changed from tree to item
                # == All previous children of left tree are deleted recursively 
                # and right tree item was added
                delegate.register_change(_key, TreeItem, right, delegate.added)
            #end only left is tree
            else:
                # it follows that only the right item is a tree 
                # current state changed from item to tree
                # == added all children recursively under right tree and
                # deleted left tree item
                delegate.register_change(_key, left, TreeItem, delegate.deleted)
            #end only right is tree
        else:
            # none of the items is a tree, compare by value
            change_type = delegate.equal_values(left, right) and delegate.unchanged or delegate.modified
            delegate.register_change(_key, left, right, change_type)
        #end handle item type
        return self
    
    ## -- End Interface -- @}
    
    # -------------------------
    ## @name Internal Utilities
    # Utility methods which can be overridden by subtypes to add support 
    # for custom types
    # @{
    
    @classmethod
    def _register_recursive_change(cls, delegate, key, tree, tree_keys, 
                                    right_is_none, change_type):
        """Recursively register the given change type for all items in the tree.
        @param delegate our delegate
        @param tree a tree-like object. If its not, then the tree_keys iterable will be empty
        @param key at which tree is located, may be RootKey
        @param tree_keys an iterable of keys which can be used to query
        respective values from the tree. May be empty, which is when we do nothing.
        @param right_is_none As we only have one tree, one of the two provided 
        trees to the `register_change` method must be NoValue.
        If this argument is True, the right tree will be NoValue, the left will
        be set. Otherwise the right one will be set, and the left is NoValue
        @param change_type one of the TwoWayDiffDelegateInterface.change_types
        @note We take care of pushing and popping the tree respectively"""
        if not tree_keys:
            return
        #end skip empty lists
        
        def left_right_in_order(tree):
            """@return (left, right) where the correct side is NoValue"""
            if right_is_none:
                return tree, NoValue
            else:
                return NoValue, tree
            #end swap values if required
        #end utility
        
        left, right = left_right_in_order(tree)
        
        delegate.push_tree_level(key, left, right)

        for child_key in tree_keys:
            value = delegate.value_by_key(tree, child_key)
            # depth first
            if delegate.is_tree(value):
                cls._register_recursive_change(delegate, child_key, value, delegate.keys(value), 
                                                        right_is_none, change_type)
            else:
                left, right = left_right_in_order(value)
                delegate.register_change(child_key, left, right, change_type)
            #end handle tree type
        #end for each key value pair
        delegate.pop_tree_level()
        
        
    ## -- End Internal Utilities -- @}
# end class TwoWayDiff

#-*-coding:utf-8-*-
"""
@package bdiff.tests.test_algorithms
@brief Implements tests for bdiff.algorithms

@copyright 2012 Sebastian Thiel
"""
__all__ = []

from unittest import TestCase

# test * import
from bdiff import *


class TestDiffAlgorithms(TestCase):
    __slots__ = ('delegate',    # a DiffIndex delegate for the diff 
                 'twoway')      # a twoway diff algorithm implementation instance
    
    ## [data structures]
    tree_a = {  '1' : 'one',
                '2' : 'two',
                '3' : { '1' : 'sub-one',
                        '2' : 'sub-two' },
                '4' : { '1' : {  '1' : 'sub-sub-one',
                                 '2' : 'sub-sub-two' },
                        '2' : dict()        # can handle empty trees
                                 
                      },
                '5' : { '1' : 'value' }
             }
             
    tree_b = {  '1' : 'one',
                '2' : 'two_changed',
                '3' : 'three',
                
                '5' : { '1' : 'value-modified' }
             }
             
    item_a = [1, 2, 3]
    item_b = (3, 4)
    
    ## [data structures]
    
    def setUp(self):
        """Provide a few default variables that we use all the time"""
        super(TestDiffAlgorithms, self).setUp()
        self.delegate = DiffIndexDelegate()
        self.twoway = TwoWayDiff()
    
    def test_twoway_simple(self):
        """basic tests using the twoway algorithm and the diff index"""
        ## [two way diff]
        dlg = DiffIndexDelegate()
        twoway = TwoWayDiff()
        
        twoway.diff(dlg, self.tree_a, self.tree_a)
        assert len(dlg.result()) == 0, "comparing equal items yields no difference"
        
        # if you want to run another diff on the same delegate.
        dlg.reset()
        twoway.diff(dlg, self.tree_a, self.tree_b)
        assert len(dlg.result()) > 0, "comparing non-equal items yields a difference"
        ## [two way diff]
        
    def test_diff_and_reversed_diff(self):
        """diff and reversed diff by exchanging parties"""
        # predicates
        added_items = DiffIndex.by_change_type(self.delegate.added)
        deleted_items = DiffIndex.by_change_type(self.delegate.deleted)
        modified_items = DiffIndex.by_change_type(self.delegate.modified)
        
        # check diff and reversed diff
        for needs_swap in range(2):
            tree_a, tree_b = self.tree_a, self.tree_b
            predicate = deleted_items
            if needs_swap:
                tree_b, tree_a = tree_a, tree_b
                predicate = added_items
            #end needs swap
            
            self.delegate.reset()
            self.twoway.diff(self.delegate, tree_a, tree_b)
            didx = self.delegate.result()                                    # diff index
            
            assert len(didx) > 0, "Should have found a difference"
            assert len(list(didx.iterate(predicate))) == 2 + 2, "Invalid number of added/removed items"
            assert len(list(didx.iterate(modified_items))) == 2, "Invalid number of modified items"
        #end for each diff reversal mode
        
    def test_check_two_items(self):
        """Compare two non-tree items with each other"""
        # check two items
        self.twoway.diff(self.delegate, self.item_a, self.item_b)
        didx = self.delegate.result()
        assert len(didx) == 1, "Expected the only item to be different"
        assert didx.values()[0].change_type() == self.delegate.modified
        
    def test_check_similar_items(self):
        """Assure similar trees or non-trees don't have differences"""
        # check similar items
        for equal_items_are_trees in range(2):
            item = equal_items_are_trees and self.tree_a or self.item_a
            self.twoway.diff(self.delegate, item, item)
            assert len(self.delegate.result()) == 0, "Same item should match itself"
            # delegate reset not required as its still empty
        #end for each equal item
        
    def test_check_all_combinations(self):
        """compare all combinations of items/values on both sides"""
        # check all combinations of root items which should be dissimilar
        for left_is_tree in range(2):
            left = left_is_tree and self.tree_a or self.item_a
            for right_is_tree in range(2):
                right = right_is_tree and self.tree_b or self.item_b
                
                self.delegate.reset()
                self.twoway.diff(self.delegate, left, right)
                assert len(self.delegate.result()) > 0, "Expected a difference to be detected"
            #end for each right item
        #end for each left item
    
    def test_check_hierarchy_states(self):
        """Verify that we figure out modifications even in nested hierarchies"""
        self.twoway.diff(self.delegate, self.tree_a, self.tree_b)
        didx = self.delegate.result()
        
        assert len(didx) == 7, "Expected specific amount of changes"
        assert didx['5/1'].change_type() == self.delegate.modified
        assert didx['4/1/2'].change_type() == self.delegate.deleted
        assert didx['3'].change_type() == self.delegate.added
        assert didx['3'].value_left() is TreeItem, "Expected a tree as previous value"
        assert issubclass(TreeItem, NoValue), "TreeItem should be a subclass of NoValue"
        
    def test_additive_merge(self):
        """Verify a simple additive merge works as expected"""
        delegate = AdditiveMergeDelegate()
        self.twoway.diff(delegate, self.tree_a, self.tree_b)
        
        # returns odict by default
        res = delegate.result()
        assert res['1'] == 'one'
        assert res['2'] == 'two_changed'
        assert res['3'] == 'three'
        assert res['5'] == { '1' : 'value-modified' }
        assert res['4'].to_dict() == {'1': {'1': 'sub-sub-one', '2': 'sub-sub-two'}}
        
        # verify list merge
        res['5'] = [1, 2, 3]
        delegate.reset()
        self.twoway.diff(delegate, res, {'5' : [4, 5]})
        assert delegate.result()['5'] == [4, 5, 1, 2, 3]
        
        # verify it deals with non-trees as well
        
        delegate.reset()
        self.twoway.diff(delegate, 1, 2)
        assert delegate.result() == 2
        
        delegate.reset()
        nval = { 1 : 'a' }
        self.twoway.diff(delegate, nval, 1)
        assert delegate.result() == 1
        
        delegate.reset()
        assert self.twoway.diff(delegate, 1, nval)
        assert delegate.result().to_dict() == nval
        
# end class TestDiff

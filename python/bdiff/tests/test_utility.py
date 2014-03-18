#-*-coding:utf-8-*-
"""
@package bdiff.tests.test_utility
@brief Implements tests for bdiff.utility

@copyright 2012 Sebastian Thiel
"""
__all__ = []

from unittest import TestCase

# test from * import
from bdiff.utility import *

class TestUtility(TestCase):

    def test_dict_object(self):
        """Verifies the dict object"""
        # simple struct-like object
        dobj = DictObject(dict(first=1, second=2))
        assert dobj.first == 1
        assert dobj.second == 2
        assert dobj['first'] is dobj.first
        assert dobj.get('first') is 1
        assert dobj.get('something', None) is None
        
        assert isinstance(str(dobj), str)
        assert repr(dobj) == str(dobj)
        
        assert len(dobj.keys()) == 2
        assert len(dobj.keys()) == len(dobj.values())
        assert 'first' in dobj
        
        self.failUnlessRaises(AttributeError, getattr, dobj, 'unknown')
        
        # references dict if possible
        dct = dict(one=1, two=2)
        dobj = DictObject(dct)
        assert dobj.__dict__ is dct
        assert dobj.__dict__ is dobj.to_dict()
        
        # no copy if not necessary
        assert dobj.__dict__ is dobj.to_dict(recursive=True)
        dobj.nested_dict = DictObject(dict(key="value"))
        assert dobj.nested_dict.key == "value"
        assert isinstance(dobj.to_dict()["nested_dict"], DictObject)
        assert isinstance(dobj.to_dict(recursive=True)["nested_dict"], dict)
        
        # copy dicts, resolve subdicts, keep them as references if possible
        sdct = dict(subone=11, subtwo=12)
        dct['sub'] = sdct
        dobj = DictObject(dct)
        
        assert dobj.__dict__ is not dct
        assert dobj.sub.__dict__ is sdct
        
        # set attr
        dobj.first = 2
        assert dobj.first == 2
        
        dobj_inv = dobj.inversed_dict()
        assert len(dobj_inv) == len(dobj) - 1, "Expected one item to be dropped due to duplicate value"
        assert 2 not in dobj
        assert 2 in dobj_inv
        
        # nesting
        dobj = DictObject(dict(hello=[1, 2, dict(something = 3)], world = (5, 6), there = dict(other=7)))
        assert dobj.hello[0] == 1
        assert isinstance(dobj.hello[2], DictObject)
        
        dobjclone = dobj.clone()
        dobjclone.newone = 42
        assert 'newone' not in dobj
        dobjclone.there.other = 42
        assert dobj.there.other == 7

# end class TestUtility

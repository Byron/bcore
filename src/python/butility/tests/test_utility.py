#-*-coding:utf-8-*-
"""
@package bdiff.tests.test_utility
@brief Implements tests for bdiff.utility

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division
from future.builtins import str
from future.builtins import range
__all__ = []

from .base import TestCase
import sys
import os

# test from * import
from butility import *


# ==============================================================================
## \name TestTypes
# ------------------------------------------------------------------------------
## \{

class TestNonInstantiatable(NonInstantiatable):
    __slots__ = ()

# end class TestNonInstantiatable

## -- End TestTypes -- \}


class TestUtility(TestCase):

    def test_platform_utilities(self):
        """verify simple utilities"""
        assert isinstance(login_name(), str)
        assert len(uname()) == 5
        assert isinstance(int_bits(), int)
        assert isinstance(dylib_extension(), str)
        assert '@' in system_user_id()
    
    def test_non_instantiatble(self):
        """check non-instantiation base class"""
        self.failUnlessRaises(TypeError, TestNonInstantiatable)
        
    def test_version(self):
        """test version implementation"""
        v1str = '2012.2.0-R1.SP2'
        v1 = Version(v1str)
        
        assert str(v1) == v1str
        assert repr(v1) == 'Version(%s)' % v1str
        
        assert len(v1.tokens(v1.TOKEN_NUMBER)) == 5
        assert len(v1.tokens(v1.TOKEN_STRING)) == 2
        
        assert v1[0] == 2012
        assert v1[1] == 2
        assert v1[2] == 0
        assert v1[3] == 'R'
        assert v1[4] == 1
        assert v1[5] == 'SP'
        assert v1[6] == 2
        
        # we are really loose on the comparison testing here, assuming that the RPM algorithm is just what
        # we implemented ... .
        vnewer = Version('2012.3.0')
        volder = Version('2012.2.0-R0')
        
        assert vnewer > v1
        assert v1 < vnewer
        assert v1 != vnewer
        assert not (v1 == vnewer)
        assert v1 == v1
        
        assert vnewer > volder
        assert volder < v1
        
        # default value
        assert Version() == Version() == Version.UNKNOWN
        assert not (Version.UNKNOWN > Version.UNKNOWN)
        assert not (Version.UNKNOWN < Version.UNKNOWN)
        assert Version.UNKNOWN >= Version.UNKNOWN
        assert Version.UNKNOWN <= Version.UNKNOWN
        assert not (Version.UNKNOWN != Version.UNKNOWN)
        
    def test_chunker(self):
        """Verify the chunker works as expected"""
        chunker = StringChunker()

        out = dict()
        for iteration in range(3):
            iteration += 1
            prev_size = len(out)
            string = 'abcdefghijklmnopqrstuvwxyz' * 123 * iteration
            cs = int(len(string) / 40)
            

            keys = chunker.split(string, cs, out)
            assert len(keys) + prev_size == len(out)

            assembled = ''.join(out[k] for k in keys)
            assert assembled == string
        # end for each iteration

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
        
        assert len(list(dobj.keys())) == 2
        assert len(list(dobj.keys())) == len(list(dobj.values()))
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
        
        del dobj.sub
        del dobj.nested_dict
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

        for dct, attr, desired_value in ((dobj.there, 'other', 7), (dobj, 'there', {})):
            self.failUnlessRaises(KeyError, dct.pop, 'notthere')
            assert dct.pop('notthere', None) is None
            assert dct.pop(attr) == desired_value
        # end for each sample

    def test_python_file_loader(self):
        mod_name = 'test_module'
        mod = PythonFileLoader.load_file(self.fixture_path('module.py'), mod_name)
        assert mod
        assert mod.Foo.hello() == 'world'

        res = PythonFileLoader.load_files(self.fixture_path(''), recurse=True)
        assert len(res) == 2
        assert res[0].endswith('module.py')
        assert res[1].endswith('submodule.py')

        del sys.modules[mod_name]
        del sys.modules['submodule']

    def test_octal(self):
        """test octal conversion"""
        assert octal('0777') == 511
        assert octal('777') == 511
        assert octal('0003') == 3

# end class TestUtility

#-*-coding:utf-8-*-
"""
@package bcore.tests.test_utility
@brief tests for bcore.utility

@copyright 2012 Sebastian Thiel
"""
__all__ = []

from bcore.tests import TestCaseBase

# W0614: Unused imports are okay, we are testing this
# R0201: test method could be a function - actually not
# pylint: disable-msg=W0614,R0201
from bcore import Version
from bcore.utility import *


# ==============================================================================
## \name TestTypes
# ------------------------------------------------------------------------------
## \{

class TestNonInstantiatable(NonInstantiatable):
    __slots__ = ()

# end class TestNonInstantiatable

## -- End TestTypes -- \}



class TestUtility(TestCaseBase):
    __slots__ = ()
    
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
        
    def test_chunker(self):
        """Verify the chunker works as expected"""
        chunker = StringChunker()

        out = dict()
        for iteration in range(3):
            iteration += 1
            prev_size = len(out)
            string = 'abcdefghijklmnopqrstuvwxyz' * 123 * iteration
            cs = len(string) / 40
            

            keys = chunker.split(string, cs, out)
            assert len(keys) + prev_size == len(out)

            assembled = ''.join(out[k] for k in keys)
            assert assembled == string
        # end for each iteration
        
# end class UtilityTests

#-*-coding:utf-8-*-
"""
@package bapp.tests.test_interfaces
@brief tests for base interfaces - they don't do anything theselves, but need subclassing

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from future.builtins import object
__all__ = []

import os

import bapp
from butility.tests import (TestInterface,
                            TempRWDirProvider)
from butility import Path
from .base import with_application
from bapp.interfaces import *


class TestIPlatformService(TestInterface):
    """Check for interface correctness"""
    __slots__ = ()

    @with_application
    def test_base(self):
        """Basic testing of all functions"""
        inst = self._instance
        
        for id_name in ('ID_SHORT', 'ID_FULL'):
            assert isinstance(inst.id(getattr(inst, id_name)), str)
        # end for each id to test
        self.failUnlessRaises(ValueError, inst.id, 'something')
        
        for variable_name in ('SEARCH_DYNLOAD', 'SEARCH_EXECUTABLES'):
            assert isinstance(inst.search_path_variable(getattr(inst, variable_name)), str)
        # end for each variable nam
        self.failUnlessRaises(ValueError, inst.search_path_variable, 'invalid')
        

# end class TestIPlatformService


class TestDirectoryServicesMixin(object):
    """Tests for the default project-instances interface
    NOTE: We cannot be called alone, yet we want to be named after a valid test.
    All this is necessary as we want to use the same test implementation multiple times in the same module, 
    which doesn't natively work with the TestInterface subclasses"""
    
    __slots__ = ()

    @with_application
    def test_directory_instances(self):
        if not hasattr(self, '_instance'):
            return
        inst = self._instance
        count = 0
        for pid in inst.path_types():
            count += 1
            assert isinstance(inst.path(pid), Path)
        # end for each pid
        assert count
        self.failUnlessRaises(ValueError, inst.path, 'foobar')
        assert inst.id() is not None
    
# end class TestIDirectoryServices


class TestIProjectService(TestDirectoryServicesMixin, TestInterface):
    __slots__ = ()


# end class TestIProjectService

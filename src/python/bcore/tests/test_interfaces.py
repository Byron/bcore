#-*-coding:utf-8-*-
"""
@package bcore.tests.test_interfaces
@brief tests for base interfaces - they don't do anything theselves, but need subclassing

@copyright 2013 Sebastian Thiel
"""
__all__ = []

import os

import bcore
from butility.tests import (TestInterfaceBase,
                            TempRWDirProvider)
from butility import Path
from .base import with_application
from bcore.interfaces import *


class TestIPlatformService(TestInterfaceBase):
    """Check for interface correctness"""
    __slots__ = ()

    @with_application
    def test_base(self):
        """Basic testing of all functions"""
        inst = self._instance
        
        for id_name in ('ID_SHORT', 'ID_FULL'):
            assert isinstance(inst.id(getattr(inst, id_name)), basestring)
        # end for each id to test
        self.failUnlessRaises(ValueError, inst.id, 'something')
        
        for variable_name in ('SEARCH_DYNLOAD', 'SEARCH_EXECUTABLES'):
            assert isinstance(inst.search_path_variable(getattr(inst, variable_name)), basestring)
        # end for each variable nam
        self.failUnlessRaises(ValueError, inst.search_path_variable, 'invalid')
        

# end class TestIPlatformService


class TestIContextController(TestInterfaceBase):
    """Attempts to trigger callbacks, even though this interface cannot verify it actually works"""
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    ## To be set by subclass
    # @{
    
    ## A file to load, which is assumed to be in contet A. It should be picked up by the implementation.
    file_in_context_a = None
    
    ## A file to load, being in a different context. The implementation should realize this and handle it 
    ## accordingly
    file_in_context_b = None
    
    ## -- End Configuration -- @}
    
    @with_application
    def test_base(self):
        assert self.file_in_context_a.isfile() and self.file_in_context_b.isfile(), 'test files must be set'
        host = new_service(bcore.IHostApplication)
        
        assert host.loaded_file() != self.file_in_context_a
        host.load(self.file_in_context_a)
        assert host.loaded_file() == self.file_in_context_a
        
        # (re)loading the same file is okay
        host.load(self.file_in_context_a)
        
        # changing to a changed context should fail or indicate some sort of error
        host.load(self.file_in_context_b)
        # both files are valid, dependending on whether the implementation can prevent the file from being opened
        assert host.loaded_file() == self.file_in_context_b or host.loaded_file() == self.file_in_context_a 
        
# end class TestIContextController


class TestDirectoryServicesMixin(object):
    """Tests for the default project-instances interface
    NOTE: We cannot be called alone, yet we want to be named after a valid test.
    All this is necessary as we want to use the same test implementation multiple times in the same module, 
    which doesn't natively work with the TestInterfaceBase subclasses"""
    
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


class TestIProjectService(TestDirectoryServicesMixin, TestInterfaceBase):
    __slots__ = ()


# end class TestIProjectService


class TestISiteService(TestDirectoryServicesMixin, TestInterfaceBase):
    __slots__ = ()


# end class TestISiteService

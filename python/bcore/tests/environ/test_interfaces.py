#-*-coding:utf-8-*-
"""
@package bcore.tests.interfaces.test_base
@brief tests for base core interfaces

@copyright 2013 Sebastian Thiel
"""
__all__ = []

import os

import bcore
from bcore.tests import (
                        TestInterfaceBase,
                        TempRWDirProvider
                    )
from bcore import Version
from butility import Path



class TestIHostApplication(TestInterfaceBase):
    """Check for interface correctness, as much as possible
    @todo try to implement a quit-test with the wrapper framework. Should be possible ... """
    __slots__ = ()
    
    # -------------------------
    ## @name Subclass Implementation
    # @{
    def file_path(self):
        """@return a filepath to a file we should be able to load and save
        @note can't make it abstract, as nose will instantiate us for our tests"""
        
    ## -- End Subclass Implementation -- @}
    
    def test_version(self):
        assert isinstance(self._instance.version(), Version)
        
    def test_save_and_load(self):
        """load a file, and save it in a temp directory"""
        filepath = self.file_path()
        assert filepath is not None, "file_path method needs implementation in subclass"
        assert self._instance.load(filepath).loaded_file() == filepath
        
        tmp = TempRWDirProvider()
        new_filepath = tmp.dir() / os.path.basename(filepath)
        assert self._instance.save(new_filepath).loaded_file() == new_filepath
        
    # for now this is all we can sensibly test ... quit could be possible with a wrapper

# end class TestIHostApplication


class TestIPlatformService(TestInterfaceBase):
    """Check for interface correctness"""
    __slots__ = ()

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
    """Tests for the default project-services interface
    NOTE: We cannot be called alone, yet we want to be named after a valid test.
    All this is necessary as we want to use the same test implementation multiple times in the same module, 
    which doesn't natively work with the TestInterfaceBase subclasses"""
    
    __slots__ = ()

    def test_directory_services(self):
        if not hasattr(self, '_instance'):
            return
        inst = self._instance
        count = 0
        for pid in inst.path_ids():
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

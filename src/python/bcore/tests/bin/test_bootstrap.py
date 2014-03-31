#-*-coding:utf-8-*-
"""
@package bcore.tests.bin.test_wrapper
@brief tests for bcore.bin.wrapper

@copyright 2012 Sebastian Thiel
"""
__all__ = []


import sys
import os.path

import bcore
from bcore.tests import TestCaseBase
from bprocess.tests.test_base import TestProcessController

# Dynamic loading of wrapper code - its not in a package for good reason
dirname = os.path.dirname
loaded_files = PythonFileLoader(os.path.join(dirname(dirname(dirname(__file__))), 'bin'), recurse=False).load()
assert len(loaded_files) == 1
wrapper_file = loaded_files[0]
import bootstrap

class TestBootstrapper(bootstrap.Bootstrapper):
    """Overrides particular functions to 'mock' the implementation"""
    ## dry-run
    
    
class TestBootstrap(TestCaseBase):
    """Tests for the bootstrap implementation"""
    __slots__ = ()
    
    def test_base(self):
        """test fundamentals
        @note doesn't run all code paths, but its just a few lines"""
        # Have to register the controller explicitly to make it available
        bcore.environment.register(TestProcessController)
        
        # Should be dealing with its executable being python as well as its file
        self.failUnlessRaises(AssertionError, TestBootstrapper().main, wrapper_file)
        self.failUnlessRaises(AssertionError, TestBootstrapper().main, '/some/nonesense')
        
        # this will actually do something (but not start a program)
        try:
            TestBootstrapper().main(self.fixture_path('bin/maya'), '-file')
        except SystemExit:
            pass
        # end handle exception

    

# end class TestWrapper

#-*-coding:utf-8-*-
"""
@package bcore.tests.environ.test_base
@brief tests for bcore.environ.base, depends on bcontext working correctly

@copyright 2012 Sebastian Thiel
"""
__all__ = []

import bcore
from bcore.tests import TestCaseBase

# try * import
from bcore.environ import *


class TestEnvironment(TestCaseBase):
    __slots__ = ()

    def test_base(self):
        pbe = ApplicationContext('test_pb')
        ose = OSContext('test_os')
        
        # Test Validation
        validator = bcore.app().context().schema_validator()
        assert len(validator) > 0
        assert len(validator.validate_schema()[1]) == 0, "default schema's should have no clashes"
    

# end class TestEnvironment

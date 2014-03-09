#-*-coding:utf-8-*-
"""
@package tx.tests.core.environ.test_base
@brief tests for tx.core.environ.base, depends on tx.core.component working correctly

@copyright 2012 Sebastian Thiel
"""
__all__ = []

import bcore
from bcore.tests import TestCaseBase

# try * import
from bcore.core.environ import *


class TestEnvironment(TestCaseBase):
    __slots__ = ()

    def test_base(self):
        pbe = PipelineBaseEnvironment('test_pb')
        ose = OSEnvironment('test_os')
        
        # Test Validation
        validator = tx.environment.schema_validator()
        assert len(validator) > 0
        assert len(validator.validate_schema()[1]) == 0, "default schema's should have no clashes"
    

# end class TestEnvironment

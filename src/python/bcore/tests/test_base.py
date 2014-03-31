#-*-coding:utf-8-*-
"""
@package bcore.tests.test_base
@brief tests for bcore.base

@copyright 2012 Sebastian Thiel
"""
__all__ = []

from bcore.tests import TestCaseBase
from bcore.base import * 

# ==============================================================================
## \name Test Types
# ------------------------------------------------------------------------------
# Types that derive from the type that should actually be tested
## \{

class TestInterface(InterfaceBase):
    __slots__ = ()
    
# end class TestInterface
## -- End Test Types -- \}


class TestCore(TestCaseBase):
    __slots__ = ()
    
    def test_interface(self):
        """verify supports methods"""
        tif = TestInterface()
        self.failUnless(tif.supports(TestInterface))
        
    def test_component_framework(self):
        """Component Architecture framework should be available without explicit imports"""
        Plugin
        service
        instances
        new_service
        new_instances

    def test_application(self):
        """Test BApplication functionality"""
        self.fail("todo")

        assert bcore.Application.main is bcore.app()
        bcore.app().instance(ISomeService)
        bcore.app().type(ISomeService)
        bcore.app().settings().value_by_schema(schema)
        assert bcore.app().raw_settings() is bcore.app().context().settings().data()

        class MyPluginType(bcore.app().Plugin):
        """A type for the registry"""
            __slots__ = ()
        
        # end class MyPluginType

   
# end class TestCore

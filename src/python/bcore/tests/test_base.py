#-*-coding:utf-8-*-
"""
@package bcore.tests.test_base
@brief tests for bcore.base

@copyright 2012 Sebastian Thiel
"""
__all__ = []

from butility.tests import TestCaseBase
from butility import (InterfaceBase,
                      abstractmethod)

import bcore

from bcore import (InstanceNotFound,
                   TypeNotFound)

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
    
    def test_application(self):
        """Test BApplication functionality"""

        self.failUnlessRaises(EnvironmentError, bcore.app)

        class ICustomInterface(InterfaceBase):
            __slots__ = ()
            
            @abstractmethod
            def hello(self):
                return str()

        # end class ICustomInterface

        # It is possible to setup plugins even without an Application
        class CustomPluginType(ICustomInterface, bcore.plugin_type()):
            """Works without application"""
            __slots__ = ()
        
            def hello(self):
                return "world"
                
        # end class CustomPluginType

        # we don't have access to the stack without an application, so lets make one
        app = bcore.Application.new()
        assert bcore.Application.main is bcore.app() is app
        self.failUnlessRaises(InstanceNotFound, bcore.app().instance, file)
        self.failUnlessRaises(TypeNotFound, bcore.app().type, file)

        # As there is no instance, this one won't find one either
        self.failUnlessRaises(InstanceNotFound, bcore.app().instance, ICustomInterface)

        # the custom type can already be found
        assert bcore.app().type(ICustomInterface) is CustomPluginType

        # instance is cought by the associated context automatically. Early types will always go to the 
        # current main application
        inst = CustomPluginType()
        assert bcore.app().instance(ICustomInterface) is inst

        # bcore.app().settings().value_by_schema(schema)
        # assert bcore.app().raw_settings() is bcore.app().context().settings().data()

        # class MyPluginType(bcore.app().Plugin):
        #     """A type for the registry"""
        #     __slots__ = ()
        
        # # end class MyPluginType

   
# end class TestCore

#-*-coding:utf-8-*-
"""
@package bapp.tests.test_base
@brief tests for bapp.base

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

from .base import (preserve_application,
                   with_application,
                   AppTestCase)
                            
from butility import (Interface,
                      abstractmethod)

import bapp

from bapp import (InstanceNotFound,
                   TypeNotFound)

from bapp.contexts import (ApplicationContext,
                           OSContext)


class TestCore(AppTestCase):
    __slots__ = ()
    
    @with_application
    def test_application(self):
        """Test BApplication functionality"""

        app = bapp.main()

        class ICustomInterface(Interface):
            __slots__ = ()
            
            @abstractmethod
            def hello(self):
                return str()

        # end class ICustomInterface

        # It is possible to setup plugins even without an Application
        class CustomPluginType(ICustomInterface, bapp.plugin_type()):
            """Works without application"""
            __slots__ = ()
        
            def hello(self):
                return "world"
                
        # end class CustomPluginType

        # we don't have access to the stack without an application, so lets make one
        assert bapp.Application.main is bapp.main() is app
        self.failUnlessRaises(InstanceNotFound, bapp.main().instance, file)
        self.failUnlessRaises(InstanceNotFound, bapp.main().new_instance, file)
        self.failUnlessRaises(TypeNotFound, bapp.main().type, file)

        # As there is no instance, this one won't find one either
        self.failUnlessRaises(InstanceNotFound, bapp.main().instance, ICustomInterface)

        # the custom type can already be found
        assert bapp.main().type(ICustomInterface) is CustomPluginType

        # instance is cought by the associated context automatically. Early types will always go to the 
        # current main application
        inst = CustomPluginType()
        assert bapp.main().instance(ICustomInterface) is inst

        # create a new instance
        new_inst = bapp.main().new_instance(ICustomInterface)
        assert new_inst is not inst
        assert bapp.main().instance(ICustomInterface) is inst, "new_inst should not be owned by context"

    @preserve_application
    def test_hierarchical_loading(self):
        """See the hierarchical yaml loader in action"""
        assert bapp.Application.main is None
        app = bapp.Application.new(setup_logging=False, 
                                    settings_trees=(self.fixture_path(''),),
                                    settings_hierarchy=True)

        assert len(app.settings().data())

       
# end class TestCore


class TestContext(AppTestCase):
    __slots__ = ()

    @with_application
    def test_base(self):
        pbe = ApplicationContext('test_pb')
        ose = OSContext('test_os')

        app = bapp.main()
        app.context().push(pbe)
        app.context().push(ose)
        
        # Test Validation
        validator = app.context().schema_validator()
        assert len(validator) > 0
        assert len(validator.validate_schema()[1]) == 0, "default schema's should have no clashes"
    

#-*-coding:utf-8-*-
"""
@package tx.tests.core.environ.test_components
@brief tests for tx.core.environ.components

@copyright 2013 Sebastian Thiel
"""
__all__ = []

from .test_interfaces import (
                                    TestIHostApplication,
                                    TestIPlatformService,
                                    TestISiteService,
                                    TestIProjectService
                                )
# * import test
from bcore.core.environ.components import *
from bcore.core.environ import (
                                IPlatformService,
                                IProjectService,
                                ISiteService
                            )



class TestHostApplication(TestIHostApplication):
    """This type benefits from test in the Interface base tests"""
    subclass_type = PythonHostApplication
    
    def file_path(self):
        raise NotImplementedError

# end class TestComponents


class TestPlatformServices(TestIPlatformService):
    """Reuse default testcases with our type"""
    __slots__ = ()
    
    # use the currently active type
    subclass_type = type(service(IPlatformService))
    
# end class TestPlatformServices


class TestProjectServices(TestISiteService):
    """Tests for the default project-services implemntation """
    __slots__ = ()
    
    subclass_type = type(service(IProjectService))

# end class TestProjectServices


class TestSiteServices(TestIProjectService):
    """Tests for the default site-services implemntation """
    __slots__ = ()
    
    subclass_type = type(service(ISiteService))

# end class TestSiteServices



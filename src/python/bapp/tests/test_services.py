#-*-coding:utf-8-*-
"""
@package bapp.tests.environ.test_components
@brief tests for bapp.environ.components

@copyright 2013 Sebastian Thiel
"""
__all__ = []

from .test_interfaces import (TestIPlatformService,
                              TestISiteService,
                              TestIProjectService)
from bapp.services import (LinuxPlatformService,
                            ProjectInformation,
                            SiteInformation)



class TestPlatformServices(TestIPlatformService):
    """Reuse default testcases with our type"""
    __slots__ = ()
    
    # Assume it's working similarly with other platforms too
    subclass_type = LinuxPlatformService
    
# end class TestPlatformServices


class TestProjectServices(TestISiteService):
    """Tests for the default project-instances implemntation """
    __slots__ = ()
    
    subclass_type = ProjectInformation

# end class TestProjectServices


class TestSiteServices(TestIProjectService):
    """Tests for the default site-instances implemntation """
    __slots__ = ()
    
    subclass_type = SiteInformation

# end class TestSiteServices



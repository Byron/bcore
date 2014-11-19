#-*-coding:utf-8-*-
"""
@package bapp.tests.test_services
@brief tests for bapp.services

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = []

from butility.tests import TestInterface
from .test_interfaces import (TestIPlatformService,
                              TestDirectoryServicesMixin)
from bapp.services import (LinuxPlatformService,
                           ProjectInformation)


class TestPlatformServices(TestIPlatformService):

    """Reuse default testcases with our type"""
    __slots__ = ()

    # Assume it's working similarly with other platforms too
    subclass_type = LinuxPlatformService

# end class TestPlatformServices


class TestProjectServices(TestDirectoryServicesMixin, TestInterface):

    """Tests for the default project-instances implemntation """
    __slots__ = ()

    subclass_type = ProjectInformation

# end class TestProjectServices



import bapp
from bprocess.tests.test_base import ITestMarkerInterface


class TestMarkerInterface(ITestMarkerInterface, bapp.plugin_type()):

    """Just to allow an instance of the interface to be created"""
    __slots__ = ()


# end class TestMarkerInterface

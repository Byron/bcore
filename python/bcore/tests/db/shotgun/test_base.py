#-*-coding:utf-8-*-
"""
@package bcore.tests.db.shotgun.test_base
@brief tests for bcore.db.shotgun.base

@copyright 2013 Sebastian Thiel
"""
__all__ = []


from nose import SkipTest

try:
    import shotgun_api3
except ImportError:
    raise SkipTest("If we are launched without the wrapper, shotgun tests can't work as dependencies are not met")
# end handle dependencies

from bcore.tests import TestCaseBase

# test import *
from bcore.db.shotgun import *
from bcore import IShotgunConnection
from bcore.core.component import ServiceNotFound
from shotgun_api3 import Fault


class TestShotgun(TestCaseBase):
    __slots__ = ()
    
    def test_base(self):
        """verify shotgun connection with a mock - for now there is no real datbase access to not slow down anything"""
        ProxyShotgunConnection()
        
        # lets get our own - the type is not loaded by default
        self.failUnlessRaises(ServiceNotFound, new_service, IShotgunConnection)
        import bcore.db.shotgun.components.rwconnection
        
        svc = new_service(IShotgunConnection)
        # All of the following code will connect to shotgun - lets not do that and assume the code stays fit for
        # duty
        return 
        self.failUnlessRaises(Fault, svc.find_one, 'Foo', [('id', 'is', 1)])
        
    


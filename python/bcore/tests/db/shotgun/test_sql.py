#-*-coding:utf-8-*-
"""
@package bcore.tests.db.shotgun.test_sql
@brief tests for bcore.db.shotgun.sql

@copyright 2013 Sebastian Thiel
"""
__all__ = []

from time import time
from nose import SkipTest

try:
    import shotgun_api3
except ImportError:
    raise SkipTest("If we are launched without the wrapper, shotgun tests can't work as dependencies are not met")
# end handle dependencies

from bcore.tests import TestCaseBase
from bcore.tests.db.shotgun import ReadOnlyTestSQLProxyShotgunConnection

# test import *
from bcore.db.shotgun import *
from bcore.db.shotgun.orm import ShotgunTypeFactory
from bcore import IShotgunConnection
from bcore.core.component import ServiceNotFound


class TestShotgunSQL(TestCaseBase):
    __slots__ = ()
    
    def test_init_sqldb(self):
        """Initialize a new shotgun database"""
        ###############
        return
        ###############
        # NOTE: only for testing this operation - it will be done automatically by decorators, and on demand,
        # using the local disk as cache.
        ReadOnlyTestSQLProxyShotgunConnection.rebuild_database()
        
    def test_sql(self):
        """Check some SQL functionality with our SQL test database"""
        sg = ReadOnlyTestSQLProxyShotgunConnection()
        
        # Write is disabled
        self.failUnlessRaises(AssertionError, sg.batch)
        
        # read disabled unless overridden
        self.failUnlessRaises(AssertionError, sg.schema_read)
        
        fac = ShotgunTypeFactory()
        
        # Simple query
        sg_id = 612
        Asset = fac.type_by_name('Asset')
        data = sg.find_one(Asset.__name__, [('id', 'is', sg_id)], Asset.sg_schema.keys())
        assert isinstance(data, dict), "didn't get a value of correct type"
        
        entity = Asset(sg_id, data)
        assert entity.code.value() == 'Mortar_A'
        
        assert sg.find_one(Asset.__name__, [('id', 'is', 10)], ['id']) is None, 'invalid ids just yield None'
        
        
        total_record_count = 0
        fetch_count = 0
        tst = time()
        for type_name in fac.type_names():
            for filter in ([], [('id', 'is', sg_id)]):
                for limit in (0, 10):
                    Entity = fac.type_by_name(type_name)
                    # we can get empty data
                    st = time()
                    data = sg.find(Entity.__name__, filter, Entity.sg_schema.keys(), limit=limit)
                    total_record_count += len(data)
                    fetch_count += 1
                    if data:
                        print "Fetched %i records in %fs" % (len(data), time() - st)
                    # end performance printing
                    
                    if limit:
                        assert len(data) <= limit
                    if limit or filter:
                        continue
                    
                    # just retrieve the value , to see it really works.
                    ######################
                    # remove for stress testing - this works, and is suffciently tested in orm/test_base.py
                    continue
                    
                    for edata in data:
                        node = Entity(edata['id'], edata)
                        for prop_name in Entity.sg_schema.keys():
                            getattr(node, prop_name).value()
                        # end for each property name
                    # end for each entity data block
                # end for each limit
            # end for each filter
        # end for each type
        print "Received a total of %i records in %i fetches in %fs" % (total_record_count, fetch_count, time() - tst)
        
        
    

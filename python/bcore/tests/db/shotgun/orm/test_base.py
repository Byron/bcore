#-*-coding:utf-8-*-
"""
@package bcore.tests.db.shotgun.orm.test_base
@brief tests for bcore.db.shotgun.orm

@copyright 2013 Sebastian Thiel
"""
__all__ = []


import json
import sys
import time
from datetime import (
                        datetime,
                        date
                     )
from nose import SkipTest

try:
    import shotgun_api3
except ImportError:
    raise SkipTest("If we are launched without the wrapper, shotgun tests can't work as dependencies are not met")
# end handle dependencies

from bcore.tests import TestCaseBase
from bcore.tests.db.shotgun import ShotgunTestDatabase
import bcore

# test import *
from bcore.db.shotgun.orm import types as sgtypes
from bcore.db.shotgun.orm import *
from bcore.db.shotgun import ProxyShotgunConnection
from bcore.utility import DictObject


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

def assert_set_value(entity, prop, value, descriptor):
    """Sets values according to their type, changing them and verifying them"""
    prop_name = descriptor.partial_name()
    ValueType = descriptor._value_type
    
    # setting the same value again is no change
    prop.set_value(value)
    assert prop_name not in entity.changed_properties() 
    
    if issubclass(ValueType, sgtypes._ShotgunDateMixin):
        args = (1, 1, 1, 1, 1, 1)
        if isinstance(value, date):
            args = args[:2]
        value = type(value)(value.year + 1, *args)
    elif isinstance(value, basestring):
        value += 'foo'
    elif isinstance(value, DictObject):
        # The value can be empty, and has no fields
        if value:
            value.url += "foo"
        else:
            value.url = "foo"
        # end handle value
    elif isinstance(ValueType, sgtypes.ShotgunCheckbox):
        value = not value
    elif isinstance(value, (int, float)):
        # can also be percent
        new_value = type(value)(50)
        if new_value == value:
            new_value += 1
        value = new_value
    elif isinstance(value, list):
        # works for normal list, as well as status list, which is a string list
        value.append('wtg')
    elif isinstance(value, dict):
        # This is for the serializable type !
        value['foo'] = 'bar'
    else:
        assert False, "unhandled value type: %s" % type(value)
    # end special type handling
    
    assert prop.set_value(value).value() == value
    assert prop_name in entity.changed_properties()
    
    # Can set every value to null - dates are somewhat special
    if not issubclass(descriptor._value_type, sgtypes._ShotgunDateMixin):
        assert not prop.set_value(None).value()
    # end handle datetime special case ... .
    
# end test value helper

def assert_set_entity(entity, prop, value, descriptor, factory):
    """Verify entities can be set properly, for single and multi-entities"""
    # don't try to create an invalid type, and bail out
    type_name = descriptor._valid_types[0]
    
    prop_name = descriptor.partial_name() # partial name is faster than name, and makes no difference
    
    # setting the same value is not a change
    prop.set_value(value)
    assert prop_name not in entity.changed_properties()
    # Set the entity to something else
    
    new_enode = factory.type_by_name(type_name)(0)
    
    prop.set_value(new_enode)
    assert prop.value() == new_enode
    
    assert prop_name in entity.changed_properties()
    
    assert not prop.set_value(None).value(), "Setting null values sets it None/nil/null"
    
# end assert set entity

## -- End Utilities -- @}



class TestShotgun(TestCaseBase):
    __slots__ = ()
    
        
    def test_factory_update_schema(self):
        """Tests some methods which may communicate to shotgun"""
        # Only to be updated once in a while
        #######
        return
        #######
        
        conn = ProxyShotgunConnection()
        
        count = 0
        for count, path in enumerate(ShotgunTypeFactory.update_schema(conn)):
            assert path.isfile()
        # end for each path
        assert count
        
    def test_factor_create_testdb(self):
        """Trivially create a local copy of all shotgun data and pickle it"""
        # Must only run on demand
        #########
        return
        #########
        ShotgunTestDatabase.rebuild_database()
        
    def test_factory(self):
        """Test type-creation features"""
        fac = ShotgunTypeFactory()
        self.failUnlessRaises(NameError, fac.type_by_name, 'foo')
        sgdb = ShotgunTestDatabase(use_records_cache = True)
        
        # Create every type
        info_every = 500
        tid = 0
        for tid, type_name in enumerate(fac.type_names()):
            sgtype = fac.type_by_name(type_name)
            # DEBUG ! - this takes 90s/10s (json/fast) to load !
            # It was useful for testing, but probably won't be required to look at all the time
            ##################################
            if type_name == 'EventLogEntry':
                continue
            ##################################
            assert issubclass(sgtype, ShotgunEntity)
            assert fac.type_by_name(type_name) is sgtype, "should cache the type"
            assert len(sgtype.sg_schema)
            
            # Query properties with data
            # To improve load times by factor 3, pickle the files uncompressed
            
            # our schema knows more entities than there is data. This is fine, the sg schema is not 100% 
            # well formed
            if not sgdb.has_records(type_name):
                continue
            # end ignore weird entities
            
            records = sgdb.records(type_name)
            
            # Test very value in each record
            for rid, record in enumerate(records):
                entity = sgtype(record['id'], record)
                assert len(entity.changed_properties()) == 0
                for name, descriptor in entity.sg_schema.iteritems():
                    prop = getattr(entity, name)
                    
                    if not prop.has_value():
                        # in case of dates, it's okay to get a date at time '0', but we don't check it
                        if not issubclass(descriptor._value_type, sgtypes._ShotgunDateMixin):
                            assert not prop.value(), "no property should return an actual value if it doesn't say so"
                        # end handle value type
                    # end 
                    
                    if isinstance(prop, ShotgunEntityProperty):
                        # All values that are attached will be returned, disregarding the declared valid types
                        enode = prop.value()
                        assert enode is None or isinstance(enode, ShotgunEntity)
                        assert_set_entity(entity, prop, enode, descriptor, fac)
                    elif isinstance(prop, ShotgunMultiEntityProperty):
                        value = prop.values()
                        assert isinstance(value, list)
                        assert_set_entity(entity, prop, value, descriptor, fac)
                    else:
                        # The value type is sometimes just our wrapper, which returns the original type
                        # Those are date types
                        value = prop.value()
                        if not isinstance(value, (datetime, date)):
                            assert descriptor._value_type.isinstance(value)
                        assert_set_value(entity, prop, value, descriptor)
                    # end handle assertion
                #end for each schema entry
                
                if rid and rid % info_every == 0:
                    print >> sys.stderr, "Processed %s record %i/%i" % (type_name, rid, len(records))
                # end provide info
                
                # NOTE: We break here as it should be enough
                ##################################################
                # For stress testing, remove this break !
                break
                ##################################################
            # end for each record
        # end for each type
        assert tid
        
    def test_types(self):
        """Test some specific type properties"""
        # Color
        col = sgtypes.ShotgunColor()
        assert col.is_symbolic(), "empty colors are automatically symbolic"
        for cid in range(3):
            assert col.channel(cid) == 0
        # for each channel
        self.failUnlessRaises(IndexError, col.channel, 3)
        
        col = sgtypes.ShotgunColor('255,40,0')
        assert not col.is_symbolic()
        assert col.r == 255 and col.g == 40 and col.b == 0
        
        col = sgtypes.ShotgunColor('symbol')
        assert col.is_symbolic()
        assert col.channels() == [0, 0, 0]
        
        # Creation
        assert sgtypes.ShotgunColor.new(tuple(), symbol='foo').is_symbolic()
        assert sgtypes.ShotgunColor.new((1,2,3)).channels() == [1,2,3]
    
        
        


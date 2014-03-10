#-*-coding:utf-8-*-
"""
@package bcore.tests.db.shotgun.base
@brief Some basic testing utilities

@copyright 2013 Sebastian Thiel
"""
__all__ = ['ShotgunTestDatabase', 'ReadOnlyTestSQLProxyShotgunConnection']

import json
import marshal
import time
import sys
import zlib


from bcore.tests import TestCaseBase
from bcore.db.shotgun import (
                                ProxyShotgunConnection,
                                SQLProxyShotgunConnection,
                                ProxyMeta
                          )
from bcore.db.shotgun.orm import ShotgunTypeFactory


class ShotgunTestDatabase(object):
    """A test database that can be used for testing read-only, but that can be writte in memory.
    Every time a value is queried, it will be deserialized from disk.
    
    It provides automatic creation of an intermediate 'fast' cache  which is faster to read
    """
    __slots__ = (
                    '_use_records_cache'
                )
    
    
    def __init__(self, use_records_cache = True):
        """Initialize this instance
        @param use_records_cache if True, when 'records' are queried the first time, a fast cache file
        of the records will be created. It loads 60 times faster than json"""
        self._use_records_cache = use_records_cache
    
    @classmethod
    def _record_storage_path(cls, type_name):
        """@return path to shotgun storage data"""
        return TestCaseBase.fixture_path('db/shotgun/json/%s.json.zip' % type_name)
        
    @classmethod
    def _record_fast_storage_path(cls, type_name):
        """@return path to file for storing records in a fast cache format"""
        return cls._record_storage_path(type_name) + '.marshal_tmp'
        
    @classmethod
    def _serialize_records(cls, path, records):
        """Write all records to the given path"""
        open(path, 'w').write(zlib.compress(json.dumps(records, indent=4, separators=(',', ': '), default=str), 9))
        
    @classmethod
    def _deserialize_records(cls, path):
        """@return deserialized shotgun records"""
        return json.loads(zlib.decompress(open(path).read()))
        
        
    # -------------------------
    ## @name Initialization
    # @{
    
    @classmethod
    def rebuild_database(cls):
        """Retrieve all data for all known entity types from shotgun. Known types are determined by the 
        factory schema."""
        conn = ProxyShotgunConnection()
        fac = ShotgunTypeFactory()
        
        for type_name in fac.type_names():
            schema = fac._deserialize_schema(fac._schema_path(type_name))
            path = cls._record_storage_path(type_name)
            print >> sys.stderr, "Dumping '%s' data to %s ..." % (type_name, path)
            st = time.time()
            records = conn.find(type_name, list(), schema.keys())
            cls._serialize_records(path, records)
            print >> sys.stderr, "Obtained %i '%s' records in %fs" % (len(records), type_name, time.time() - st)
        # end for each schema to read
    
    ## -- End Initialization -- @}
        

    # -------------------------
    ## @name Interface
    # @{
    
    def has_records(self, type_name):
        """@return True if records exist for the given shotgun data type
        @param type_name the Shotgun entity type, like 'Asset'"""
        return self._record_storage_path(type_name).isfile()
    
    def records(self, type_name):
        """@return a list of dictionaries in a format you would receive when queried using the API.
        It will be owned by you, as it is freshly deserialized
        @param type_name the Shotgun type name, like 'Asset'
        @note check for has_records beforehand"""
        assert self.has_records(type_name)
        ppath = self._record_fast_storage_path(type_name)
        st = time.time()
        cache_type = 'json'
        if self._use_records_cache and ppath.isfile():
            records = marshal.load(open(ppath))
            cache_type = 'fast'
        else:
            records = self._deserialize_records(self._record_storage_path(type_name))
            if self._use_records_cache and not ppath.isfile():
                rst = time.time()
                marshal.dump(records, open(ppath, 'w'))
                print >> sys.stderr, "Wrote %i records in %ss into fast cache" % (len(records), time.time() - rst)
            # end update pickle cache
        # end load pickle cache
        args = (type_name, cache_type, len(records), time.time() - st)
        print "Loaded '%s' dataset(%s) with %i records in %fs" % args
        return records
        
    def serialize_records(self, type_name, records):
        """Create or udpate a serialized version of records, which match the give shotgun type_name
        @return self"""
        st = time.time()
        self._serialize_records(self._record_storage_path(type_name))
        print >> sys.stderr, "Serialized %i records in %fs" % (len(records), time.time() - st)
        return self
                
    
    ## -- End Interface -- @}
    
# end class ShotgunTestDatabase


class ReadOnlyProxyMeta(ProxyMeta):
    """Non-Read-only methods will cause an exception, when called. This prevents write calls from 
    leaving the test-bed"""
    __slots__ = ()

    @classmethod
    def _create_method(cls, method_name, is_readonly, proxy_attr):
        """@return a new method named method_name that does not alter it's instance
        @note all additional arguments are mainly for your information
        @param cls this metaclass instance
        @param method_name name of method that is to be created
        @param is_readonly if True, the method must not change the underlying object
        @param proxy_attr the name of the attribute on instance that keeps the proxy instance."""
        if is_readonly:
            # don't override methods in our direct base
            if method_name in SQLProxyShotgunConnection.__dict__:
                return SQLProxyShotgunConnection.__dict__[method_name]
            return super(ReadOnlyProxyMeta, cls)._create_method(method_name, is_readonly, proxy_attr)
        else:
            def write_not_permitted(*args, **kwargs):
                raise AssertionError("%s: Cannot change database in test-mode" % method_name)
            return write_not_permitted
        # end handle read-onlyness
    ## -- End Subclass Interface -- @}
    

# end class ReadOnlyProxyMeta


class ReadOnlyTestSQLProxyShotgunConnection(SQLProxyShotgunConnection):
    """A front-end to the normal SQLProxyShotgunConnection which simply skips writes 
    and helps to auto-generate it's underlying SQL database"""
    __slots__ = ()
    __metaclass__ = ReadOnlyProxyMeta
    
    
    def __init__(self, db_url = None):
        """Initialize ourselves, making sure we read from our own database, if needed."""
        # If we don't yet have a test-database, rebuild it automatically
        # Must happen before super class is initialized, as it will create a base file right away
        if not self.has_database():
            self.rebuild_database()
        # end handle rebuild on demand
        
        
        if db_url is None:
            db_url = self._sqlite_rodb_url()
        super(ReadOnlyTestSQLProxyShotgunConnection, self).__init__(db_url)
        
    def _set_cache_(self, name):
        if name == '_proxy':
            assert False, "Cannot use shotgun proxy, please check your test to assure it doesn't trigger it"
        else:
            super(ReadOnlyTestSQLProxyShotgunConnection, self)._set_cache_(name)
        #end handle engine instantiation
        
    @classmethod
    def _sqlite_rodb_url(cls):
        """@return an sqlalchemy compatible engine URL to our local READ-ONLY database
        It will be created on the fly and must not be checked in"""
        return 'sqlite:///%s' % cls._sqlite_rodb_path() 
        
    @classmethod
    def _sqlite_rodb_path(cls):
        """@return a path to the designated sqlite database"""
        return TestCaseBase.fixture_path('db/shotgun/sqlite.db_tmp')
    
    # -------------------------
    ## @name Test Database Initialization
    # @{
    
    @classmethod
    def has_database(cls):
        """@return True if our database is initialized. If not, rebuild_database() should be called"""
        return cls._sqlite_rodb_path().isfile()
        
    @classmethod
    def rebuild_database(cls):
        """Build our read-only test database from scratch, using data from the ShotgunTestDatabase
        @return a new instance of our type"""
        sqlite_path = cls._sqlite_rodb_path()
        if sqlite_path.isfile():
            sqlite_path.remove()
        #end clear previous database
        
        fac = ShotgunTypeFactory()
        fetcher = ShotgunTestDatabase().records
        
        return cls(SQLProxyShotgunConnection.init_database(cls._sqlite_rodb_url(), fac, fetcher)._meta)
    
    
    
    ## -- End Test Database Initialization -- @}

    

# end class ReadOnlyTestSQLProxyShotgunConnection


#-*-coding:utf-8-*-
"""
@package bcore.db.shotgun.sql
@brief An SQL backend for shotgun, to allow increasing performance of shotgun interaction of local tools

@note needs sqlalchemy
@copyright 2013 Sebastian Thiel
"""
__all__ = ['SQLProxyShotgunConnection']


import sys
import time

from marshal import (
                        dumps,
                        loads
                    )
from zlib import (
                    compress,
                    decompress
                 )
from cStringIO import StringIO

import sqlalchemy
from sqlalchemy.schema import (
                                  Table,
                                  Column,
                                  MetaData,
                              )

from sqlalchemy.types import (
                                Integer,
                                Binary,
                             )

from .base import (
                    ProxyMeta,
                    ProxyShotgunConnection,
                    shotgun_schema
                  )

from bcore.core.kvstore import (
                                KeyValueStoreSchema,
                                KeyValueStoreSchemaValidator
                            )



sql_schema = KeyValueStoreSchemaValidator.merge_schemas((shotgun_schema,
                                                        KeyValueStoreSchema(shotgun_schema.key(), 
                                                                            { 'sql_cache_url' : str })))


class SQLProxyShotgunConnection(ProxyShotgunConnection):
    """A database that uses an SQLAlchemy engine to direct all reads to the database.
    
    Write operations go straight to shotgun. Those are expected to be written back to our database by other 
    means"""
    __slots__ = (
                    '_meta'   # Our SQL engine
                )
    
    _schema = sql_schema
    
    def __init__(self, db_url = None):
        """Initialize this instance with the given database URL
        If none, it will be set using kwstore data"""
        self.set_db_url(db_url)
    
    def _set_cache_(self, name):
        if name == '_meta':
            # Use kvstore information to get engine URL
            shotgun = self.context_value()
            assert shotgun.sql_cache_url, "No valid sql_cache_url found"
            self.set_db_url(shotgun.sql_cache_url)
            
        else:
            super(SQLProxyShotgunConnection, self)._set_cache_(name)
        #end handle engine instantiation
    
    # -------------------------
    ## @name Schema Handling
    # @{
    
    @classmethod
    def _make_table(cls, type_name, meta_data):
        """@return an SQLAlchemy table schema made to keep data of the given shotgun data type
        @param cls
        @param type_name shotgun typename
        @param meta_data SQLAlchemy meta data object to which to associate the table
        @note table names will be lower case !"""
        return Table(type_name.lower(), meta_data,
                     Column('id', Integer, primary_key = True),
                     Column('properties', Binary),
                    )
    
    @classmethod
    def _make_meta_data(cls, factory):
        """@return an SQLAlchemy MetaData object initialized with our Schema, based on the one of the 
        given factory
        @param cls
        @param factory instance of type ShotgunTypeFactory"""
        md = MetaData()
        for type_name in factory.type_names():
            cls._make_table(type_name, md)
        # end for each typename to create table for
        return md
        
    @classmethod
    def _serialize_properties(cls, record):
        """@return string representing the given record in a serialized format"""
        return compress(dumps(record), 9)
        
    @classmethod
    def _deserialize_properties(cls, properties_buffer):
        """@return a dict that was formerly serialized with _serialize_properties
        @param cls
        @param properties_buffer a buffer object representing the binary properties blob"""
        return loads(decompress(properties_buffer))
        
    ## -- End Schema Handling -- @}
    
    # -------------------------
    ## @name Initialization
    # Methods to be called specifically to initialize a new database with data
    # @{
    
    @classmethod
    def init_database(cls, engine_url, factory, fetch_entity_data_fun):
        """Intiialze the database at the given engine_url based on entity schema data obtainable from the 
        given factory.
        @param cls
        @param engine_url an sqlalchemy engine URL to an EMPTY database
        @param factory a ShotgunTypeFactory instance
        @param fetch_entity_data_fun a function f(type_name) -> [entity_dict, ...] returning 
        whatever the shotgun API would return when querying all entities of a given type.
        @return a new instance of ourselves initialized to use the given engine_url to fetch data from"""
        engine = sqlalchemy.create_engine(engine_url)
        existing_meta_data = MetaData(engine, reflect = True)
        if existing_meta_data.tables:
            raise AssertionError("Database at '%s' was not empty" % engine_url)
        # end verify  empty database
        
        meta = cls._make_meta_data(factory)
        meta.bind = engine
        meta.create_all()
        
        # now, for each table we have, query all data and fill it in
        connection = engine.connect()
        execute = engine.connect().execute
        serialize = cls._serialize_properties
        
        for type_name in factory.type_names():
            insert = meta.tables[type_name.lower()].insert()
            with connection.begin() as trans:
                records = list()
                records_append = records.append
                for rid, record in enumerate(fetch_entity_data_fun(type_name)):
                    records_append({'id' : record['id'], 'properties' : serialize(record)})
                # end for each record
                # multi-insert for a major speedup !
                st = time.time()
                execute(insert, records)
                trans.commit()
                print >> sys.stderr, "Inserted %i records into %s in %fs" % (rid, engine_url, time.time() - st)
                # end for each type
            # end with transaction
        # end for each shotgun_type/table
        
        return cls(meta)
    ## -- End Initialization -- @}
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    def set_db_url(self, db_url):
        """Set this instance to connect to the given database
        @param db_url An SQL alchemy compatible database URL, or None, in which case we will drop the existing
        database connection and re-connect using kvstore data when needed.
        It can also be an SQLAlchemy.MetaData instance, which will be used directly
        @return this instance"""
        if not db_url:
            try:
                del(self._meta)
            except AttributeError:
                pass
            # end ignore no engine
        else:
            # Connect right away and obtain schema from database itself
            if isinstance(db_url, MetaData):
                meta = db_url
            else:
                meta = MetaData(db_url, reflect = True)
            self._meta = meta
        # end handle mode of operation
        
        return self
        
    
    ## -- End Interface -- @}
    
    
    # -------------------------
    ## @name Shotgun Interface Overrides
    # @{
    
    def find(self, entity_type, filters, fields, order = list(), filter_operator = "all", limit = 0, 
                       retired_only = False, page = 0):
        """@see https://github.com/shotgunsoftware/python-api/wiki/Reference:-Methods#wiki-find
        @note this implementation will only work for ID based filters or an empty filter. If we can't reproduce
        what our arguments demand, we will just pass the call on to our base class.
        @note will always return *all* fields that are known to the schema, assuming that user's who don't want
        that don't use it anyway."""
        # dict filters = nested expression
        return_super = lambda: super(SQLProxyShotgunConnection, self).find(entity_type, filters, fields, order,
                                                                filter_operator, limit, retired_only, page)
        if len(filters) > 1 or isinstance(filters, dict) or not fields or order or \
            filter_operator != 'all' or retired_only or page > 0:
            return return_super()
        # end bail out with super class call
        
        # check the filter - the only thing we can do is all ids or one id
        if filters:
            # FETCH ONE
            ############
            assert len(filters) == 1
            field, op, id_to_find = filters[0]
            if field != 'id' or op != 'is':
                return return_super()
            # end handle filters
            # find one with ID
            tbl = self._meta.tables[entity_type.lower()]
            res = sqlalchemy.select([tbl.c.properties], tbl.c.id == id_to_find).execute().fetchall()
            if not res:
                return list()
            assert len(res) == 1
            res = [self._deserialize_properties(res[0][0])]
        else:
            # FETCH ALL
            #############
            if not limit:
                limit = None
            # end convert limit
            result = sqlalchemy.select([self._meta.tables[entity_type.lower()].c.properties], limit=limit).execute().fetchall()
            res = [self._deserialize_properties(row[0]) for row in result if row[0] is not None]
        # end handle filters term
        return res
        
    def find_one(self, entity_type, filters, fields = ['id'], order = list(), filter_operator = 'all'):
        """@see https://github.com/shotgunsoftware/python-api/wiki/Reference:-Methods#wiki-find_one
        @note will work similarly, but with all limitations of find()
        @return None if the given entity was not found.
        """
        res = self.find(entity_type, filters, fields, order, filter_operator, limit = 1)
        if not res:
            return None
        return res[0]
        
    ## -- End Shotgun Interface Overrides -- @}
    

    

# end class SQLProxyShotgunConnection





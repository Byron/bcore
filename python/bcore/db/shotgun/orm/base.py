#-*-coding:utf-8-*-
"""
@package bcore.db.shotgun.orm.base
@brief Contains factories and base types to deal with shotgun specific issues

@copyright 2013 Sebastian Thiel
"""
__all__ = ['ShotgunTypeFactory', 'ShotgunEntity', 'ShotgunEntityMeta', 
           'ShotgunPropertyDescriptor', 'ShotgunProperty', 
           'ShotgunEntityProperty', 'ShotgunMultiEntityProperty']

from bcore import ILog
from bcore.utility import (
                            Singleton,
                            DictObject,
                            LazyMixin
                       )
from bcore.path import Path
from bcore.core.properties import (
                                    PropertyDescriptor,
                                    PropertyBase,
                                    PropertySchemaMeta
                                )
from .types import (
                    value_type_map,
                    _ShotgunDateMixin,
                    ShotgunEntityMarker,
                    ShotgunMultiEntityMarker,
                   )
                    

from copy import deepcopy
import cPickle as pickle
import zlib


log = service(ILog).new('bcore.db.shotgun.orm')


# -------------------------
## @name Module-Global Information
# @{

## A set of names of entities/valid types which are not really part of the system and must be ignored
shotgun_gui_entity_types = set((  'Banners', 
                                  'AppWelcome', 
                                  'Banner', 
                                  'Tag', 
                                  'DisplayColumn',
                                  'EntityFieldPref',
                                  'NoteLink',
                                  'FormattingRule',
                                  'WorkDayRule',
                                  'NoteTask',
                                  'SavedFilter',
                                  ))


## -- End Global Information -- @}

# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

def create_shotgun_entity(data, resolve_type_fun, parent_entity):
    """Create a shotgun entity from data and a type map.
    @param data returned from shotgun, with information for a single entity and id and type fields
    @param resolve_type_fun a function returning a type by a name
    @param parent_entity the entity whose property triggered this call. It is used to initialize connection 
    information right away
    @return The newly created entity instance
    """
    return resolve_type_fun(str(data['type']))(data['id'], fetch_data_fun = parent_entity._fetch_data_fun, name = data.get('name'))

## -- End Utilities -- @}


def log_entity_creation_failure(data, parent_entity, property_name):
    """Emit a log error detailing the problem that occurred when create_shotgun_entity() failed"""
    log.error("Failed to instantiate '%s(%i)' connected to %s.%s", data['type'], data['id'], parent_entity, property_name, exc_info=True)


class ShotgunEntity(LazyMixin):
    """The base object for all shotgun types returned by the ShotgunTypeFactory.
    
    Automatically generated types will inherit all methods of this type accordingly
    
    We provide a lazy data retrieval mechanism through a shotgun connection. Either we
    are initialized with data, or we will retrieve it (all at once) the first time someone wants 
    to access it.
    
    Writes to attributes are cached, and methods are provided to retrieve only changed values, 
    and to write them back using the 'batch' method. This base is flexible enough to 
    serve as base for other implementations which have their own constraints and requirements.
    
    @note we explicitly don't specify a meta-class here, we are a just a base without 
    without any further type information
    """
    __slots__ = (
                    '_id',              # We know our type, this is our shotgun ID
                    '_name',            # Our name identifier - it's mutable and generated from "name" or "code"
                    '_fetch_data_fun',  # function f(self) -> value_dict 
                    '_base_value_dict', # simple dict with the initial version of our values
                    '_value_dict'       # A copy of _base_value_dict which receives all our writes
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Attribute at which to store our schema
    _schema_attribute = 'sg_schema'
    
    ## -- End Configuration -- @}
    
    def __init__(self, id, value_dict = None, fetch_data_fun = None, name = None):
        """Initialize this instance
        @param id our unique shotgun ID as integer
        @param name optional name, which is a copy of the 'code' or 'name' property of entities. Its provided
        when an Entity is specified as link, for GUI purposes. Its entirely optional though
        @param value_dict a plain dictionary as retrieved when querying all our fields using find_one() or None
        to allow delayed retrieval.
        @param fetch_data_fun if not None, an IShotgunConnection compatible instance that can be used to retrieve
        a value_dict for all ouri fields using f(self) -> value_dict.
        The function should bind whichever connections it needs to retrieve the value
        """
        assert isinstance(id, int), "shotgun ids are integers"
        self._id = id
        self._base_value_dict = None
        self._name = name
        if value_dict:
            self._set_value_dict(value_dict)
        self._fetch_data_fun = fetch_data_fun
        
    def __str__(self):
        return "%s(%i)" % (self.__class__.__name__, self._id)
        
    def __eq__(self, rhs):
        """@return True if we are the same entity as the other one"""
        if self.__class__ is not rhs.__class__:
            return False
        return self._id == rhs._id
    
    def _set_cache_(self, name):
        if name == '_value_dict':
            assert self._fetch_data_fun, "Require fetch_data function to be able to retrieve entity data"
            self._set_value_dict(self._fetch_data_fun(self))
        else:
            super(ShotgunEntity, self)._set_cache_(name)
        # end handle set cache
            
    def _set_value_dict(self, value_dict):
        """Set our internal dicts to represent the given value_dict, keeping possible changes
        @note for now we loose our local changes when calling this function. However, we can easily
        implement that it won't happen"""
        self._base_value_dict = value_dict
        self._value_dict = deepcopy(value_dict)
        
        
    # -------------------------
    ## @name Interface
    # @{
    
    def to_link_dict(self):
        """@return ourselves as minimal dict representation, useful for setting us as raw value in a shotgun
        data dictionary (as retrieved from the server)"""
        res = dict(id = self._id, type = type(self).__name__)
        # in order to suffice constraints, we must provide the name if we have it
        if self._name:
            res['name'] = self._name
        # end handle name
        return res 
    
    def changed_properties(self):
        """@return list of string names of properties that have changed compared
        to the value we initially fetched."""
        if self._base_value_dict is None:
            return list()
        # end handle uninitialized record
        
        out = list()
        for (name, lhs) in self._base_value_dict.iteritems():
            rhs = self._value_dict[name]
            # enforce eq to be called (instead of ne)
            if not (lhs == rhs):
                out.append(name)
            # end if there is a mismatch
        # end for each name, lhs, rhs tuple
        return out
    ## -- End Interface -- @}
        
# end class ShotgunEntity


class ShotgunProperty(PropertyBase):
    """Implements a shotgun property and access through a ShotgunEntity"""
    __slots__ = ()

    # -------------------------
    ## @name Interface
    # @{
    
    def has_value(self):
        """@return True if our value is set. If False is returned, the value you receive when querying
        will just be a default value."""
        return bool(self._instance._value_dict[self._descriptor.partial_name()])
    
    def value(self):
        """@return the currently stored value, or None if no value is stored.
        In the latter case, """
        desc = self._descriptor
        assert desc._value_type is not None
        
        val = self._instance._value_dict.get(desc.partial_name())
        
        if not val:
            return desc._value_type()
        # end handle empty value/None
        
        # Call the constructor, as this may fix certain values that are just strings in our database, but
        # should be actual times (date, datetime)
        # NOTE: If we have changed the type, in case of datetime, we have to set. Otherwise we break constraints
        # For some reason, sometimes we get unicode strings instead of Numbers, so let's convert.
        # Conversion is smart, and will only change the value if needed
        val = desc._value_type(val)
        if issubclass(desc._value_type, _ShotgunDateMixin):
            # Store the fixed value - this is just because of the test database using strings as date-time objects,
            # which wouldn't be returned by the shotgun API otherwise. However, it's probably not bad either
            # to have the logic here and keep it
            # NOTE: assumes converted type via _value_type(val)
            name = desc.partial_name()
            # but only if we had a value, otherwise we would create one
            base_value = self._instance._base_value_dict[name]
            if base_value and not isinstance(base_value, type(val)):
                self._instance._base_value_dict[name] = val
            # end handle set base
            self._instance._value_dict[name] = val
        # end handle type change
        return val
   
    def set_value(self, value):
        """Set primitive values
        @note If None is given, the value is set the None, making has_value() return False accordingly
        @throws TypeError if the type does not match what we need"""
        if value is None:
            self._instance._value_dict[self._descriptor.partial_name()] = value
            return self
        # end set own value None
        # Falls through, so type is only changed when needed and convertible.
        # Throws otherwise
        value = self._descriptor._value_type(value)
        
        if self.value() == value:
            return self
        
        
        self._instance._value_dict[self._descriptor.partial_name()] = value
        return self
        
    def delete(self):
        raise NotImplementedError('Deletion of Shotgun fields is not supported')
    
    ## -- End Interface -- @}

# end class ShotgunProperty


class ShotgunEntityProperty(ShotgunProperty):
    """A property which will produce and return a ShotgunEntity"""
    __slots__ = ()
    
    def value(self):
        """@return A single Entity node"""
        desc = self._descriptor
        val = self._instance._value_dict.get(desc.partial_name())
        
        if not val or not desc._valid_types:
            return None
        # end handle no connection or invalid property
        try:
            return create_shotgun_entity(val, desc._resolve_type_fun, self._instance)
        except Exception:
            # Can happen if there are entities attached that are not allowed
            log_entity_creation_failure(val, self._instance, desc.name())
            return None
        # end handle data inconsistency
        
    def set_value(self, entity):
        """Set ourselves to point to the given entity. May be None to mark no connection
        @param entity a ShotgunEntity instance, or None to unset the current value
        @throws TypeError if the input entity is not of type ShotgunEntity"""
        desc = self._descriptor
        if entity is None:
            self._instance._value_dict[desc.partial_name()] = entity
            return self
        # end handle entity
        
        if not isinstance(entity, ShotgunEntity):
            raise TypeError("Invalid input type '%s', expected ShotgunEntity" % type(entity))
        # end check type
        
        if self.value() == entity:
            return self
        # end handle value
        
        # fill the dict accordingly - we don't keep the wrapped object
        self._instance._value_dict[self._descriptor.partial_name()] = entity.to_link_dict()
        return self
        
# end class ShotgunEntityProperty


class ShotgunMultiEntityProperty(ShotgunProperty):
    """A property which provides a custom interface to return multiple entities"""
    __slots__ = ()

    # -------------------------
    ## @name Interface
    # @{
    
    def values(self):
        """@return a list with all Entities connected to this property.
        The list may be empty"""
        desc = self._descriptor
        elist = self._instance._value_dict.get(desc.partial_name())
        
        entities = list()
        
        # We can be an invalid entity attribute, if all our types where invalid
        # elist can be None
        if not elist or not desc._valid_types:
            return entities
        # end handle invalid property
        
        for edata in elist:
            try:
                entities.append(create_shotgun_entity(edata, desc._resolve_type_fun, self._instance))
            except Exception:
                log_entity_creation_failure(edata, self._instance, desc.name())
                continue
            # end handle data inconsistency
        # end for each entity data block
        return entities
    
    ## -- End Interface -- @}
    
    def set_value(self, entity):
        """Set the given entity to be the only one we know. This effectively resets the previous value
        entirely.
        If entity is None, all entity connections are cleared.
        It may also be a list, which makes this call similar to set_values()
        @param entity a ShotgunEntity instance or None. It may also be a list, in which case the behavior 
        equals the one of set_values()
        @todo use _valid_types for type checking
        @return self"""
        if not isinstance(entity, (tuple, list)):
            entity = [entity]
        # end handle multiple values
        
        return self.set_values(entity)
        
    def set_values(self, entities):
        """Set the given entities to be our connections. Each used entity type must be compatible to this 
        property, as defined in the property's schema.
        @param entities an iterable of ShotgunEntity instances
        @todo use _valid_types for type checking
        @return self"""
        verified_entities = list()
        for entity in entities:
            # Drop invalid-empty values
            if not entity:
                continue
            # end handle None/no value
            
            # NOTE: Should check if entity is one of _valid_types, but I feel that this will cause errors
            # as shotgun is full of connections that are not officially allowed !
            if not isinstance(entity, ShotgunEntity):
                raise TypeError("Invalid input type '%s', expected ShotgunEntity" % type(entity))
               
            verified_entities.append(entity)
        #end for each entity
        
        # Check if the value is actually the same (order independent)
        existing_entities = self.values()
        if len(existing_entities) == len(verified_entities) and set(existing_entities) == set(verified_entities):
            return self
        # end skip if there was no change, order independent for now
        
        # Finally convert and set the value
        self._instance._value_dict[self._descriptor.partial_name()] = [entity.to_link_dict() for entity in verified_entities]
        
        return self
        
    def value(self):
        """@return The first entity of values(), or None"""
        entities = self.values()
        if not entities:
            return None
        return entities[0]

# end class ShotgunMultiEntityProperty


class ShotgunPropertyDescriptor(PropertyDescriptor):
    """A descriptor specifically designed to handle the peculiarities of shotgun fields"""
    __slots__ = (
                    '_gui_name',       # The name it should have in user interfaces
                    '_value_type_name',# original name of the data-type (could also be member of actual value_type
                    '_value_type',     # Type we should use, either primitive or entity
                    '_valid_types',    # If value_type is an Entity/MutliEntity, those are the allowed subclasses as strings
                    '_resolve_type_fun',   # a function which returns a type by a name
                    '_editable',       # if True, writes are allowed in GUI environments
                    '_default'         # default value
                )
    
    
    value_type_property_map = {
        ShotgunEntityMarker : ShotgunEntityProperty,
        ShotgunMultiEntityMarker : ShotgunMultiEntityProperty
    }
    
    ## A mapping from shotgun data types to actual types
    ## We take it as class member to allow subclasses to have their own versions
    value_type_map = value_type_map
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## ShotgunProperty returned if it is not include in the value_type_property_map
    DefaultPropertyType = ShotgunProperty
    
    @property
    def PropertyType(self):
        """@return the actual ShotgunProperty we need, based on our value_type"""
        return self.value_type_property_map.get(self._value_type, self.DefaultPropertyType)
    
    ## -- End Configuration -- @}
    
    
    def __init__(self, name, gui_name, description, value_type, 
                       value_type_name, editable, default, valid_types, resolve_type_fun):
        """Initialize this instance with appropriate types"""
        super(ShotgunPropertyDescriptor, self).__init__(name, description)
        self._gui_name = gui_name
        self._value_type = value_type
        self._value_type_name = value_type_name
        
        self._valid_types = valid_types
        self._resolve_type_fun = resolve_type_fun
        
        self._editable = editable
        self._default = default
        
    @classmethod
    def new(cls, name, schema, resolve_type_fun):
        """@return a new property descriptor based on the given shotgun schema
        @param cls
        @param name the name under which to store the property descriptor
        @param schema the schema dict for new property descriptor
        @param resolve_type_fun a function to resolve the type by a type name
        """
        valid_types = tuple()
        if 'valid_types' in schema.properties:
            # NOTE: in order to avoid infinite recursion (we could refer to our own type which is 
            # currently being created), we rely on a post-process by our meta-class to set the types 
            # afterwards. Strings are just temporary
            valid_types = schema.properties.valid_types.value
        # end handle valid types
        
        value_type_name = schema.data_type.value
        value_type = cls.value_type_map.get(value_type_name)
        if value_type is None:
            # The entity type is special, as it requires a custom creator
            # NOTE: Cannot make assertion as the DB can change without us knowing at all times
            log.error("Unknown data type encountered: '%s' - fix required !", value_type_name)
            # Defer the clash, None will cause failure, but later on if someone really queries the value
            # NOTE: maybe we should just crash here to not let the bug get a away ... failure will happen,
            # with a str type at least it should survive reads
            value_type = None
        # end handle no value type
        
        return cls( name, 
                    schema.name.value, 
                    schema.description.value,
                    value_type,
                    value_type_name,
                    schema.editable.value,
                    schema.properties.default_value.value,
                    valid_types,
                    resolve_type_fun)
        

# end class ShotgunPropertyDescriptor


class ShotgunEntityMeta(PropertySchemaMeta):
    """A metaclass to generate shotgun entity types on the fly"""
    __slots__ = ()
    
    ## Attribute that a type must have that we can create accordingly
    CLASS_SHOTGUN_SCHEMA_ATTRIBUTE = '_sg_schema'
    
    ## Attribute with function that can resolve types we encounter
    CLASS_SHOTGUN_FACTORY_INSTANCE_ATTRIBUTE = '_sg_type_resolver'
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## The type we use when instantiating shotgun properties
    ShotgunPropertyDescriptorType = ShotgunPropertyDescriptor
    
    ## -- End Configuration -- @}
    
    
    def __new__(metacls, name, bases, clsdict):
        """Create a new shotgun type
        
        We will setup properties according to the types schema
        """
        # We don't store this schema, doesn't need to remain in memory
        schema = clsdict.pop(metacls.CLASS_SHOTGUN_SCHEMA_ATTRIBUTE)
        factory = clsdict.pop(metacls.CLASS_SHOTGUN_FACTORY_INSTANCE_ATTRIBUTE)
        assert schema is not None and factory, "Any subtype of ShotgunEntity is supposed to have the CLASS_SHOTGUN_SCHEMA_ATTRIBUTE and CLASS_SHOTGUN_FACTORY_INSTANCE_ATTRIBUTE set"
        
        for attr_name, schema in schema.iteritems():
            assert attr_name not in clsdict, "Will not overwrite existing class members with generated ones"
            clsdict[attr_name] = metacls.ShotgunPropertyDescriptorType.new(attr_name, schema, factory.type_by_name)
        # end for each name, schema pair
        
        return super(ShotgunEntityMeta, metacls).__new__(metacls, name, bases, clsdict)
        


# end class ShotgunEntityMeta



class ShotgunTypeFactory(Singleton):
    """A utility to help producing custom types and keeping caching them
    
    We rely on a serialized version of the 
    """
    __slots__ = (
                    '_type_map'    # a mapping of type_name (e.g. Asset) to the actual type 
                )
    
    SCHEMA_FILE_EXTENSION = '.pickle.zip' 
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Type to use as base for all types we generate
    ShotgunEntityBaseType = ShotgunEntity
    
    ## The meta class to use to create new types
    ShotgunEntityMetaType = ShotgunEntityMeta
    
    ## -- End Configuration -- @}
    
    def __init__(self):
        """Initialize instance attributes"""
        self._type_map = dict()
        
    # -------------------------
    ## @name Internal Utilities
    # @{
    
    @classmethod
    def _schema_path(cls, type_name):
        """@return path to our schema for the specified shotgun type"""
        return Path(__file__).dirname() / 'schema' / ('%s%s' % (type_name, cls.SCHEMA_FILE_EXTENSION))
        
    @classmethod
    def _serialize_schema(cls, schema):
        """Serialize the given schema data (for all shotgun types)
        @return schema paths"""
        paths = list()
        for type_name, type_schema in schema.iteritems():
            paths.append(cls._schema_path(type_name))
            open(paths[-1], 'w').write(zlib.compress(pickle.dumps(DictObject(type_schema)), 9))
        # end for each type
        return paths
    
    @classmethod
    def _deserialize_schema(cls, schema_path):
        """Deserialize the schema dict which was formerly serialized using _serialize_schema()
        @param cls
        @param schema_path path to serialized schema"""
        return pickle.loads(zlib.decompress(open(schema_path).read()))
        
    def _resolve_type_name(self, type_name):
        """@return the newly create Type instance for the given type_name
        Will create the type based on the stored schema information
        @throws NameError"""
        if type_name in shotgun_gui_entity_types:
            log.info("Shotgun type named '%s' is a gui type, which will just be stubbed" % type_name)
            schema = DictObject()
        # end handle gui types
        else:
            schema_path = self._schema_path(type_name)
            if not schema_path.isfile():
                raise NameError("Shotgun type named '%s' unknown in our cached schema" % type_name)
            # end handle unknown types
            
            schema = self._deserialize_schema(schema_path)
        # end obtain schema
        
        return self.ShotgunEntityMetaType(type_name, (self.ShotgunEntityBaseType, ), 
                                        { 
                                          self.ShotgunEntityMetaType.CLASS_SHOTGUN_SCHEMA_ATTRIBUTE : schema,
                                          self.ShotgunEntityMetaType.CLASS_SHOTGUN_FACTORY_INSTANCE_ATTRIBUTE : self,
                                        })  
        
    ## -- End Internal Utilities -- @}
    
    # -------------------------
    ## @name Schema Database Setup
    # @{
    
    @classmethod
    def update_schema(cls, connection):
        """Load the schema using the given connection and write the respective schema information to disk
        for later consumption.
        @param cls
        @param connection an IShotgunConnection compatible type
        @note if changes are required, adjust the schema in shotgun and call this method
        @return a list of all paths of the updated or created schema files (one for each type"""
        return cls._serialize_schema(connection.schema_read())
        
    ## -- End Schema Database Setup -- @}
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    def type_by_name(self, type_name):
        """@return the Type suitable to represent the given name
        @param type_name Shotgun Entity type name, like 'Asset'. capitalization matters
        @throws NameError if the type_name does not exist in our known schema
        @note types are lazily created only when you demand it"""
        if type_name not in self._type_map:
            self._type_map[type_name] = self._resolve_type_name(type_name)
        # end handle type map
        return self._type_map[type_name]
        
    def type_names(self):
        """@return list of names of all known types, compatible to type_by_name"""
        return [f.basename().split('.')[0] for f in self._schema_path('foo').dirname().files('*%s' % self.SCHEMA_FILE_EXTENSION)] 
    
    ## -- End Interface -- @}

    

# end class ShotgunTypeFactory


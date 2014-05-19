#-*-coding:utf-8-*-
"""
@package bapp.properties
@brief Implementation of property descriptors and properties for Environment Context Clients

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['ContextPropertyDescriptor', 'PropertyApplicationSettingsMixinMeta',
           'PropertyApplicationSettingsMixin', 'CompoundPropertyDescriptor']

from bapp.utility import ApplicationSettingsMixin

from bkvstore import ( KeyValueStoreSchema,
                       RootKey )

from bproperty import    ( PropertySchemaMeta,
                           PropertyDescriptor,
                           CompoundPropertyDescriptor,
                           Property,
                           NotDeletableError,
                           NotWritableError )


class ContextPropertyDescriptor(PropertyDescriptor):
    """A descriptor which sets a particular value type, and simplified getters"""
    __slots__ = (
                    '_value_type', # the type values we return will have
                )
    
    def __init__(self, *args, **kwargs):
        """Initialize our type value
        @param args any args usually passed to our super class
        @param kwargs may contain a type"""
        self._value_type = kwargs.pop('type', None)
        assert self._value_type is not None, "type kwarg must be provided"
        super(ContextPropertyDescriptor, self).__init__(*args, **kwargs)
    
    def __get__(self, inst, cls):
        """@return our property initialized with default attributes
        @param inst instance through which we are accessed, or None
        @param cls always the class that owns us (which is not necessariliy type(inst))
        @note if we are accessed through the class, we always return ourselves"""
        if inst is None:
            return self
        # end handle class access
        
        # resolve value - as we are matching the schema, it is assumed to exist
        value = inst.value_cache()
        for token in self.name().split(PropertyDescriptor.NAME_SEPARATOR):
            value = value[token]
        # end for each token
        
        return value
    
    def __set__(self, inst, value):
        raise AttributeError("Cannot currently set KVStore values")
        
    def __delete__(self, inst):
        """Delete our property"""
        raise NotDeletableError(self.name())
        
    # -------------------------
    ## @name Interface
    # @{
    
    def value_type(self):
        """@return our value type"""
        return self._value_type
    
    ## -- End Interface -- @}
    
# end class ContextPropertyDescriptor


class PropertyApplicationSettingsMixinMeta(PropertySchemaMeta):
    """A meta-class to automatically assemble a simplified schema from ContextDescriptors"""
    __slots__ = ()
    
    ## Attribute in types we instantiate containing the root key
    CLASS_SCHEMA_ROOT_KEY_ATTRIBUTE = '_schema_root_key'

    @classmethod
    def _set_schema_value(cls, schema, name, descriptor):
        """Set just the descriptors value type"""
        schema[name] = descriptor.value_type()
        
    @classmethod
    def _store_schema(cls, clsdict, bases, attribute, schema):
        """Store schema as correct type"""
        root_key = cls._class_attribute_value(clsdict, bases, cls.CLASS_SCHEMA_ROOT_KEY_ATTRIBUTE)
        assert root_key, "RootKey must be set in type to be instantiated at cls.%s" % cls.CLASS_SCHEMA_ROOT_KEY_ATTRIBUTE
        clsdict[attribute] = KeyValueStoreSchema(root_key, schema)

# end class Property


class PropertyApplicationSettingsMixin(ApplicationSettingsMixin):
    """A context client to more easily accss context values, read-only"""
    __slots__ = (
                    '_settings_value_cache', # An optional cache for our context value, 
                )
    
    __metaclass__ = PropertyApplicationSettingsMixinMeta
    _schema_attribute = '_schema'
    
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Override this value to store your values underneath a different root
    _schema_root_key = RootKey
    
    ## -- End Configuration -- @}

    # -------------------------
    ## @name Context Value Caching
    # @{
    
    def update_value_cache(self):
        """Update our context value, which effectively retrieves a new value copy and stores it
        in the cache
        @return this instance"""
        self._settings_value_cache = self.settings_value()
        return self
        
    def has_value_cache(self):
        """@return True if we have a cached value"""
        return hasattr(self, '_settings_value_cache')
        
    def clear_value_cache(self):
        """Remove our value cache. This is ideally called when you are done with interacting with your values
        @return this instance"""
        if self.has_value_cache():
            del(self._settings_value_cache)
        # end remove cache attribute
        return self
        
    def value_cache(self):
        """@return our value cache
        @note will automatically be updated in case it doesn't yet exist"""
        if not self.has_value_cache():
            self.update_value_cache()
        return self._settings_value_cache
        
    ## -- End Context Value Caching -- @}

# end class PropertyApplicationSettingsMixin



#-*-coding:utf-8-*-
"""
@package butility.properties.base
@brief Base implementations for Properties using descriptors

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['PropertyError', 'NotWritableError', 'NoSuchPropertyError', 'NotDeletableError', 
           'PropertyBase', 'CompoundProperty', 
           'PropertyDescriptor', 'CompoundPropertyDescriptor',
           'PropertyMeta', 'PropertySchemaMeta']

from butility import (abstractmethod,
                     Error,
                     MetaBase)
import logging
import weakref

log = logging.getLogger('butility.properties')

# ==============================================================================
## @name Exceptions
# ------------------------------------------------------------------------------
## @{

class PropertyError(Error):
    """The base error for all property framework related errors"""
    __slots__ = ()

# end class PropertyError

class NotWritableError(PropertyError):
    """Thrown if a property could not be written to"""
    __slots__ = ()

# end class NotWritableError

class NotDeletableError(PropertyError):
    """Thrown if a could not be deleted"""
    __slots__ = ()


class NoSuchPropertyError(PropertyError):
    """Thrown if a CompoundProperty's child was requested that didn't exist"""
    __slots__ = ()

# end class NoSuchPropertyError

## -- End Exceptions -- @}




# ==============================================================================
## @name Properties
# ------------------------------------------------------------------------------
## @{

class PropertyBase(object):
    """A property returned by a property descriptor
    
    @note Instances of this type are considered transient, and must not be kept alive after use. Instead,
    they must be re-retrieved each time. One reason is that they keep a strong pointer to their owner's
    instance.
    
    @note even though Descriptors have support for read-only and/or write-only attributes, they 
    lack support for more complex attributes or interfaces, which this type is providing
    """
    __metaclass__ = MetaBase
    __slots__ = (
                    '_descriptor',   # A back-link to our descriptor
                    '_instance'      # A back-link to the instance who owns this property
                )
    
    def __init__(self, descriptor, instance):
        """Intialize this instance with the required backlinks"""
        self._descriptor = descriptor
        self._instance = instance
    
    # -------------------------
    ## @name Interface
    # @{
    
    @abstractmethod
    def delete(self):
        """Delete this property and it's value entirely
        @throws NotDeletableError"""
        
    @abstractmethod
    def value(self):
        """@return actual value of our property
        @note currently we consider all Properties readable, which is why a separate is_readable() 
        method is not provided."""
    
    @abstractmethod
    def set_value(self, value):
        """Set our actual value
        @return this property instance
        @throws NotWritableError"""
        
    ## -- End Interface -- @}

# end class PropertyBase


class CompoundProperty(PropertyBase):
    """A property which has named child-properties, allowing nested properties.
    @note this type just as intermediate object to return values by name"""
    __slots__ = ( )
    
    
    def __getattr__(self, name):
        """@return a child-property with the given name
        @throws AttributeError"""
        try:
            return self.property(name)
        except NoSuchPropertyError:
            raise AttributeError("Property named '%s' was not found" % name)
        # end handle name not found
        
    def __getitem__(self, name):
        """@return a child-property with the given name
        @throws KeyError
        @note useful to simulate dict access"""
        try:
            return self.property(name)
        except NoSuchPropertyError:
            raise KeyError("Property named '%s' was not found" % name)
        # end handle name not found
        
    def __len__(self):
        """@return amount of child properties"""
        return len(self._descriptor._children)
        
    # -------------------------
    ## @name Interface
    # @{
    
    def property(self, name):
        """@return a property matching the given name
        @param name name of the child property to access
        @throw NoSuchPropertyError"""
        return self.descriptor(name).__get__(self._instance, type(self._instance))
        
    def descriptor(self, name):
        """@return PropertyDescriptor compatible instance which carries the given name
        @throw NoSuchPropertyError"""
        return self._descriptor.descriptor(name)
        
    def descriptor_names(self):
        """@return a list of child property names in order of their creation"""
        return self._descriptor.descriptor_names()
    
    ## -- End Interface -- @}
    
    def delete(self):
        raise AssertionError("Can't delete compound property")
        
    def value(self):
        raise AssertionError("Can't obtain value on compound property")
    
    def set_value(self, value):
        raise AssertionError("Can't set value of compound property")
        
# end class CompoundProperty


## -- End Properties -- @}


# ==============================================================================
## @name Descriptors
# ------------------------------------------------------------------------------
## @{


class PropertyDescriptor(object):
    """A base class for a descriptor representing a Property.
    
    Properties can be anything, and provide their own interface to the user.
    
    @note it is recommended to use one of the provided meta-classes for additional convenience or safety
    @note natively compatible with compound attributes
    @note If a Descriptor is accessed through the class, it returns itself.
    """
    __slots__ = (
                    '_name',          # The name of the property, also the name it is stored in the clsdict
                    '_description',   # A descriptive text about the Property
                    '_weak_parent',   # An optional weak-link to our parent CompoundPropertyDescriptor
                    '__weakref__'    # Allows us to be used as weak reference
                )
    
    NAME_SEPARATOR = '.'
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## The PropertyBase compatible type that is to be instantiated
    ## Must be set by subclass
    PropertyType = None
    
    ## -- End Configuration -- @}
    
    
    def __init__(self, name = None, description = ""):
        """Intialize this instance
        @param name the name which equals the attribute that carries us in our owner class' dict
        If None, it will be set by the PropertyMeta class. It is an error to leave it at None
        @param description A human-readable description about the purpose of the property"""
        self._weak_parent = None
        self._name = name
        self._description = description
    
    # -------------------------
    ## @name Descriptor Interface
    # @{
    
    def __get__(self, inst, cls):
        """@return our property initialized with default attributes
        @param inst instance through which we are accessed, or None
        @param cls always the class that owns us (which is not necessariliy type(inst))
        @note if we are accessed through the class, we always return ourselves"""
        if inst is None:
            return self
        # end handle class access
        
        return self.PropertyType(self, inst)
        
    def __set__(self, inst, value):
        """Set the given value to the instance
        @note called during rhs assignments, and we implement it to use the Property implicitly
        @param inst the instance
        @param value value to set in instance"""
        raise AttributeError("Please use the set_value(value) method instead of an assignment")
        
    def __delete__(self, inst):
        """Delete our property"""
        self.PropertyType(self, inst).delete()
        
    
    ## -- End Descriptor Interface -- @}
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    def name(self):
        """@return the fully qualified descriptor's name
        @note if part of a compound property, nesting will be indicated with the '.' character"""
        assert self._name is not None
        base = ''
        
        if self._weak_parent:
            parent = self._weak_parent
            names = list()
            
            while parent:
                assert parent._name is not None
                names.append(parent._name)
                parent = parent._weak_parent
            # end loop up
            base = self.NAME_SEPARATOR.join(reversed(names)) + self.NAME_SEPARATOR
        # end handle compound properties
        
        return base + self._name
        
    def partial_name(self):
        """@return the shortest possible name, which is not necessarily qualified enough to refer to 
        it's property unambiguously."""
        return self._name
        
        
    def description(self):
        """@return our description"""
        return self._description
    
    ## -- End Interface -- @}


# end class PropertyDescriptor


class CompoundPropertyDescriptor(PropertyDescriptor):
    """A descriptor whhich allows to nest other descriptors"""
    __slots__ = (
                    '_children',    # An iterable of child descriptors, in order
                    '_child_map',   # a mapping of child descriptors to their name: name => PropertyDescriptor
                )
    
    
    PropertyType = CompoundProperty

    def __init__(self, *args, **kwargs):
        """Initialize this instance with all PropertyDescriptor arguments, as well as 
        any amount of PropertyDescriptors that are to be used as Children
        @param args any amount of PropertyDescriptor compatible instances
        @param kwargs all kwargs supported by our super class"""
        super(CompoundPropertyDescriptor, self).__init__(**kwargs)
        cmap = dict() 
        
        # Check our children right away
        for child in args:
            assert isinstance(child, PropertyDescriptor), "Arguments must be PropertyDescriptor instances"
            name = child.partial_name()
            assert name is not None, "Descriptor needs it's name to be set right away"
            assert name not in cmap, "Duplicate property name: %s" % name
            child._weak_parent = weakref.proxy(self)
            cmap[name] = child
        # end handle assertions
        
        self._children = args
        self._child_map = cmap
        
        
    def __getattr__(self, name):
        """@return a child-property with the given name
        @throws AttributeError"""
        try:
            return self.descriptor(name)
        except NoSuchPropertyError:
            raise AttributeError("Property named '%s' was not found" % name)
        # end handle name not found
        
    def __getitem__(self, name):
        """@return a child-property with the given name
        @throws KeyError
        @note useful to simulate dict access"""
        try:
            return self.descriptor(name)
        except NoSuchPropertyError:
            raise KeyError("Property named '%s' was not found" % name)
        # end handle name not found
        
    # -------------------------
    ## @name Interface
    # @{
    
    def descriptor(self, name):
        """@return PropertyDescriptor compatible instance which carries the given name
        @throw NoSuchPropertyError"""
        try:
            return self._child_map[name]
        except KeyError:
            raise NoSuchPropertyError(name)
        # end handle descriptor
        
    def descriptor_names(self):
        """@return a list of child property names in order of their creation"""
        out = list()
        for descriptor in self._children:
            # NOTE: Must be unqualified name !
            out.append(descriptor.partial_name())
        return out
    
    ## -- End Interface -- @}
     
# end class CompoundPropertyDescriptor


## -- End Descriptors -- @}



# ==============================================================================
## @name MetaClasses
# ------------------------------------------------------------------------------
## @{

class PropertyMeta(MetaBase):
    """A metaclass to verify all Property descriptors have their appropriate name
    @note useful for debugging, or to save some typing"""
    __slots__ = ()
    
    @classmethod
    def _resolve_descriptor_names(cls, clsdict):
        """assure all descriptors have their name set"""
        for name, value in clsdict.iteritems():
            if not isinstance(value, PropertyDescriptor):
                continue
            # end ignore non-properties
            
            # Assure it has a value set
            value._name = name
        # end for each name, value pair
    
    def __new__(metacls, name, bases, clsdict):
        """Check the type's properties for validity or set names automatically"""
        metacls._resolve_descriptor_names(clsdict)
        return super(PropertyMeta, metacls).__new__(metacls, name, bases, clsdict)

# end class PropertyMeta


class PropertySchemaMeta(MetaBase):
    """A metaclass to colllect all properties and merge them into a common schema.
    
    It will also resolve all Descriptor names
    Subclasses should specify the exact schema type and may customize the way it it generated.
    
    Generally schemas are the concatenated result of a class and all it's subclasses.
    Classes that whish to use this for their _schema have to set the CLASS_SCHEMA_STORAGE_ATTRIBUTE within
    their own class.
    
    @note We implement an additive merge of all Properties we find in all bases
    @todo Performance Improvement: reuse existing schemas from base types
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## The type we use when instantiating a new dictionary
    ## This becomes the schema itself
    dict_type = dict 
    
    ## Separator for different keys
    KEY_SEPARATOR = PropertyDescriptor.NAME_SEPARATOR
    
    ## Attribute on the class that uses us as MetaClass at which to store the schema
    ## If the class does not have that attribute, it will not be written
    CLASS_SCHEMA_STORAGE_ATTRIBUTE = '_schema_attribute'
    ## -- End Configuration -- @}
    
    @classmethod
    def _resolve_conflict(cls, left, right):
        """@return either the left or right value
        @param cls
        @param left a PropertyDescriptor which was already present
        @param right a new PropertyDescriptor that would override the one already present 
        @note default implementation raises
        Other implementations could merge compound attributes for instance, or allow overrides
        @throws Any may throw any exception to indicate error"""
        raise AssertionError("Property named '%s' does already exist" % left.name())
        
    @classmethod
    def _store_schema(cls, clsdict, bases, attribute, schema):
        """Store the given schema to the right spot in the class dictionary
        @param cls
        @param clsdict dict of yet-to-be-created class
        @param bases
        @param attribute at which to store the schema
        @param schema the Schema as instance of dict_type
        @note can be used to convert the finally stored type into a desired one"""
        clsdict[attribute] = schema
        
    @classmethod
    def _set_schema_value(cls, schema, name, descriptor):
        """Called to set the value at schema[name] to descriptor, or anything derived from it"""
        schema[name] = descriptor
    
    @classmethod
    def _build_schema_recursively(metacls, schema, descriptor):
        """Build a schema recursively
        @param metacls this metaclass
        @param schema a dictionary at the level that would be able to hold the descriptor
        @param descriptor a PropertyDescriptor instance"""
        name = descriptor.partial_name()
        if isinstance(descriptor, CompoundPropertyDescriptor):
            if name in schema:
                descriptor = metacls._resolve_conflict(schema[name], descriptor)
                assert isinstance(descriptor, CompoundPropertyDescriptor), "conflict resolution changed type"
            # end handle conflicts
            schema = schema.setdefault(name, metacls.dict_type())
            for name in descriptor.descriptor_names():
                metacls._build_schema_recursively(schema, descriptor.descriptor(name))
            # end for each name
        else:
            if name in schema:
                descriptor = metacls._resolve_conflict(schema[name], descriptor)
            metacls._set_schema_value(schema, name, descriptor)
        # end handle compounds
        
    def __new__(metacls, name, bases, clsdict):
        """Merge all properties into one dictionary, resolving CompoundAttributes accordingly"""
        # Assure all names are resolved
        PropertyMeta._resolve_descriptor_names(clsdict)
        
        
        storage_attr_value = metacls._class_attribute_value(clsdict, bases, metacls.CLASS_SCHEMA_STORAGE_ATTRIBUTE)
        if storage_attr_value:
            mro_combined = list()
            for base in bases:
                mro_combined.extend(base.mro())
            # end for each base
            
            schema = metacls.dict_type()
            def check_and_build(value):
                if not isinstance(value, PropertyDescriptor):
                    return
                #end skip non-properties
                metacls._build_schema_recursively(schema, value)
            # NOTE: An improved implementation would pick-up existing schema's and just use them, saving 
            # a lot of time for the merge !
            
            # gather all base class properties
            for base in reversed(mro_combined):
                for attr_name, value in base.__dict__.iteritems():
                    check_and_build(value)
                # end for each name, value pair
            # end for each base
            
            # finally process our current ones
            for attr_name, value in clsdict.iteritems():
                check_and_build(value)
            # end for each value in clsdict
            
            metacls._store_schema(clsdict, bases, storage_attr_value, schema)
        else:
            log.debug("Cannot generate schema from properties as %s attribute was not found in clsdict", metacls.CLASS_SCHEMA_STORAGE_ATTRIBUTE)
        #end handle schema
        
        return super(PropertySchemaMeta, metacls).__new__(metacls, name, bases, clsdict)
    
# end class PropertySchemaMeta

## -- End MetaClasses -- @}






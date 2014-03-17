#-*-coding:utf-8-*-
"""
@package bcore.tests.core.test_properties
@brief tests for bcore.core.properties

@copyright 2013 Sebastian Thiel
"""

from bcore.tests import TestCaseBase

# test * import
from bcore.core.properties import *


# ==============================================================================
## @name Utility Types
# ------------------------------------------------------------------------------
## @{

class TestProperty(PrefixProperty):
    __slots__ = ()

# end class TestPropertyDescriptor


class TestPropertyDescriptor(PropertyDescriptor):
    """brief docs"""
    __slots__ = ()

    PropertyType = TestProperty
    

# end class TestPropertyDescriptorDescriptor

## [PrefixPropertyClass]

class PropertyHolder(object):
    """A type which defines some properties"""
    __slots__ = (
                    '_foo',
                    '_bar',
                    '_parent_foo',
                    '_parent_bar',
                    '_parent_sub_foo',
                )
    
    __metaclass__ = PropertySchemaMeta
    _schema_attribute = '_schema'
    
    foo = TestPropertyDescriptor()
    bar = TestPropertyDescriptor(name='bar',
                                 description="bar property")
    
    parent = CompoundPropertyDescriptor(TestPropertyDescriptor(name='foo'), 
                                        TestPropertyDescriptor(name='bar'),
                                        CompoundPropertyDescriptor(
                                            TestPropertyDescriptor(name='foo'),
                                            name='sub'
                                        ))
    
## [PrefixPropertyClass]    

# end class PropertyHolder

## -- End Utility Types -- @}




class TestProperties(TestCaseBase):
    __slots__ = ()
    
    def test_base(self):
        """Test basic properties capabilities"""
        ph = PropertyHolder()
        
        # Properties
        assert isinstance(PropertyHolder.foo, PropertyDescriptor), 'class access returns descriptor itself'
        assert isinstance(ph.foo, TestProperty), 'expected property to be returned'
        assert PropertyHolder.foo.name() == 'foo', 'Name is automatically set'
        assert PropertyHolder.bar.name() == 'bar'
        
        assert not hasattr(ph, '_foo')
        
        ph.foo.set_value(5)
        assert ph.foo.value() == 5
        assert hasattr(ph, '_foo')
        
        # assignment syntax - disabled
        self.failUnlessRaises(AttributeError, setattr, ph, 'foo', 6)
        assert ph.foo.value() == 5
        
        del(ph.foo)
        assert hasattr(ph, 'foo'), "Can't delete actual property"
        assert not hasattr(ph, '_foo'), "Can delete underlying slot"
        
        
        # Compounds
        ############
        assert len(ph.parent.descriptor_names()) == 3
        assert ph.parent.descriptor_names()[0] == 'foo'
        assert isinstance(ph.parent.foo, PropertyBase)
        assert ph.parent.descriptor('foo').name() == 'parent.foo'
        assert ph.parent.sub.descriptor('foo').name() == 'parent.sub.foo', "properties return properties"
        assert PropertyHolder.parent.sub.foo.name() == 'parent.sub.foo', "descriptors always return descriptors"
        assert isinstance(ph.parent['foo'], TestProperty)
        self.failUnlessRaises(AttributeError, getattr, ph.parent, 'baz')
        self.failUnlessRaises(KeyError, ph.parent.__getitem__, 'baz')
        self.failUnlessRaises(NoSuchPropertyError, ph.parent.property, 'baz')
        self.failUnlessRaises(NoSuchPropertyError, ph.parent.descriptor, 'baz')
        self.failUnlessRaises(AttributeError, getattr, PropertyHolder.parent, 'baz')
        self.failUnlessRaises(KeyError, PropertyHolder.parent.__getitem__, 'baz')
        self.failUnlessRaises(NoSuchPropertyError, PropertyHolder.parent.descriptor, 'baz')
        
        ph.parent.foo.set_value(4)
        assert ph.parent.foo.value() == 4
        
        # no setattr support
        self.failUnlessRaises(AttributeError, setattr, ph.parent.sub, 'foo', 5)
        assert not hasattr(ph, '_parent_sub_foo')
        ph.parent.sub.foo.set_value(5)
        assert ph.parent.sub.foo.value() == 5
        assert ph._parent_sub_foo == 5
        
        
        # test schema property !
        assert isinstance(PropertyHolder._schema, dict)
        assert len(PropertyHolder._schema) == 3
        assert len(PropertyHolder._schema['parent']) == 3
        
        # Examples
        ## [PrefixPropertyClass Usage]
        ph = PropertyHolder()
        assert ph.foo.set_value(5).value() == 5
        ph.parent.sub.foo.set_value('hi')
        assert len(ph.parent) == 3
        assert len(ph.parent.sub) == 1
        ## [PrefixPropertyClass Usage]

# end class TestProperties



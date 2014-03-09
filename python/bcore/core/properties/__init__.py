#-*-coding:utf-8-*-
"""
@package tx.core.properties
@brief Properties implementation to improve ease-of-use of KVStore and other frameworks using schema's

@page properties Properties Framework

This framework helps to build arbitrarily complex property definitions and automate their handling. Properties
can be nested arbitrarily.

It is extremely simple and nothing more than a wrap around standard python descriptors, adding a stronger (and
more extensible) interface and some convenience.

@section properties_components Components

Properties are implemented using [python descriptors](http://nbviewer.ipython.org/urls/gist.github.com/ChrisBeaumont/5758381/raw/descriptor_writeup.ipynb),
which in turn return instance of type [PropertyBase](@ref tx.core.properties.base.PropertyBase). The latter
implement a basic get/set interface, which can also respond to deletion (e.g. `del(self.property)`).

As an additional (and optional) layer, there are MetaClasses which facilitate using properties.

+ **Components Summary**
 - **Descriptors**
  - \ref tx.core.properties.base.PropertyDescriptor "PropertyDescriptor"
   - A basic property with meta-data support
  - \ref tx.core.properties.base.CompoundPropertyDescriptor "CompoundPropertyDescriptor"
   - A Descriptor that can contain other descriptors, useful for nesting of properties
 - **Properties**
  + \ref tx.core.properties.base.PropertyBase "PropertyBase"
   - A simple utility type returned when the descriptor is accessed. It is meant to be subclassed
     for an actual implementation of how to retrieve or set a value.
  + \ref tx.core.properties.base.CompoundProperty "CompoundProperty"
   - Utility returned by CompoundPropertyDescriptor to return child properties accordingly
 - **Meta Classes**
  + \ref tx.core.properties.base.PropertyMeta "PropertyMeta"
   - Basic meta-class to auto-name PropertyDescriptor instances based on their field in the class dict
  + \ref tx.core.properties.base.PropertySchemaMeta "PropertySchemaMeta"
   - A MetaClass with similar functionality as PropertyMeta, which additionally gathers all Descriptors
     into a separate dictionary which serves as easily parseable schema.
 
@section properties_examples Examples

In the first example, a \ref tx.core.properties.types.PrefixProperty "PrefixProperty" is used to formalize
accessing the classes member variables. For safety and efficiency, they are put into slots. However, technique
works similarly without slots as well.

@snippet bcore/tests/core/test_properties.py PrefixPropertyClass

This is how properties can be accessed.

@snippet bcore/tests/core/test_properties.py PrefixPropertyClass Usage

The next example uses the specialization for EnvironmentContextClients.

@snippet bcore/tests/core/component/test_properties.py ExampleContextClient

When using the properties, access was simplified to be more the way the kvstore is supposed to be used. Also note 
the direct property access, as opposed to using property access methods.

@snippet bcore/tests/core/component/test_properties.py ExampleContextClient Usage

@copyright 2013 Sebastian Thiel
"""

from .base import *
from .types import *

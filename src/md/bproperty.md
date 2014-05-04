![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)

This framework helps to build arbitrarily complex property definitions and automate their handling. Properties can be nested arbitrarily.

It is extremely simple and nothing more than a wrap around standard python descriptors, adding a stronger (and more extensible) interface and some convenience.

Components
==========

Properties are implemented using [python descriptors](http://nbviewer.ipython.org/urls/gist.github.com/ChrisBeaumont/5758381/raw/descriptor_writeup.ipynb),
which in turn return instance of type [PropertyBase](@ref butility.properties.base.PropertyBase). The latter
implement a basic get/set interface, which can also respond to deletion (e.g. `del(self.property)`).

As an additional (and optional) layer, there are MetaClasses which facilitate using properties.

Components Summary
------------------

- **Descriptors**
    - \ref butility.properties.base.PropertyDescriptor "PropertyDescriptor"
        - A basic property with meta-data support
    - \ref butility.properties.base.CompoundPropertyDescriptor "CompoundPropertyDescriptor"
        - A Descriptor that can contain other descriptors, useful for nesting of properties
- **Properties**
    + \ref butility.properties.base.PropertyBase "PropertyBase"
        - A simple utility type returned when the descriptor is accessed. It is meant to be subclassed for an actual implementation of how to retrieve or set a value.
    + \ref butility.properties.base.CompoundProperty "CompoundProperty"
        - Utility returned by CompoundPropertyDescriptor to return child properties accordingly
 - **Meta Classes**
    + \ref butility.properties.base.PropertyMeta "PropertyMeta"
        - Basic meta-class to auto-name PropertyDescriptor instances based on their field in the class dict
    + \ref butility.properties.base.PropertySchemaMeta "PropertySchemaMeta"
        - A MetaClass with similar functionality as PropertyMeta, which additionally gathers all Descriptors into a separate dictionary which serves as easily parseable schema.
 
Examples
========

In the first example, a \ref butility.properties.types.PrefixProperty "PrefixProperty" is used to formalize accessing the classes member variables. For safety and efficiency, they are put into slots. However, technique works similarly without slots as well.

@snippet bapp/tests/core/test_properties.py PrefixPropertyClass

This is how properties can be accessed.

@snippet bapp/tests/core/test_properties.py PrefixPropertyClass Usage

The next example uses the specialization for EnvironmentContextClients.

@snippet bapp/tests/core/component/test_properties.py ExampleContextClient

When using the properties, access was simplified to be more the way the kvstore is supposed to be used. Also note the direct property access, as opposed to using property access methods.

@snippet bapp/tests/core/component/test_properties.py ExampleContextClient Usage

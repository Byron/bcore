#-*-coding:utf-8-*-
"""
@package bsemantic.base
@brief Contains base classes specifying and implementing the substitution system.

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str


from butility.future import with_metaclass
import sys

__all__ = ['ElementNode', 'ElementNodeList', 'ElementNodeTree', 'ValidatedElementNode']


from butility import (Meta,
                      DictObject,
                      LazyMixin,
                      string_types)

from bkvstore import (RelaxedKeyValueStoreProviderDiffDelegate,
                      KeyValueStoreProvider)
from .exceptions import InvalidValueError


# ==============================================================================
# @name Utilities
# ------------------------------------------------------------------------------
# @{

class RelaxedKeyValueStoreProvider(KeyValueStoreProvider):

    """A key value store with relaxed semantics"""
    __slots__ = ()

    DiffProviderDelegateType = RelaxedKeyValueStoreProviderDiffDelegate

# end class RelaxedKeyValueStoreProviderKeyValueStoreProvider


def to_tuple(val):
    """@return tuple of val
    if val is None, the tuple will be empty. If val is a tuple, return it. Convert list types to a tuple.
    All other types will be returned as first argument
    """
    if isinstance(val, tuple):
        return val
    if val is None:
        return tuple()
    if isinstance(val, (list, set)):
        return tuple(val)
    return (val,)


class ValidatedElementNodeMetaClass(Meta):

    """Provides dynamic compile-time features for the VerifiedElementNode"""
    __slots__ = ()
    _attr_name_schema = '_schema_'
    _attr_name_slots = '__slots__'

    def __new__(mcs, name, bases, clsdict):
        """Process metadata and generate the type respectively"""
        schema = clsdict.get(mcs._attr_name_schema, list())
        slots = clsdict.get(mcs._attr_name_slots, list())

        if isinstance(slots, tuple):
            slots = list(slots)
        elif isinstance(slots, string_types):
            slots = [slots]
        # end convert slots to list

        if isinstance(schema, tuple):
            schema = list(schema)

        # next, behave similar to slots, such that we will find all _schema_ specifications and put them into
        # our own _schema_ - we find schemas horizontally and vertically.
        schema_attrs = set(pair[0] for pair in schema)

        def add_schema_from(cls):
            """concatenate schemas into one datastructure"""
            # allow overrides - therefore the base classes must not override anything that's already contained
            cls_schema = cls.__dict__.get(mcs._attr_name_schema, tuple())
            for attr, default in cls_schema:
                if attr in schema_attrs:
                    continue
                schema.append((attr, default))
                schema_attrs.add(attr)
            # end for each attribute in cls schema
        # end handle schema concatenation

        def add_schema_recursive(cls):
            """recursively use add_schema_from"""
            add_schema_from(cls)
            for base in cls.__bases__:
                add_schema_recursive(base)
            # end for each base
        # end add_schema_recursive

        for base in bases:
            add_schema_recursive(base)
        # end for each base to add recursively

        # make slots for each schema attribute
        for attr, _ in schema:
            if attr not in slots:
                slots.append(attr)
            # end prevent duplicate additions
        # end for each attribute to add as slot

        # update the changed attributes
        clsdict[mcs._attr_name_slots] = tuple(slots)
        clsdict[mcs._attr_name_schema] = tuple(schema)

        return Meta.__new__(mcs, name, bases, clsdict)

# end class ValidatedElementNodeMetaClass

# -- End Utilities -- @}

# W0613 unused argument - we don't actually need them, but they are good as context for others
# pylint: disable-msg=W0613

# ==============================================================================
# @name Base Types
# ------------------------------------------------------------------------------
# @{


class ElementNode(LazyMixin):

    """Represents an element of a name, which carries meta-data to drive algorithms.

    An ElementNode is organized in a tree, which links from parents to its children only.
    This tree represents all possible names that can be created, in a static fashion.

    ElementNodes provide meta-data about the node, which can be used by algorithms to determine how to 
    actually build a name.

    You can access the separator character(s) to the parent using the child_separator member.

    @note Access to the data in this node is generally read-only
    @attention this type relies on external information, and it trusts its source. The provider of the data 
    should verify it, or use our own verification through the `validate()` method.
    """
    __slots__ = (
        # public slots
        'child_separator',  # per-instance override, by default unset, lazily populated
        # private slots
        '_key',             # fully qualified key,
        '_name',            # the node's name
        '_data',            # static set of data, including meta-data

        # cached values
        '_meta_data',       # a static set of meta-data
    )

    # -------------------------
    # @name Constants
    # @{

    # the default separator to be used to separate the previous element
    # There may be an instance level override
    default_child_separator = '/'
    # separator for hierarchy levels in key, like root.subitem.meta
    key_separator = '.'
    # attribute in our data which carries the metadata
    attr_metadata = 'meta'
    # attribute of meta-data that contains our tags
    attr_type = 'type'

    # NOTE: currently we don't have a schema definition language strong enough to allow us to
    # formally declare it

    # -- End Constants -- @}

    def __init__(self, key, name, data):
        """Initialize this instance with a given set of data.

        @param key: the fully qualified key at which this node is posistioned in the original input data.
        It must use `key_separator` separate its levels of hierarchy, like 'root.sublevel.leaf'
        @param name: the name of this node, its plain and not fully qualified.
        @param data: dictionary with key-value pairs obtained at `key`, representing our data. 
        It may be nested and contain this node's children as well.
        It may also be a list or tuple, in which case the entry of the list must be a string which is 
        interpreted as  name of a node without any values.
        We are allowed to perform transformations only on copies of it, or extract parts of it accordingly.
        """
        super(ElementNode, self).__init__()
        self._key = key
        self._name = name
        if isinstance(data, (tuple, list)):
            data_dict = dict()
            for item in data:
                assert isinstance(item, string_types), "invalid item type: %s" % type(item)
                # emulate empty items more directly. This conversion makes code further down
                # easier as it can assume a dictionary
                data_dict[item] = dict()
            # end for each item
            data = data_dict
        # end handle conversion
        assert isinstance(data, dict), "require a data dictionary by that point"
        self._data = data

    def _set_cache_(self, attr):
        """Update our cached attributes"""
        if attr == '_meta_data':
            try:
                # we don't do a deep-copy here
                self._meta_data = self._data[self.attr_metadata]
            except KeyError:
                self._meta_data = dict()
            # end handle meta data exists
        elif attr == 'child_separator':
            self.child_separator = self._meta_data.get('child_separator', self.default_child_separator)
        else:
            return super(ElementNode, self)._set_cache_(attr)
        # end attr == self.attr_metadata

    def _to_fq_key(self, *keys):
        """Append one or more key elements to the fully qualified key of this instance
        @return a new fully qualified key"""
        assert keys
        return self.key() + self.key_separator + self.key_separator.join(keys)

    def _to_fq_meta_key(self, *keys):
        """Similar as _to_fq_key, but it will insert the meta key in fron of *keys"""
        return self._to_fq_key(self.attr_metadata, *keys)

    # -------------------------
    # @name Subclass Interface
    # @{

    def _child_type(self, child_key, data):
        """@return the type of this instance
        @param child_key the name of the child, being the key of the child's data in our data dict
        @param data a dictionary with the child's data, or a list of child names (i.e. the childs children)
        @note defaults to the actual type, subclasses may use it to identify the type by other means"""
        return type(self)

    # -- End Subclass Interface -- @}

    # -------------------------
    # @name Interface
    # @{

    def key(self):
        """@return fully qualified key of this instance, which indicates the position of our node within
        the hierarchy of the original source data"""
        return self._key

    def name(self):
        """@return the name of this instance"""
        return self._name

    def children(self):
        """@return a list of ElementNode instances which represent our children.
        May be empty if this is a leaf node"""
        out = list()
        for key, value in self._data.items():
            if key == self.attr_metadata:
                continue
            # end skip metadata
            out.append(self._child_type(key, value)(self._to_fq_key(key), key, value))
        # end for each child
        return out

    def is_leaf(self):
        """@return True if we have children, False otherwise."""
        # everything except the meta-data key is a child
        # We don't necessarily have a meta-data key
        this_size = 0
        if self.attr_metadata in self._data:
            this_size = 1

        return len(self._data) == this_size

    def data(self):
        """@return a DictObject with our actual data. This is the most direct and unchecked interface to the
        node's meta-data, that should only be used if you expect to see custom values which are not supported
        by the base-interface.
        May be empty if there is no meta-data.
        @note the data is a copy of our actual data set, and thus cannot affect us."""
        return DictObject(self._meta_data).clone()

    def type(self):
        """@return a tuple of strings that represent the type of this instance. It can be seen a set of tags, or 
        a flattened inheritance hierarchy, and can be interpreted at will.
        It may be empty, as nodes don't have to specify a type
        """
        return to_tuple(self._meta_data.get(self.attr_type, None))

    def validate(self, index):
        """Run basic validation and put information about it into the given index dictionary
        @param index dictionary whose keys will be fully qualified keys about the location of the data entry
        that was invalid, as well as a string description about the issue
        @return this instance"""
        if not self._meta_data:
            index[self._to_fq_meta_key()] = "no meta data found"
        if not self.type():
            index[self._to_fq_meta_key(self.attr_type)] = "Type was empty or unset"
        return self
    # -- End Interface -- @}

# end class ElementNode


class ValidatedElementNode(with_metaclass(ValidatedElementNodeMetaClass, ElementNode)):

    """An ElementNode implementation which allows direct, attribute access against a simple, flat, schema.

    Even though the base implementation is able to provide simple type checking, we make additional calls to our 
    subclass to further validate a value.

    We extend `validation()` to record if there is a schema mismatch, and help determining errors in the provided
    data.

    Each validated member will be stored in a slot to prevent validation on each subsequent access. Its retrieved
    from the underlying meta-data

    Subclass Documentation
    #######################
    Subclasses specify a class member serving as database for read-only properties which are created automatically.
    Accessing these is fully type-checked.

    Your subclass might look like this:
    @snippet bsemantic/tests/test_base.py verified_element_node

    Whereas the usage of your instance could look like that:
    @snippet bsemantic/tests/test_base.py verified_element_node_usage

    Advanced Features
    ##################
    You can have mixin types which define a schema on their own, but don't derive from `ValidatedElementNode`.
    Their attributes will be made available by your class, which allows their implementation to use the required
    attributes and to validate themselves accordingly.

    Extensions
    ##########

    Its possible to extend the name handling system in various ways. The following example shows how to
    dynamically instantiate your own types, while using the default iterators.

    @snippet bsemantic/tests/test_inference.py name-handling-extension
    """
    __slots__ = ()

    # Your subclass provides a tuple of pairs, where the first value is the name of the designated property,
    # and the second one is its designated type or default value.
    # See the class documentation for additional details
    _schema_ = tuple()

    def _obtain_meta_data_for(self, key):
        """@return our meta-data dictionary (possibly) containing the given key"""
        return self._meta_data

    def _set_cache_(self, attr):
        """Validate and set our property"""
        for schema_attr_name, default in self._schema_:
            if schema_attr_name == attr:
                value = self._validated_property(attr, self._obtain_meta_data_for(attr).get(attr, None), default)
                setattr(self, attr, value)
                return
            # end name matches
        # end for each schema pair
        return super(ValidatedElementNode, self)._set_cache_(attr)

    def _validated_property(self, attr_name, value, default):
        """Called to assure the given attribute  with name `attr_name` is valid according to the `default` value
        @param attr_name a string identifying the attribute's name
        @param value the actual value we obtained from our meta data dictionary. May be None to indicate
        there was no such entry
        @param default either a type or an instance which is provides information about the desired value
        @return a verified and valid value for the given attribute"""
        if value is None and not isinstance(default, type):
            if default is None:
                raise InvalidValueError(self._to_fq_meta_key(attr_name), "default value was None")
            # use default (which is assumed to be valid)
            value = default
        else:
            # call subclass, it can validate the entire value, no matter what
            value = self._to_valid_value(attr_name, value, default)
        # end handle default
        return value

    # -------------------------
    # @name Subclass Interface
    # @{

    def _to_valid_value(self, attr_name, value, default):
        """@return a valid value for the value at the given attribute `attr_name`.
        It is called if `value` is None or if its type has to be checked against the default.
        @param attr_name see _validated_property()
        @param value the value from an untrusted source. Maybe None if it didn't exist in the source data.
        Otherwise it is some value, which should be checked against the default.
        @param default see _validated_property()
        @throws InvalidValueError in case the value could not be handled
        @note the base implementation just tries to convert the value to the default value's type
        """
        default_type = isinstance(default, type) and default or type(default)
        try:
            return default_type(value)
        except Exception:
            msg = "Failed to convert value '%s' to type '%s'" % (value, default_type)
            raise InvalidValueError(self._to_fq_meta_key(attr_name), msg)
        # end handle exceptions
        try:
            return super(ValidatedElementNode, self)._to_valid_value(attr_name, value, default)
        except AttributeError:
            return self
        # end implement mixin support

    # -- End Subclass Interface -- @}

    def validate(self, index):
        """Tries to obtain valid values and registers InvalidValueError in the index
        @note should run on a Node which was just created, and therefore has no cached values yet"""
        super(ValidatedElementNode, self).validate(index)
        for attr, _ in self._schema_:
            try:
                getattr(self, attr)
            except InvalidValueError as err:
                index[err.key] = err.annotation
            # end handle exception
        # end for each attribute
        return self


# end class VerifiedElementNode


class ElementNodeList(list):

    """Represents a list of ElementNode instances which provides additional support for transformation and analysis.

    @note this type is mainly required for convenience
    """
    __slots__ = ()

    def __str__(self):
        """@return ourselves as list of element names, separated with the actual separator"""
        out = str()
        if self:
            for index in range(len(self) - 1):
                elm = self[index]
                out += elm.name() + elm.child_separator
            # end for each node
            out += self[-1].name()
        # end if we have at least an item
        return out

    # -------------------------
    # @name Interface
    # documentation
    # @{

    def clone(self):
        """@return a shallow copy of this instance, thus it will only be the list which is cloned. The actual
        nodes will be referenced, and changes to a node will affect all other clones of this list that use it."""
        return type(self)(self)

    def find_first_if(self, predicate):
        """@return the first ElementNode for which the predicate returns True, or None if no one matched
        @param predicate (bool)fun(node) a function taking a `node` returning a bool
        """
        for elm in self:
            if predicate(elm):
                return elm
        # end for each elm
        return None

    def is_leaf(self):
        """@return True if our last ElementNode doesn't have children"""
        assert self, "list must not be empty"
        return self[-1].is_leaf()

    # -- End Interface -- @}

# end class ElementNodeList


class ElementNodeTree(object):

    """Is a tree of Nodes which provides utilities to work with those elements."""
    __slots__ = (
        '_root_node'  # The root of all elements
    )

    # -------------------------
    # @name Configuration
    # @{

    # The ElementNodeList compatible type we will instatiate
    ElementNodeListType = ElementNodeList
    skip_root_node = True

    # -- End Configuration -- @}

    def __init__(self, root_node):
        """Initialize this instance with a root node
        @param root_node an ElementNode instance which ideally contains children
        It will be used as the starting point for the tree iteration, and its type 
        will be used to instantiate new nodes (by default)
        """
        assert isinstance(root_node, ElementNode), "Require an ElementNode, got '%s'" % type(root_node)
        self._root_node = root_node

    # -------------------------
    # @name Interface
    # @{

    def _iter_at(self, node_list, predicate=None, prune=None):
        """@return an iterator at the given node"""
        node = node_list[-1]

        # breadth first - return all children first
        children = node.children()
        for child in children:
            node_list.append(child)
            try:
                if predicate is None or predicate(node_list):
                    yield node_list
                # end yield if allowed
            finally:
                node_list.pop()
            # end assure parent list is popped
        # end for each child

        # now go down one level
        for child in children:
            node_list.append(child)
            try:
                if prune is not None and prune(node_list):
                    continue
                # end handle prune
                for other_node in self._iter_at(node_list, predicate=predicate, prune=prune):
                    yield other_node
                # end for each yielded node
            finally:
                node_list.pop()
            # end assure parent list is popped
        # end for each child

    def __iter__(self):
        """@return an iterator yielding ElementNodeList instances of our element tree, iterated **breadth-first**
        @attention If you intend to alter the returned ElementNodeList, you must call the `clone()` mehtod beforehand.
        Otherwise you might affect the iteration"""
        return self.iterate()

    def iterate(self, predicate=None, prune=None):
        """@return iterator which will return only those ElementNodeList instances for which predicate returns true.
        It will return the root of the tree.
        @param predicate (bool) fun(element_node_list) a function returning True for each ElementNodeList to yield.
        Please note that even if it returns False, the iterator will descent into lower levels of the tree.
        That means, the predicate comes first, the 
        If the predicate is None, all ElementNodeLists will be returned
        @param prune (bool) fun(element_node_list) a function returning True if the subtree of the given element 
        list should be pruned, i.e. not handled. This allows you to stop recursing into deeper tree levels.
        If None, there will be no pruning"""
        nlist_base = self.ElementNodeListType()
        nlist_base.append(self.root_node())

        if predicate is None or predicate(nlist_base):
            yield nlist_base

        if prune is not None and prune(nlist_base):
            raise StopIteration

        for nlist in self._iter_at(nlist_base, predicate=predicate, prune=prune):
            yield nlist.clone()
        # end for each node list

    @classmethod
    def new(cls, root_key, data, element_node_type):
        """@return a new instance of this type, given just a `root_key` to obtain the first level from `data`
        @param root_key key in into the data-dictionary at which its data can be found. It may not be nested.
        @param data a dictionary instance which contains `root_key`
        @param element_node_type the type of the ElementNode you would like to create
        @param cls
        """
        return cls(element_node_type(root_key, root_key, data[root_key]))

    def root_node(self):
        """@return the tree's root node"""
        return self._root_node

    def validate(self, index):
        """Validate each ElementNode in the tree and write the results into the index
        @param index a dictionary receiving fully qualified keys, with their values being message strings for 
        further information about the issue.
        @return this instance
        @note See the ElementNode type's `validate()` method for more details.
        """
        elm_set = set()
        for nlist in self:
            for elm in nlist:
                if elm in elm_set:
                    continue
                # end skip seen items
                elm_set.add(elm)
                elm.validate(index)
            # end for each element in nlist
        # end for each node list in tree
        return self
    # -- End Interface -- @}


# end class ElementNodeTree

# RuleSetIterator

# -- End Base Types -- @}

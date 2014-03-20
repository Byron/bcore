#-*-coding:utf-8-*-
"""
@package bkvstore.persistence
@brief Contains tools related to persisting objects - currently yaml only

@note I'd like to have named this module 'yaml', but this will prevent any imports
from the actual yaml package from within this package
@copyright 2012 Sebastian Thiel
"""
__all__ = ['OrderedDictYAMLLoader']

import yaml.constructor
import yaml.representer

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
# end get fastest loader

from butility import ( OrderedDict,
                       DictObject )

# ==============================================================================
## \name Yaml Tools
# ------------------------------------------------------------------------------
# Yaml specific tools and overrides
## \{


def initialize_yaml_overrides():
    """Initialize our yaml overrides and customizations.
    They are non-invasive as such as all other yaml will not be influenced by it

    Add our representer which just assures that ordered dicts are never
    displayed as custom types, but just as dicts. This will make the files
    we write much prettier.
    """
    yaml.add_representer(OrderedDict, represent_ordereddict)
    yaml.add_representer(DictObject, represent_dictobject)


class OrderedDictYAMLLoader(Loader):
    """ A YAML loader that loads mappings into ordered dictionaries.

    It is required to assure that iterating keys during serialization and
    deserialization will not change the order of the keys.
    Otherwise it would be confusing as files being written back unchanged
    will result in a different file with a mostly unpredictable order.

    @note based on https://gist.github.com/844388
    """

    def construct_object(self, node, deep=False):
        """Overridden to assure we use our overridden method before using
        trying the plug-in types"""
        if node in self.constructed_objects:
            return self.constructed_objects[node]
        if deep:
            old_deep = self.deep_construct
            self.deep_construct = True
        if node in self.recursive_objects:
            raise yaml.constructor.ConstructorError(None, None,
                    "found unconstructable recursive node", node.start_mark)
        self.recursive_objects[node] = None
        constructor = None
        tag_suffix = None

        # prefer our own mapping override - don't use plugin types for this!
        if isinstance(node, yaml.MappingNode):
            constructor = self.__class__.construct_mapping
        elif node.tag in self.yaml_constructors:
            constructor = self.yaml_constructors[node.tag]
        else:
            for tag_prefix in self.yaml_multi_constructors:
                if node.tag.startswith(tag_prefix):
                    tag_suffix = node.tag[len(tag_prefix):]
                    constructor = self.yaml_multi_constructors[tag_prefix]
                    break
            else:
                if None in self.yaml_multi_constructors:
                    tag_suffix = node.tag
                    constructor = self.yaml_multi_constructors[None]
                elif None in self.yaml_constructors:
                    constructor = self.yaml_constructors[None]
                elif isinstance(node, yaml.ScalarNode):
                    constructor = self.__class__.construct_scalar
                elif isinstance(node, yaml.SequenceNode):
                    constructor = self.__class__.construct_sequence
                elif isinstance(node, yaml.MappingNode):
                    constructor = self.__class__.construct_mapping
        if tag_suffix is None:
            data = constructor(self, node)
        else:
            data = constructor(self, tag_suffix, node)
        if hasattr(data, 'next'):
            generator = data
            data = generator.next()
            if self.deep_construct:
                for dummy in generator:
                    pass
            else:
                self.state_generators.append(generator)
        self.constructed_objects[node] = data
        del self.recursive_objects[node]
        if deep:
            self.deep_construct = old_deep
        return data


    def construct_mapping(self, node, deep=False):
        """Called preferably - all we do is use an ordered dict. Unfortunately
        the dict type is nothing we could easily override"""
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)
            #end
        #end is node a mapping node

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc,
                                        key_node.start_mark)
                #end raise other exception
            #end try hash(key)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        #end for each key_node, value_node in node.value
        return mapping
        
    # Support for older yaml versions - this is required to make it work
    # For some reason, it pulls another version of yaml in which is missing this method
    if not hasattr(Loader, 'dispose'):
        def dispose(self):
            """noop
            @todo remove this """
            pass


class OrderedDictRepresenter(yaml.representer.Representer):
    """Provide a standard-dict representation for ordered dicts as well.
    This assumes that we are automatically serializing into ordered dicts"""

    @classmethod
    def represent_ordered_mapping(cls, dumper, tag, mapping, flow_style=None):
        """Same as BaseRepresenter.represent_mapping, except that it skips sorting"""
        value = list()
        node = yaml.MappingNode(tag, value, flow_style=flow_style)
        if dumper.alias_key is not None:
            dumper.represented_objects[dumper.alias_key] = node
        best_style = True

        for item_key, item_value in mapping.iteritems():
            node_key = dumper.represent_data(item_key)
            node_value = dumper.represent_data(item_value)
            if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
                best_style = False
            if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
                best_style = False
            value.append((node_key, node_value))
        if flow_style is None:
            if dumper.default_flow_style is not None:
                node.flow_style = dumper.default_flow_style
            else:
                node.flow_style = best_style
        return node
    #end represent_ordered_mapping
# end class OrderedDictRepresenter

def represent_dictobject(dumper, data):
    return yaml.representer.Representer.represent_mapping(dumper,
                                                u'tag:yaml.org,2002:map', data)

def represent_ordereddict(dumper, data):
    """Represents and ordered dict like a dict
    @note: what's usually self is a dumper, which is not an instance of our
    type though. Therefore we explicitly call our code through a classmethod."""
    return OrderedDictRepresenter.represent_ordered_mapping(dumper,
                                                u'tag:yaml.org,2002:map', data)

## -- End Yaml Tools -- \}

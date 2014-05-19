#-*-coding:utf-8-*-
"""
@package bkvstore.persistence
@brief Contains tools related to persisting objects - currently yaml only

@note I'd like to have named this module 'yaml', but this will prevent any imports
from the actual yaml package from within this package
@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['OrderedDictYAMLLoader']

import yaml
import yaml.constructor

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
    """
    A YAML loader that loads mappings into ordered dictionaries.
    """
 
    def __init__(self, *args, **kwargs):
        Loader.__init__(self, *args, **kwargs)
 
        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)
 
    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)
 
    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)
 
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


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

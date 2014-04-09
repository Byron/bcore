#-*-coding:utf-8-*-
"""
@package bsemanticgenerators
@brief Module with generators for names of many kinds

Generators are commonly provided as small base implementations which can be used as mixins.

@copyright 2012 Sebastian Thiel
"""
__all__ = ['StringFormatNode', 'StringFormatNodeTree', 'StringFormatNodeList']

import re


from .base import (
                        ValidatedElementNodeBase,
                        ElementNodeTree,
                        ElementNodeList,
                        RelaxedKeyValueStoreProvider
                   )
from .exceptions import MissingFormatResultError
from bkvstore import (
                                UnorderedKeyValueStoreModifier,
                                KeyValueStoreProvider
                            )
from bapp.utility import DictObject

import bapp.core.logging


# ==============================================================================
## @name Generator Nodes
# ------------------------------------------------------------------------------
# Mixins for nodes that add very specific functionality
## @{

# R0201 Method could be a function, but we want it to be overridable
# pylint: disable-msg=R0201
    
class StringFormatNode(ValidatedElementNodeBase):
    """A node that substitutes a string with data usually provided as DictObject.
    
    Valid formats are those supported by the `format()` method of a string. However, we only support named 
    substitutions.
    @verbatim
    {project.name}.{ext}
    @endverbatim
    
    As you can imagine, its vital that sufficient data is provided.
    
    The result of any substitution is stored in the `format_result` field of each instance, which may be None
    if there was not enough data provided.
    
    If the format doesn't exist or is empty, it will default to the name of the node.
    @note currently validation is not supported
    """
    # NOTE: slots don't work with mixins, this really just a bug if you ask me 
    # However, there is no way around it except for having a dict, or using single inheritance only
    __slots__ = (
                    # public slots
                    'format_result',                # None or the string as result of the formatting operation
                    '_format_data',        # a key-value provider with the data used for formatting
                )
    
    _schema_ =  (
                    ('format', ''),      # a format string used as template for substitution
                )
    
    ## a regex to find compound fields, like {hello:03d} or {hello.world}, or {foo.baz.bar}
    re_compound_fields = re.compile(r'\{(\w+(?:\.\w+)*).*?\}')
    
    ## We use a log just to be sure we don't loose inforation
    log = bapp.core.logging.module_logger('bsemanticgenerators')
    
    def __init__(self, *args, **kwargs):
        super(StringFormatNode, self).__init__(*args, **kwargs)
        self.format_result = None
        self._format_data = dict()
    
    def _resolve_attribute(self, instance, attribute_name):
        """Try to query all attributes as indicated by the attribute name of the instance
        @param instance an object with getattr support
        @param attribute_name a simple attribute name, whose sub-attributes may be separated by a '.' character,
        i.e. 'attr' or 'attr.subattr'
        @return 
        """
        attrs = attribute_name.split('.')
        for attr in attrs:
            instance = getattr(instance, attr, None)
            if instance is None:
                # attr did not exist on instance, or was None (which happens in DictObjects which nicely
                # return nil values, similar to their java script counterparts
                return False
            #end handle non-existing attributes
        #end for each attribute
        return True
    
    # -------------------------
    ## @name Subclass Interface
    ## Subclasses may override these methods to alter the hehaviour, for instance, to pre-adjust the format
    ## or manipulate the data the format uses for substitution.
    # @{
        
    def _has_required_keys(self, data):
        """Assure that the data dictionary contains all keys that our  format requires
        @return True if we have all required data keys, False otherwise
        """
        for key in self.format_keys():
            tokens = key.split('.', 1)
            instance_name = tokens[0]
            attr = len(tokens) == 2 and tokens[1] or None 
            if tokens[0] not in data:
                return False
            #end handle missing instance
            if attr is not None and not self._resolve_attribute(data[instance_name], attr):
                return False
            #end for each 
        #end fore each format key
        return True
    
    def _apply_format(self, data, index=None):
        """@return a string which is the result of the substitution
        @param data see the `format()` method
        @param index a dict that will be used similarly to the `validate()` method of the `ValidatedElementNodeBase`
        to track format errors (which can only be cought when actually applying the format).
        If None, these issues will not be recorded.
        @return a new string with all substitutions applied successfully, or None string if there was insufficient data
        or if we didn't have the format attribute.
        And a (nested) data dictionary instance which contains all the data strings actually used. It will be empty
        if there was no format.
        """
        # determine if all named fields are actually available in data
        invalid = (None, dict())
        if not self._has_required_keys(data):
            return invalid
        #end
        msg = None
        try:
            assert self.format_string(), "node '%s': Format should not be empty" % self.key()
            res = self.format_string().format(**data)
            
            # still here ? Store the data we actually used
            kvmod = UnorderedKeyValueStoreModifier(dict())
            kvprovider = RelaxedKeyValueStoreProvider(DictObject(data).to_dict(recursive=True))
            for key in self.format_keys():
                kvmod.set_value(key, kvprovider.value(key, dict()))
            #end for each key
            
            return res, kvmod.data()
        except KeyError:
            # apparently, someone used an alternate form, otherwise the _has_required_keys would have cought this
            msg = "Use the dot-separated form to access members, not the dict one, in format '%s'" % self.format_string()
            self.log.error(msg, exc_info=True)
        except Exception:
            # catch all - this is a serious issue though
            msg = "Failed to apply format '%s'" % self.format_string()
            self.log.error(msg, exc_info=True)
        #end handle insufficient data for format
        if msg and index:
            index[self._to_fq_meta_key('format')] = msg
        #end keep track of issues
        return invalid
        
    ## -- End Subclass Interface -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def apply_format(self, data):
        """Apply our format using the given data. Write the result into our `format_result` member, which is a 
        substituted string or None on failure.
        The substitution will fail if the format could not be consumed completely.
        @param data a dictionary like object whose keys are names of objects which (possibly) support getattr
        to obtain attributes. It may also be a KeyValueStoreProvider instance, which will just have its data
        converted to the required type beforehand.
        @return this instance
        """
        if isinstance(data, KeyValueStoreProvider):
            data = DictObject(data.data())
        #end check data type
        self.format_result, self._format_data = self._apply_format(data)
        return self
        
    def format_string(self):
        """@return the format string to use. By default, this is the value of our `format` member"""
        return self.format or self.name()
        
    def format_keys(self):
        """@return list of strings that indicate which attributes are accessed by the format.
        e.g. ['project.name', 'ext']. It is possible that strings are returned multiple times, as they can be
        mentioned multiple times in the format as well. They will be returned in their order of appearance
        in the format string"""
        return list(match.group(1) for match in self.re_compound_fields.finditer(self.format_string()))
        
    def format_data(self):
        """@return a (nested) dictionary instance with the data used to substitute into the format string
        @note the data will be empty if `format_result` is None
        @note use the `format_keys() method to query the keys that are present in the data dictionary. 
        You may use an UnorderedKeyValueStoreModifier to conveniently change values using nested keys, and pass 
        it back to the apply_format method to change the substitution result, and the respective values
        returned by this method."""
        return self._format_data
        
    ## -- End Interface -- @}
    
# end class StringFormatNode


class StringFormatNodeList(ElementNodeList):
    """A list which supports string generation by concatenating multiple nodes into one.
    
    The substitution operation is handled in two steps:
    
    - Substitute data into the nodes of this list - the result is stored within the node
    - Concatenate the results into one string.
    
    In order to obtain a valid string, all Nodes must have succeeded in their substitution. 
    This should automatically be the case if the data is as rich as the data used to obtain
    this list by iterating the respective `StringFormatNodeTree`.
    """
    __slots__ = ()

    # -------------------------
    ## @name Interface
    # @{
    
    def apply_format(self, data):
        """Format all `StringFormatNode` instance in this list with the given data set
        @note usually all nodes in this list are already formatted when this list is obtained, as its part
        of the iteration. If you want to substitute a different data set, this method should be called for
        convenience though.
        @param data a dictionary-like object whose keys are names of objects which usually support the
        getattr.
        @return this instance"""
        for node in self:
            node.apply_format(data)
        #end for each node
        return self
        
    def to_string(self):
        """Concatenate the previous substitution result of all Nodes using their separation character and 
        return it as string.
        @return a string
        @throws MissingFormatResultError if a node was missing its formatted result."""
        out = str()
        if not self:
            return out
        #end bail out if empty
        
        # add the remaining ones
        for index in range(len(self)-1):
            node = self[index]
            if node.format_result is None:
                raise MissingFormatResultError(node)
            out += node.format_result + node.child_separator
        #end for each node
        if self[-1].format_result is None:
            raise MissingFormatResultError(self[0])
        #end handle missing format
        out += self[-1].format_result
        return out
    
    ## -- End Interface -- @}

# end class StringFormatNodeList

## -- End Generator Nodes -- @}


# ==============================================================================
## @name Generator Trees
# ------------------------------------------------------------------------------
## @{

class StringFormatNodeTree(ElementNodeTree):
    """A tree which iterates a tree of `StringFormatNode` compatible nodes.
    
    It implements an algorithm which allows to efficiently walk a tree only along the branches that can be
    substituted using an input dictionary."""
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## the basic require we have for element nodes
    ElementNodeType = StringFormatNode
    ## the type of node list that we guarantee 
    ElementNodeListType = StringFormatNodeList
    
    ## -- End Configuration -- @}
    
    def __init__(self, root_node):
        """Initialize this instance with a root node of the appropriate type"""
        if not isinstance(root_node, StringFormatNode):
            raise ValueError("Require a StringFormatNodeTree")
        #end assure type
        super(StringFormatNodeTree, self).__init__(root_node)
        
    def _iter_formatted_node_at(self, node_list, data, predicate=None, prune=None):
        """Completely override the base functionality such that we will count level specific information
        on our own stack and yield ourselves once we know that we have reached the longest path.
        We will prune the path right away if this parent is already invalid.
        @param node_list list of nodes which indicate the current parent
        @param data a data dictionary for value substitution
        @param predicate determines if a node list can be returned
        @param prune determines if we may enter recursion
        """
        node = node_list[-1]
        if node.apply_format(data).format_result is None:
            raise StopIteration
        #end stop this branch if this node is not valid
        
        # figure out if there is a valid child - if not, this must be a valid path (which is the longest one)
        # we will apply the pruning to determine which children we actually consider
        # this set helps to prevent prune to be called more than once per child list
        valid_child_nodes = list()
        
        for child_node in node.children():
            node_list.append(child_node)
            try:
                if prune is not None and prune(node_list):
                    continue
                #end ignore pruned children
                if child_node.apply_format(data).format_result is not None:
                    valid_child_nodes.append(child_node)
                    # do not break here, we want to prune out all to find valid ones, which involves the prune
                    # otherwise we might believe we don't have to yield this path, even though the children
                    # will later be pruned completely.
                    # break
                #end use child
            finally:
                node_list.pop()
            #end assure list is popped
        #end for each child
        
        # if we have no valid children, yield this list
        if not valid_child_nodes:
            if predicate is None or predicate(node_list):
                yield node_list
            #end handle result
        #end yield actual result
        
    
        # enter recursion
        for child_node in valid_child_nodes:
            node_list.append(child_node)
            try:
                for child_nlist in self._iter_formatted_node_at(node_list, data,
                                                                       predicate=predicate, prune=prune):
                    yield child_nlist
                #end for each child in recursion
            finally:
                node_list.pop()
            #end handle parent list
        #end for each valid child path
        
        
    # -------------------------
    ## @name Interface
    # @{
    
    def iterate_formatted_nodes(self, data, predicate=None, prune=None):
        """
        The Iteration Algorithm
        =======================
        The algorithm works such that it will iterate all `StringFormatNodes` top-down, in a breadth-first manner. 
        If a node fails to substitute its format, the corresponding StringFormatNodeList will not be 
        returned, but only its parent.
        
        Generally, the tool will only return the longest possible StringFormatNodeLists.
        @return an iterator yielding `StringFormatNodeList` compatible instances which successfully substituted
        all their variables using the given `DictObject` compatible `data` instance.
        @param data a (possibly nested) DictObject providing all available data for substitution.
        @param predicate a function returning True for every StringFormatNodeList that should be yielded.
        @param prune a function returning True if the children of the given node list should not be iterated.
        This can greatly improve performance if you know where you want to iterate upon
        """
        nlist_base = self.ElementNodeListType()
        nlist_base.append(self.root_node())
        
        # assure we only provide copies, internally we work on the very same list
        for nlist in self._iter_formatted_node_at(nlist_base, data, predicate=predicate, prune=prune):
            yield nlist.clone()
        #end for each node list from iteration
        
    
    ## -- End Interface -- @}
    
    @classmethod
    def new(cls, root_key, data, element_node_type=ElementNodeType):
        """Creates a new root node with the type we require.
        @note see our base class documentation for more information"""
        return super(StringFormatNodeTree, cls).new(root_key, data, element_node_type)
        

# end class StringFormatNodeTree

## -- End Generator Trees -- @}


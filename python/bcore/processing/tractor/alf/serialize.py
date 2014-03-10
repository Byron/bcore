#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.serialize
@brief A module with serialization types - they are decoupled entirely from the tree structure

@copyright 2013 Sebastian Thiel
"""
__all__ = ['AlfSerializer']

import bcore
import os

from .types import (
                        Assign,
                        Cmd
                    )
                    
from .schema import (
                        JobDate,
                        Assignments,
                        Tasks,
                        Commands,
                        Tags,
                        IDRef, 
                        TaskTitleRef,
                        RefBase,
                        ReturnCodes
                    )

class AlfSerializerBase(object):
    """A base to implement the algorithm to serialize an Alf tree into a stream.
    
    Subclasses must implement a callback to actually write characters into the stream.
    @note this base enforces a certain order in which node attributes are written"""
    __slots__ = (
                    '_writer' # the stream to use for initialiation
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    simple_attribute_types = (JobDate, Tags, IDRef, TaskTitleRef, ReturnCodes, str, int, bool)
    tree_attribute_types = (Tasks, )
    list_attribute_types = (Assignments, Commands)
    
    ## -- End Configuration -- @}
    
    
    def __init__(self):
        """Initialize with default values"""
        self._writer = None
        
    def _recursive_serialization(self, node, depth):
        """Perform actual serialization"""
        self._node(node, depth, True)
        seen_attrs = list()
        all_attrs = list()
        
        schema = node.alf_schema.mandatory_options 
        if schema:
            all_attrs.extend(schema.keys())
            for attr in self._mandatory_attrs(schema):
                self._node_attr(node, attr, depth, True)
                seen_attrs.append(attr)
            # end for each mandatory arg to write
        # end have mandatory attributes
        
        schema = node.alf_schema.options 
        if schema:
            all_attrs.extend(schema.keys())
            
            # WRITE SIMPLE ATTRIBUTES
            ##########################
            for attr in self._filter_optional_attrs_by_type(schema, self.simple_attribute_types):
                self._node_attr(node, attr, depth, False)
                seen_attrs.append(attr)
            # end for each simple attribute
            
            
            # WRITE LIST ATTRIBUTES and RECURSIVE ATTRIBUTES
            for attribute_types in (self.list_attribute_types, self.tree_attribute_types):
                for attr in self._filter_optional_attrs_by_type(schema, attribute_types):
                    seen_attrs.append(attr)
                    node_list = getattr(node, attr)
                    if not node_list:
                        continue
                    # end skip empty lists
                    self._recurse(node, attr, depth, True)
                    for child_node in node_list:
                        self._recursive_serialization(child_node, depth+1)
                    # end for each node
                    self._recurse(node, attr, depth, False)
                # end for each advanced attribute
            # end for each advanced attribute type
        # end if we have options at all
        
        self._assert_written_attributes(seen_attrs, all_attrs)
        self._node(node, depth, False)
        
    
    # -------------------------
    ## @name Utilities
    # @{
    
    def _mandatory_attrs(self, schema):
        """@return all mandatory arguments of given schema
        @param schema a schema dictionary which is declared mandatory
        @note not sorted, as order matters"""
        return schema.keys()
        
    def _filter_optional_attrs_by_type(self, schema, types):
        """@return a sorted list of attributes which have any of the given types
        @param schema a schema dicitionary which is declared optional
        @param types a single type or a list of types"""
        return sorted(attr for attr, typ in schema.iteritems() if issubclass(typ, types))
        
    def _assert_written_attributes(self, seen_attributes, all_schema_attributes):
        """This methods just asserts that we have written everything. If this is not the case, it could be a bug.
        If you want to filter attributes, you should make sure this method doesn't raise by overriding it"""
        assert len(seen_attributes) == len(all_schema_attributes), "didn't write all attributes"
        
    ## -- End Utilities -- @}
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    def init(self, writer):
        """Intialize this instance with a write function
        @param writer a function taking a single argument, being the string to write. Could be  file.write for instance.
        It may also be an object with a write function, which is when we will select the write function ourselves."""
        self._writer = writer
        if hasattr(writer, 'write'):
            self._writer = writer.write
        # end convenience case
        return self
    
    def serialize(self, node, resolve_references=True):
        """Serialize the given tree into the our stream
        @param node an instance of type AlfTreeOperator or AlfOperatorBase
        @param resolve_references by default, we resolve reference prio to serialization and may thus change the
        input tree operator.
        @note calls resolve_references on the tree
        @return self"""
        assert self._writer is not None, 'call init() beforehand'
        if resolve_references and hasattr(node, 'resolve_references'):
            node.resolve_references()
        # end resolve refs if possible to detect errors
        self._recursive_serialization(node, 0)
        return self
        
    ## -- End Interface -- @}
    
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    @bcore.abstractmethod
    def _recurse(self, node, attr, depth, enter):
        """Called when the children of the given node are recursed into.
        @param node AlfTreeOperator node whose children we will examine breadth first
        @param attr attribute name which provides us with new tree values
        @param depth integer denoting the depth of the node in the tree. 0 is the root node
        @param enter if True, we are entering the recursion, otherwise we are exiting it.
        Per node there will be exactly two calls to recurse, if there are children"""
        
    @bcore.abstractmethod
    def _node(self, node, depth, enter):
        """Called when we start serializing a node, or when we are done
        @note see _recurse() for an explanation of arguments"""
        
    @bcore.abstractmethod
    def _node_attr(self, node, attr, depth, mandatory):
        """Write the given node's attribute data into the stream basd
        @param node an instance of type AlfTreeOperator
        @param attr the name of the attribute
        @param depth level at which tree node exists
        @param mandatory if True, attr is mandatory, otherwise its an optional one"""
        
    
    ## -- End Subclass Interface -- @}

    

# end class BaseSerializer


class AlfSerializer(AlfSerializerBase):
    """A serializer to produce alf formatted streams"""
    __slots__ = (
                    '_prefix'   # prefix for every line we print 
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    tab = '\t'
    
    ## -- End Configuration -- @}
    
    def __init__(self):
        super(AlfSerializer, self).__init__()
        self._prefix = ''
    
    def _update_prefix(self, depth):
        """Set the prefix to correspond to the given tree level depth"""
        self._prefix = self.tab * depth
        
    # -------------------------
    ## @name Subclass Implementation
    # @{
    
    def _recurse(self, node, attr, depth, enter):
        if enter:
            token = '-%s {%s' % (attr, os.linesep)
            self._writer(token)
        else:
            self._update_prefix(depth)
            self._writer(self._prefix + '} ')
        # end handle enter recursion
        
    def _node(self, node, depth, enter):
        self._update_prefix(depth)
        if enter:
            self._writer(self._prefix + node.__class__.__name__ + ' ')
        else:
            self._writer(os.linesep)
        # end handle enter
        
    def _node_attr(self, node, attr, depth, mandatory):
        value = getattr(node, attr)
        if value is None or not value:
            return
        # end handle no-value
        
        if isinstance(value, JobDate):
            value = "%s %s %s:%s" % (value.month, value.day, value.hour, value.minute)
        elif isinstance(value, list):
            value = ', '.join(str(val) for val in value)
        elif isinstance(value, RefBase):
            value = value.id
        elif isinstance(node, Cmd) and attr == 'appname':
            # needs special handling, as args is a variables argument list we have parsed ourselves
            if node.args:
                value += ' ' + ' '.join(str(arg) for arg in node.args)
            # end handle node args
        else:
            value = str(value)
        # end handle different types
        
        if ' ' in value or '\n' in value:
            value = "{ %s }" % value
        # end handle brackets
        
        if not mandatory:
            self._writer('-%s ' % attr)
        # end handle arg prefix
        
        self._writer(value + ' ')
            
    ## -- End Subclass Implementation -- @}
        

    

# end class AlfSerial

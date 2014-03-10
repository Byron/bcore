#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.generators.base
@brief A package containing task tree generators and respective base classes

@copyright 2013 Sebastian Thiel
"""
__all__ = ['NodeGeneratorBase', 'SequenceGeneratorBase', 'ValueSequenceGeneratorBase', 
           'NodeGeneratorContextStore', 'NodeGeneratorChainBase']

import bcore

from bcore.core.kvstore import (
                                KeyValueStoreSchema,
                                KeyValueStoreModifier,
                                KeyValueStoreModifierDiffDelegate,
                                KeyValueStoreSchemaValidator,
                                ValidateSchemaMergeDelegate,
                            )

from bcore.core.diff import (
                            TwoWayDiff,
                            AdditiveMergeDelegate,
                            RootKey
                        )

from bcore.utility import GraphIteratorBase



class NodeGeneratorContextStoreModifierDiffDelegate(KeyValueStoreModifierDiffDelegate):
    """A delegate to raise on missing keys, instead of putting in the default value.
    
    When setting values, we always merge additively"""
    DictType = dict
    
    def _handle_deleted(self, key, parent_tree, previous_value):
        if key is not RootKey:
            parent_tree[key] = previous_value
        # handle deleted
    

class NodeGeneratorContextStore(KeyValueStoreModifier):
    """
    A keyvalue store whose diffing algorithm is modified to raise on missing keys. Default values are
    considered a missing key as well
    """
    __slots__ = ()
    
    KeyValueStoreModifierDiffDelegateType = NodeGeneratorContextStoreModifierDiffDelegate
    
# end class NodeGeneratorContextStore


class NodeGeneratorValidateSchemaMergeDelegate(ValidateSchemaMergeDelegate):
    """Keys are only clashing if their types don't match"""
    __slots__ = ()
    
    def _resolve_conflict(self, key, left_value, right_value):
        """Return the newest value and record the key which clashed"""
        self._clashing_keys.append(self._qualified_key(self._to_string_key(key)))
        return right_value

# end class NodeGeneratorValidateSchemaMergeDelegate


class NodeGeneratorSchemaValidator(KeyValueStoreSchemaValidator):
    """Tests against types only, not against values. Therefore, classes will only be reported if 
    there is a types mismatch"""
    __slots__ = ()
    
    ValidateSchemaMergeDelegateType = NodeGeneratorValidateSchemaMergeDelegate

# end class NodeGeneratorSchemaValidator


class _NodeGeneratorMeta(bcore.MetaBase):
    """A meta-class to auomatically generate certain fields for NodeGenerators"""
    
    def __new__(metacls, name, bases, clsdict):
        attrs = 'variable_field_schema', 'static_field_schema'
        # find all schemas of all bases and merge them into the combined_field_schema attribute
        schemas = list()
        def check_and_append(schema):
            # can't really check if the schema is already in the list as x in list doesn't seem to yield
            # correct results, saying True even if its false (??)
            if schema is not None:
                schemas.append(schema)
            # end handle schema
        # end utility 
        
        for base in bases:
            for mro_cls in base.mro():
                for attr in attrs:
                    check_and_append(getattr(mro_cls, attr, None))
                # end for each attr to check for schemas
            # end for each mro_cls (including base)
        # end for each base
        for attr in attrs:
            check_and_append(clsdict.get(attr, None))
        # end for each attr
        
        if schemas:
            clsdict['combined_field_schema'] = NodeGeneratorSchemaValidator.merge_schemas(list(reversed(schemas)), merge_root_keys=False)
        # end add combined field
        
        return super(_NodeGeneratorMeta, metacls).__new__(metacls, name, bases, clsdict)
        
# end class _NodeGeneratorMeta


class NodeGeneratorBase(GraphIteratorBase):
    """base class for all task generators, providing basic functionality to subclasses.
    
    A generator, as the name suggests, creates a task hierarchy to define a particular kind of job, which is
    accessible to it, but not created by it.
    
    It is receiving a call for initialization, any amount of iteration calls to generate actual tasks, and 
    one call to finish up the operation.
    On each iteration, it will receive a context matching its field schema, to allow it build the respective
    task tree.
    Some generators can iterate indefinitely, some can only iterate only a fixed amount based on values provided
    during their initialization.
    
    A generator defines a schema for variable fields which it requires in its context information during the 
    iteration.
    
    Task generators are chainable with other generators, in order build an increasingly complex nested task
    structure. They may add to their own context as they please, and its entirely optional to actually
    alter the task structure. Generators are connected like a singly linked list.
    """
    __slots__ = (
                    '_next',        # The next producer/generator
                )
    __metaclass__ = _NodeGeneratorMeta
    
    
    
    def __init__(self, next = None):
        """Initialize our variables
        @param next the next Generator, or None to end the chain.
        @see next() and set_next()"""
        self._next = next
    
    # -------------------------
    ## @name Subclass Configuration
    # @{
    
    ## A schema identifying the data you require to generate your task hierarchy
    ## Fields in this schema will change during each iteration
    ## @note should be set in subclass, but may be None
    variable_field_schema = None
    
    ## A schema identifying static fields from which variables fields will be generated on each iteration
    ## This can be seen as configuration of this type.
    ## It is absolutely viable and possible to change this information from iteration to iteration though,
    ## as others could make it part of their variable field schema. This is useful, for instance, to vary
    ## chunk start-end from one file to the next
    ## @note should be set in subclass, but may be None
    static_field_schema = None
    
    ## A schema being the additive combination from the previous two. This separation is mainly useful
    ## for gui purposes, but internally only a single schema is used for convenience
    ## Automaticially generated by metaclass
    combined_field_schema = None
    
    ## A delegate to do additive merges, used to merge schemas together when asking for default_context()
    AdditiveMergeDelegateType = AdditiveMergeDelegate
    
    ## Type of the context store created by us
    NodeGeneratorContextStoreType = NodeGeneratorContextStore
    
    ## -- End Configuration -- @}
    
    # -------------------------
    ## @name Interface Implementation
    # @{
    
    def _predecessors(self, node):
        raise NotImplementedError("there are no predecessors")
        
    def _successors(self, node):
        if node._next:
            return [node._next]
        return tuple()
    
    ## -- End Interface Implementation -- @}
    
    
    # -------------------------
    ## @name Utilities
    # @{
    
    def _context_value(self, context, schema = None):
        """@return the context value for the given schema
        @param context NodeGeneratorContextStore instance from which to extract a value
        @param schema usually one of our two schemas, static or dynamic
        If None, the combined field schema will be chosen automatically"""
        if schema is None:
            schema = self.combined_field_schema
        return context.value(schema.key(), schema)
        
    def _set_context_value(self, context, value, schema = None):
        """Set the context to use the given value, as previously obtained by context_value
        @param context NodeGeneratorContextStore instance into which to set the value
        @param value possibly nested value, as previously obtained by _context_value()
        @param schema if unset, it will default to the combined_field_schema. Its the schema to use when
        setting the values
        @return self"""
        if schema is None:
            schema = self.combined_field_schema
        context.set_value(schema.key(), value)
        return self
        
    @classmethod
    def _merge_schemas(self, schemas):
        """@return see merge_schemas, this is just a redirect"""
        return NodeGeneratorSchemaValidator.merge_schemas(schemas, merge_root_keys=False)
        
    ## -- End Utilities -- @}
    
    
    # -------------------------
    ## @name Subclass Interface
    # Functions to be implemented or useful for subclasses
    # @{
    
    def _generation(self, context, begin):
        """Called before the iteration through calls to _tree_iterator starts
        @param context context with static fields suitable for consumption according to your schema
        @param begin if True, we are beginning the generation of tasks, otherwise we have ended it
        @note subclasses should call this implementation"""
    
    @bcore.abstractmethod
    def _tree_iterator(self, context):
        """A method producing a task based on the given context
        @param context a NodeGeneratorContextStore instance to query the values according to your static AND dynamic 
        field schema.
        The values in the fields usually changes between the invocations in case of dynamic fields. 
        Its valid to change the dynamic fields defined in your schema as well.
        @return an iterator yielding any amount of new Task instance (which can have any amount of subtasks)
        """
        
    def _default_context(self):
        """@return a NodeGeneratorContextStore instance containing all your static fields
        @note similar to default_context(), but always local to this instance
        @note default implementation will return a copy of our static schema, if it exists"""
        if self.static_field_schema is None:
            return self.NodeGeneratorContextStoreType(dict())
        return self.NodeGeneratorContextStoreType({self.static_field_schema.key() : self.static_field_schema}, take_ownership = False)
    
    def _is_valid_context(self, context):
        """@return True if the given context contains values suitable for us to operate
        @note default implementation always returns true, as we already have strong guarantees that all
        values that we need are contained in the context or seem suitable"""
        return True
    
    ## -- End Subclass Interface -- @}
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    def generator(self, context):
        """Produce an iterator to generate the actual task or job, or AlfTreeOperator in general, based on 
        the given context information
        @param context NodeGeneratorContextStore with all static fields defined in the static_field_schema of ourselves
        and all of our connected generators. You can use default_context() to obtain a context with all required 
        fields.
        @return an iterator yielding possibly deeply nested Jobs/and/or Tasks
        @throws Exception if a required static field was not provided
        """
        self._generation(context, True)
        for tree in self._tree_iterator(context):
            # call children
            assert hasattr(tree, 'subtasks'), 'need to generate tree nodes'
            if self.next() is not None:
                for sub_task in self.next().generator(context):
                    tree.subtasks.append(sub_task)
                # end for each subtask
            #end have tree
            yield tree
        # end for each tree
        self._generation(context, False)
        # end for each generator
        
    def default_context(self):
        """@return a NodeGeneratorContextStore instance whose fields are initialized with some sensible defaults. Those 
        can be obtained from any data source.
        The fields match our static field schema.
        The instance will include all fields used by our next() generators, recursively.
        @note this function is used by user interfaces to provide initial values, or options that can be changed"""
        # additive merge over all static schemas, don't allow overrides
        delegate = self.AdditiveMergeDelegateType()
        twoway = TwoWayDiff()
        base = delegate.DictType()
        
        for generator, depth in self._iter_(self, self.downstream, self.breadth_first):
            twoway.diff(delegate, base, generator._default_context().data())
            base = delegate.result()
        # end for each generator
        return self.NodeGeneratorContextStoreType(delegate.result())
        
    def is_valid_context(self, context):
        """@return True if all generators support the values in this context
        @note this is interesting to check compatibility of particular configurations prior to attempting 
        to generate tasks. Most notably, task generators could check the proposed job file is suitable for them"""
        return all(generator._is_valid_context(context) for generator, depth in self._iter_(self, self.downstream, self.breadth_first))
        
    def field_schema(self):
        """@return a merged  KeyValueStoreSchema instance, being a combination of all static schemas that are defined by instances 
        in our chain. The schema's key will be the RootKey
        @see next() and set_next() to build a chain of generators"""
        schemas = list()
        for generator, depth in self._iter_(self, self.downstream, self.breadth_first):
            if generator.static_field_schema:
                schemas.append(generator.static_field_schema)
        # end for each schema
        return self._merge_schemas(schemas)
        
    def set_next(self, generator):
        """Set the generator which should be called to obtain a child tree
        @param generator a generator instance, or None to end the generator chain
        @return self"""
        self._next = generator
        return self
    
    def next(self):
        """@return instance being the next iterator in line, or None or there is None"""
        return self._next
        
    ## -- End Interface -- @}

# end class NodeGeneratorBase


class NodeGeneratorChainBase(object):
    """A simple utility type which represents a chain of generators. A chain has a head and a tail.
    Subtypes are the main item expected by the generator framework, as it is able to maintain a complex
    and dynamically generated chain of generators in one package
    @note this type is intended to be subclassed to initialize it with the desired head"""
    __slots__ = (
                    '_head' ## the chain's head of type NodeGeneratorBase
                )
    
    def __init__(self):
        """Intialize the chain with no head"""
        self._head = None
    
    # -------------------------
    ## @name Interface
    # @{
    
    def head(self):
        """@return head of this generator chain"""
        return self._head
        
    def tail(self):
        """@return tail of the generator chain"""
        next = self._head
        while next.next():
            next = next.next()
        return next
        
    def default_context(self):
        """@return our heads default context
        @note subtypes can use this method to fill in additional values"""
        return self.head().default_context()
        
    def generator(self, context):
        """@return our heads generator instance, which will use the given context to produce Alf tasks
        @note useful for subtypes which want to have a pre-callback. Post-callbacks are not really possible
        as the generator might be invoked any time. However, in the end it depends on your application"""
        return self.head().generator(context)
        
    def prepend_head(self, head):
        """Add the given head in front of the current head
        @param head a chainable object which implements the NodeGeneratorBase interface
        @return self"""
        self.set_head(head.set_next(self.head()))
        return self
        
    def set_head(self, head):
        """set the chain to use the given head, discarding the previous one
        @return self"""
        self._head = head
        return self
        
    ## -- End Interface -- @}    

# end class NodeGeneratorChainBase


class SequenceGeneratorBase(NodeGeneratorBase):
    """A generator producing contexts in a certain definable order.
    
    Sequence generators are useful for splitting up sequences of values into smaller chunks, which are used 
    in context fields in a certain order.
    
    For instance, once can sequence a frame range from 1-10 into 3 chunks 1,10,2-9. Any other algorithm could
    be imagined here.
    
    Other forms of sequences are a list of strings, which can be interpreted as nodes for rendering. For instance,
    a nuke scene with 3 writers, w1, w2, w3, could be chunked into two chunks with w1-w2 and w3.
    Or imagine a list of files, that are all chunked individually, but could be sorted in various ways.  
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## don't change the ordering at all 
    ORDER_UNCHANGED = 'unchanged'
    ## invert the order
    ORDER_INVERSED = 'inverse' 
    
    ## A list of orderings we support natively via _ordered_chunks() 
    ordering = [ORDER_UNCHANGED, ORDER_INVERSED]
    
    ## -- End Configuration -- @}
    
    
    # -------------------------
    ## @name Subclass Utilities
    # Methods that can be used by subclasses
    # @{
    
    def _ordered_chunks(self, chunks, order):
        """@return a new list of chunks with an order as defined by the order argument
        @param chunks a list of chunks, as previously returned by a call to chunks()
        @param order a tag specifying the order, must be one of our ORDER_* constants"""
        if order == self.ORDER_INVERSED:
            return list(reversed(chunks))
        elif order == self.ORDER_UNCHANGED:
            return chunks
        # end handle ordering scheme
        
        raise AssertionError(order + ' is not implemented')
        
        
    ## -- End Subclass Utilities -- @}
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    @bcore.abstractmethod
    def chunks(self, context):
        """@return a list of chunks in a format depending on the subclass implementation.
        @param context static fields used to configure the chunk range
        @note if chunks is 0, a single chunk with all items must be generated! Negative values are treated 
        as a divider, so -1 is similar to 0, -2 means two chunks are desired."""
        
    ## -- End Interface -- @}
        
    
# end class SequenceGeneratorBase


class ValueSequenceGeneratorBase(SequenceGeneratorBase):
    """Provides a list of values that can be chunked together in various ways.
    
    This type is useful when handling names of nodes that are to be rendered, or names of layers or passes 
    that you want.
    
    We support chunking by specifying how many values we want per chunk
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    def _value_chunks(self, values, values_per_chunk, order = SequenceGeneratorBase.ORDER_UNCHANGED):
        """Utility method to produce chunks of a list of values
        @param values an iterable of values we should use for chunking
        @param values_per_chunk amount of values per chunk
        @param order one of our orderings
        @return a list of lists of values"""
        assert order in self.ordering, 'invalid order'
        assert values_per_chunk > 0
        
        out = list()
        for cfirst in range(0, len(values), values_per_chunk):
            # make use of auto-clamping of slices
            out.append(values[cfirst:cfirst + values_per_chunk])
        #end for each chunk range
        
        return self._ordered_chunks(out, order)
    
    ## -- End Subclass Interface -- @}
    

# end class ValueSequenceGeneratorBase




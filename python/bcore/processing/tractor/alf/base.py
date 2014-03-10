#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.base
@brief Base classes for use with tractor

@copyright 2013 Sebastian Thiel
"""
__all__ = ['AlfOperatorMeta', 'AlfOperatorBase', 'AlfTreeOperator']

import bcore
from bcore.utility import GraphIteratorBase

# ==============================================================================
## @name Alf Base Classes
# ------------------------------------------------------------------------------
## @{


class AlfOperatorMeta(bcore.MetaBase):
    """Metaclass setting up descriptors for accessing stored values based on the schema."""
    __slots__ = ()
    
    attr_prefix = '_'
    
    class TypeCheckingDescriptor(object):
        """Checks for a given type and converts appropriately"""
        __slots__ = (
                        'attr', ## Name of the attribute we refer to 
                        'type'  ## type of the attribute we refer to
                    )
        
        iterable_types = (tuple, list, set)
        
        def __init__(self, attr, type):
            self.attr = attr
            self.type = type
            
        def _attrname(self):
            """@return name of the instance attribute"""
            return AlfOperatorMeta.attr_prefix + self.attr
            
        def __get__(self, inst, cls):
            """default-aware getter"""
            if inst is None:
                return self
            # allow access to descriptor itself
            try:
                return getattr(inst, self._attrname())
            except AttributeError:
                # return empty lists or None !
                # None is used as a marker to indicate a value is not set
                if issubclass(self.type, self.iterable_types):
                    value = self.type()
                else:
                    value = None
                # end handle nil type
                # cache the value for later
                self.__set__(inst, value)
                return value
            # end handle value is unset
            
        def __set__(self, inst, value):
            # None is always allowed as this marks an attribute unset
            if value is not None and not isinstance(value, self.type):
                # scalar value to list conversion
                if issubclass(self.type, self.iterable_types) and not isinstance(value, self.iterable_types):
                    value = [value]
                # end handle scalar conversion
                value = self.type(value)
            setattr(inst, self._attrname(), value)
        
    # end class TypeCheckingDescriptor
    
    
    @classmethod
    def _setup_descriptors(cls, schema, clsdict):
        """Setup decriptoros to match the given schema. By default we create slots with the schema key
        prefixed with underscore, and a descriptor at the place of the key for type verification and conversion
        """
        slots = clsdict.get('__slots__')
        assert isinstance(slots, (tuple, list)), '__slots__ must be present and tuple or instance'
        slots = list(slots)
        
        for key, value_type in schema.iteritems():
            slot_var = cls.attr_prefix + key
            assert slot_var not in slots, "meta class will add schema keys, you shouldn't do it explicitly"
            slots.append(slot_var)
            
            # Allow overrides !
            assert key not in clsdict, "metaclass expects no customizations of attr access - try to subclass it"
            clsdict[key] = cls.TypeCheckingDescriptor(key, value_type)
        # end for each key
        clsdict['__slots__'] = slots
        
    
    def __new__(metacls, name, bases, clsdict):
        """Setup descriptors to facilitate and automate attribute access"""
        alf_schema = clsdict.get('alf_schema')
        if alf_schema:
            for attr in ('options', 'mandatory_options'):
                schema = getattr(alf_schema, attr)
                if schema:
                    metacls._setup_descriptors(schema, clsdict)
                # end check schema exists
            # end for each attr
        #end have schema
        
        return bcore.MetaBase.__new__(metacls, name, bases, clsdict)

# end class AlfOperatorMeta


class AlfOperatorBase(object):
    """A base class to help defininig operators"""
    __slots__ = ()
    __metaclass__ = AlfOperatorMeta

    
    ## A schema specifying attributes of the alf command
    alf_schema = None
    
    def __init__(self, *args, **kwargs):
        """Initialize this instance with arguments matched against the mandatory and free options
        @param args always matched to mandatory arguments.
        If there is just one argument and it is a tuple or list, it will be interpreted as *args.
        If it is a dict, it will be updating the possibly existing **kwargs.
        @param kwargs matched to mandatory arguments first, then to actual options"""
        assert self.alf_schema is not None, "subtype must set its alf_schema"
        
        if len(args) == 1:
            if isinstance(args[0], dict):
                kwargs.update(args[0])
                args = tuple()
            elif isinstance(args[0], (tuple, list)):
                args = args[0]
            # end handle packing
        # allow dicts as first arguments to support implicit type
        
        args = list(args)
        self._parse_mandatory_args(args, kwargs)
        self._parse_options(kwargs)
        
        assert len(args) == 0, "Unparsed arguments: %s" % (', '.join(args))
        assert len(kwargs) == 0, "Unparsed kwargs: %s" % str(kwargs)
    
    # -------------------------
    ## @name Subclass Overridable
    # @{
    
    def _set_attrs_from_dict(self, schema, kwargs):
        """Set our own attributes from keys and their values in kwargs if it is existing in schema.
        Each match will be removed from kwargs.
        @return set with matched keys"""
        matched = set()
        for key, value in kwargs.items():
            if not key in schema:
                continue
            # let descriptor do the type checking
            setattr(self, key, value)
            del(kwargs[key])
            matched.add(key)
        # end for each key, value in kwargs
        return matched
    
    def _parse_options(self, kwargs):
        """Parse all optional arguments from the list of passed in key-value arguments"""
        schema = self.alf_schema.options
        if not schema:
            return
        self._set_attrs_from_dict(schema, kwargs)
        
    def _parse_mandatory_args(self, args, kwargs):
        """Parse all mandatory arguments. If they are not matched in kwargs, they are obtained in order 
        from args"""
        schema = self.alf_schema.mandatory_options
        if not schema:
            return
        
        # parse named args
        matched = self._set_attrs_from_dict(schema, kwargs)
        
        # try to match remaining arguments one by one from args in order
        for key in schema.keys():
            if key in matched:
                continue
            if not args:
                raise AssertionError("not enough arguments given to parse mandatory arguments - current key: %s" % key)
            setattr(self, key, args.pop(0))
            matched.add(key)
        # end for each key in schema
        remaining = set(schema.keys()) - matched 
        assert len(remaining) == 0, "didn't match the following mandatory arguments: %s" % (', '.join(remaining))
        
    ## -- End Subclass Overridable -- @}

# end class AlfOperatorBase


class AlfTreeOperator(AlfOperatorBase, GraphIteratorBase):
    """An operator that sets up a tree of items.
    As those items can refer to each other, there is a relation between id and refersto tags of commands and/or
    tasks"""
    __slots__ = ()
    
    def __str__(self):
        """@return pretty version of self"""
        return "%s(title='%s')" % (type(self).__name__, self.title)
    
    # -------------------------
    ## @name GraphIteratorBase Implementation
    # @{
    
    def _predecessors(self, node):
        raise NotImplementedError()
        
    def _successors(self, node):
        if isinstance(node, AlfTreeOperator):
            return node.subtasks
        return list()
    
    ## -- End GraphIteratorBase Implementation -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def resolve_references(self):
        """Verify task and command relations for consistency, and resolve the Referal with the actual instance.
        We also verify that task titles are unique per job
        @note for now we only check for duplicate ids and task titles and for invalid references.
        We also assume Job scope for IDs, not sub-tasks scope as described in the tractor docs to keep 
        the implementation simple. Therefore we are more enforcing than tractor, which could be a problem
        if static task templates are to be duplicated.
        We would have to just implement a recursive breadth first iteration ourselves to have the callbacks
        nicely
        @note its safe to call it multiple times, which will just update previous occurrences accordingly
        @return self
        @throws Exception if referrals are inconsistent"""
        
        task_map = dict() # 'task title' => task instance
        id_map = dict() # 'id' => Cmd or Task
        idrefs = list() # a list of IDrefs or TaskIDRef to resolve
        duplicate_tasks = list()    # a list of tasks which have the same title
        
        def add_to_idmap(item):
            """Adds given item to idmap but asserts that it doesn't exist there and that id is not None"""
            if item.id is None:
                return
            assert item.id not in id_map, "Item %s has duplicate ID: '%s'" % (item, item.id)
            id_map[item.id] = item
        # end utility
            
        def add_cmd_refs(cmds):
            """Adds idrefs from given commands to our maps and lists"""
            for cmd in cmds:
                add_to_idmap(cmd)
                if cmd.refersto is not None:
                    idrefs.append(cmd.refersto)
            # end for each command to handle
        # end utility
        
        # Need to delay import due to cycles ... 
        from .schema import IDRef
        from .types import Instance, Task
        
        # First, gather all items with an ID - for now we assume anything can point at anything
        # Which is the case for Instances to tasks, but not for IDs
        for item, level in self._iter_(self, self.downstream, self.breadth_first):
            # This will iterate tasks and instances
            if isinstance(item, Instance):
                idrefs.append(item.taskref)
                continue
            # end handle instance
            
            # Handle Task or Job
            # Get commands
            for cmd_attr in ('cleanup', 'cmds'):
                cmds = getattr(item, cmd_attr, None)
                if cmds:
                    add_cmd_refs(cmds)
            # end for each command attr
            
            if isinstance(item, Task):
                # Its a task
                add_to_idmap(item)
                if item.title in task_map:
                    duplicate_tasks.append(item)
                task_map[item.title] = item
            # end handle task
        # end for each iteration step
        
        # At this point, we have no duplicate ids or titles, now resolve the references
        for ref in idrefs:
            if isinstance(ref, IDRef):
                lut = id_map
            else:
                lut = task_map
                # lazily flag the error only if it would be one
                if len(duplicate_tasks) > 0:
                    msg = "The following duplicate tasks where found, Instance references would not be unique: "
                    msg += ', '.join(str(task) for task in duplicate_tasks) 
                    raise AssertionError(msg)
                # end handle duplicates
            # end handle different reference types
            assert ref.id in lut, "reference %s could not be found in lookup table - is there a spelling error?" % ref
            ref.instance = lut[ref.id]
        # end for each idref
        
        return self
    ## -- End Interface -- @}

# end class AlfTreeOperator


## -- End Alf Base Classes -- @}



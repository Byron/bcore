#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.schema
@brief Contains schemas for tractor related types

@copyright 2013 Sebastian Thiel
"""
__all__ = ['Assignments', 'Tasks', 'Tags', 'ReturnCodes', 'Commands', 'TaskTitleRef', 'IDRef', 'JobDate']


import bcore
from bcore.core.kvstore import TypedList
from bcore.utility import OrderedDict

from .base import AlfOperatorBase


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{


class AlfList(TypedList):
    """A list which allows to be initialized with any amount of arguments, or with a single list-like argument,
    which is useful for convenient static initialization"""
    __slots__ = ('_args', '_kwargs')
    
    def __new__(cls, *args, **kwargs):
        """hides kwargs, provides it for later"""
        # ignore base class !
        inst = list.__new__(cls)
        inst._args = args
        inst._kwargs = kwargs
        return inst
        
    def __init__(self, *args, **kwargs):
        """Allows static initialization with iterable or without"""
        TypedList.__init__(self)
        if len(self._args) == 1:
            if not isinstance(self._args[0], (tuple, list, set)):
                self._args = [self._args]
            else:
                self._args = self._args[0]
            # end deal with all kinds of args
        # end scalar to iterable conversion
        for arg in self._args:
            self.append(arg)
    
    
# end class AlfList


## -- End Utilities -- @}


# ==============================================================================
## @name Utility Types
# ------------------------------------------------------------------------------
## @{


class Assignments(AlfList):
    """A unique list of assignments. Duplicate variable names are not allowed in the list
    
    Allowed Syntax
    --------------
    
    @snippet test_examples.py alf_assignments
    @snippet test_examples.py alf_assignments_explicit
    
    
    Deduplication
    -------------
    Duplicates are not allowed and will fail in the moment you try to append.
    
    @snippet test_examples.py alf_assignments_duplicates
    
    @note extend will not check for duplicates !
    """
    __slots__ = ()
    
    def __init__(self, *args, **kwargs):
        """Allows for name=value assignments, which are translated into actual assignments"""
        AlfList.__init__(self)
        for key, value in self._kwargs.iteritems():
            self.append(self.MemberType(key, value))
        # end for each key-value pair
        del(self._kwargs)
        
    def append(self, value):
        """Hanlde duplicates"""
        super(Assignments, self).append(value)
        
        varname = self[-1].varname
        for index in range(len(self)-1):
            if self[index].varname == varname:
                raise AssertionError("Variable named %s did already exist in assignments" % varname)
            # end has varname already ?
        # end check for duplicates
        
    

# end class Assignments


class Tasks(AlfList):
    """brief docs"""
    __slots__ = ()
    
    @classmethod
    def _is_valid_member(cls, value):
        """@return True for Tasks and instance"""
        from .types import Instance
        return isinstance(value, Instance) or super(Tasks, cls)._is_valid_member(value)
        
    
    
# end class Tasks
    
    
class Tags(AlfList):
    """A set of string tags that are supposed to remain unque. Tags name a resources that is usually limited, 
    but it can also be used to count particular kinds of jobs.
    Tags are only kept in lowercase, the case doesn't matter to tractor.
    
    @note auto-deduplication only works for append and during initialilzation.
    
    ## Examples
    
    @snippet test_examples.py alf_tags
    """
    __slots__ = ()
    
    MemberType = str
    
    def append(self, value):
        """Assured proper type and case"""
        if not isinstance(value, str):
            value = str(value)
        value = value.lower()
        if value in self:
            return
        super(Tags, self).append(value)
    
# end class Tags


class ReturnCodes(AlfList):
    """A list of integer return codes"""
    __slots__ = ()
    
    MemberType = int

    
# end class ReturnCodes


class Commands(TypedList):
    """A list of Cmd types"""
    __slots__ = ()
    
    
class RefBase(object):
    """A simple type which holds the id of the task or command it refers to, and the instance 
    once the pointer was resolved"""
    __slots__ = ( 
                    'id',           ## Id of our referral
                    'instance',     ## The actual instance
                )
    
    def __init__(self, id):
        """Initialize this instance"""
        self.id = id
        self.instance = None
        
    def __str__(self):
        return "%s(id='%s')" % (type(self).__name__, self.id)

# end class RefBase


class TaskTitleRef(RefBase):
    """A reference to a Task (and only a Task), where id specifies a task Title"""
    __slots__ = ()

# end class TaskTitleRef 


class IDRef(RefBase):
    """A reference to the ID of a Task or a Command"""
    __slots__ = ()

# end class IDRef


class AnyType(object):
    """When called with a single argument, the argument itself is returned."""
    __slots__ = ()
    
    def __new__(cls, *args):
        """Must be called with at least one argument"""
        assert args, "must be called with exactly one argument"
        return args[0]
        

# end class AnyType


## -- End Utility Types -- @}


# ==============================================================================
## @name Schema Classes
# ------------------------------------------------------------------------------
## @{

class AlfSchemaBase(object):
    """A base class for alf related schemas"""
    
    ## A schema defining the options we support. Those are entirely optional.
    # They must be provided as key-value args
    # NOTE: we don't support nested schemas here
    options = None
    
    ## A schema definining mandatory options - they have to be provided.
    # They can be provided as arguments as well as key-value args
    # @note no support for nested schemas
    # @warning order matters here, therefore instantiate an ordered dict and set values one by one ! 
    mandatory_options = None
    
# end class AlfSchemaBase


# NOTE: Have to put next two classes here to suit code dependencies
class JobDateSchema(AlfSchemaBase):
    """A schema for the job date"""
    __slots__ = ()
    
    mandatory_options = OrderedDict()
    for name in ('month', 'day', 'hour', 'minute'):
        mandatory_options[name] = int
    # end assure order is kept

# end class JobDateSchema


class JobDate(AlfOperatorBase):
    """An Alfred Job date. Hours are measured in 24, not in 12 as you cannot specify AM/PM
    
    ## Examples
    
    @snippet test_examples.py alf_jobdate_usage
    
    @note It is an AlfOperator just for user convenience. 
    """
    __slots__ = ()

    alf_schema = JobDateSchema

# end class JobDate


class Job(AlfSchemaBase):
    """A schema for a Job operator"""
    __slots__ = ()
    
    options = OrderedDict() 
    options['title']       = str
    options['after']       = JobDate
    options['init']        = Assignments
    options['subtasks']    = Tasks
    options['cleanup']     = Commands
    options['atleast']     = int
    options['atmost']      = int
    options['tags']        = Tags
    options['service']     = str
    options['envkey']      = str
    options['etalevel']    = int
    options['comment']     = str
    options['metadata']    = str
    options['editpolicy']  = str
    options['postscript']  = Commands

# end class Job


class Task(AlfSchemaBase):
    """A schema for the Task operator"""
    __slots__ = ()
    
    mandatory_options = { 'title' : str }
    
    options = OrderedDict()
    options['subtasks']        = Tasks
    options['cmds']            = Commands
    options['cleanup']         = Commands
    options['chaser']          = str
    options['preview']         = str
    options['service']         = str
    options['serialsubtasks']  = bool
    options['id']              = str

# end class Task


class Cmd(AlfSchemaBase):
    """A schema for the operator class"""
    options = OrderedDict()
    options['msg']         = str
    options['service']     = str
    options['tags']        = Tags
    options['metrics']     = str
    options['id']          = str
    options['exand']       = bool
    options['refersto']    = IDRef
    options['atleast']     = int
    options['atmost']      = int
    options['samehost']    = bool
    options['envkey']      = str
    options['retryrc']     = ReturnCodes
            
    mandatory_options = OrderedDict()
    mandatory_options['appname'] = str

# end Cmd Schema

class Instance(AlfSchemaBase):
    """A schema for the Instance operator class"""
    __slots__ = ()

    mandatory_options = { 'taskref' : TaskTitleRef }

# end class Instance

class Assign(AlfSchemaBase):
    """A schema for Assign operator"""
    __slots__ = ()
    
    mandatory_options = OrderedDict()
    mandatory_options['varname'] = str
    mandatory_options['value'] = AnyType

# end class Assign
## -- End Schema Classes -- @}


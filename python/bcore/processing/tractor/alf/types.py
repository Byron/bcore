#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.types
@brief Utilities to build alf data structures in python

@note all classes in this module refer to Alf objects. The prefix was removed to keep things more readable
and more simple.
@copyright 2013 Sebastian Thiel
"""
__all__ = ['Job', 'Task', 'Cmd', 'RemoteCmd', 'Instance', 'Assign']

from .base import (
                        AlfTreeOperator,
                        AlfOperatorBase
                   )

from . import schema

# ==============================================================================
## @name Implementations
# ------------------------------------------------------------------------------
## @{

class Job(AlfTreeOperator):
    """A Job representation, see http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html#job"""
    __slots__ = ()
    
    alf_schema = schema.Job
    
# end class Job


class Task(AlfTreeOperator):
    """A Task representation, see http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html#task"""
    __slots__ = ()

    alf_schema = schema.Task
    
# end class Task


class Cmd(AlfOperatorBase):
    """A Command representation, see http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html#cmd
    
    Examples
    --------
    
    @snippet test_examples.py alf_cmd
    """
    __slots__ = (
                    'appname', # Application name
                    'args',    # list of arguments
                )
    
    alf_schema = schema.Cmd              
    
    def _parse_mandatory_args(self, args, kwargs):
        """Parse app-name and 
        raise NotImplementedError()"""
        super(Cmd, self)._parse_mandatory_args(args, kwargs)
        self.args = list(args[:])
        del(args[:])
    
    def executable_property():
        """"""
        def get(self):
            return self.appname
            
        def set(self, val):
            self.appname = val
            
        return property(get, set)
        
    ## Alias for appname
    executable = executable_property()
    del(executable_property)

# end class Cmd


class RemoteCmd(Cmd):
    """A remote command repreentation, see http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html#remotecmd"""
    __slots__ = ()


# end class RemoteCmd


class Instance(AlfOperatorBase):
    """A instance representation, see http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html#instance"""
    __slots__ = ()
    
    alf_schema = schema.Instance


# end class Instance


class Assign(AlfOperatorBase):
    """A variable assignment for alf-scripts, see http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html#assign.
    Stored values may be any string-convertible instance.
    As a special feature, we call 'value_string' value, which is the actual python value.
    It will be converted to a string during serialization"""
    __slots__ = ()
    
    alf_schema = schema.Assign
    
    def value_string_property():
        def get(self):
            if self.value is None:
                return None
            return str(self.value)
            
        def set(self, val):
            self.value = val
            
        return property(get, set)
        
    value_string = value_string_property()
    del(value_string_property)


# end class Assign

## -- End Implementations -- @}





# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
# NOTE: At some point, we would abstract this into meta-types which are suitable for interpretation by GUI as well
## @{

class StringChoice(list):
    """A list that can keep information of a selected entry"""
    # This can't be pickled
    __slots__ = (
                    '_selected', # index which is considered selected
                )
    
    def __init__(self, *args, **kwargs):
        super(StringChoice, self).__init__(*args, **kwargs)
        self._selected = 0
        
    # -------------------------
    ## @name Pickle Support
    # @{
    
    def __getstate__(self):
        return (1, self._selected)
        
    def __setstate__(self, state):
        version, data = state
        assert version == 1
        self._selected = data
    
    ## -- End Pickle Support -- @}
        
    
    def set_selected_index(self, index):
        """Sets the given index to be selected. Must be valid and within the bounds of this list"""
        assert index > -1 and index < len(self)
        self._selected = index
        return self
        
    def selected_index(self):
        """@return the currently selected index"""
        return self._selected
        
    def selected(self):
        """@return selected value"""
        return self[self._selected]
        
# end class StringChoice

## -- End Utilities -- @}

# Special fix = Setup member types for our 'Multi-Operator' types - they can't do it themselves as there
# is a dependency cycle
schema.Assignments.MemberType = Assign
schema.Tasks.MemberType = Task
schema.Commands.MemberType = Cmd

# -*- coding: utf-8 -*-
"""
@package tx.decorators
@brief useful standard decorators

@copyright 2012 Sebastian Thiel
"""

__all__ = ['return_member']

from bcore.utility import wraps

# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
## @{

## @note looks like this could be done with properties as well
## @note also, from the name of this decorator it's not apparent that the value can't be None
##       that would be better handled by not hasattr -> raise error, value is None -> return value
##       and a seperate not_none decorator

def return_member(name):
    """A decorator returning a member with `name` of the input instance
    @note raise if the member does not exist or is None"""
    def function_receiver(fun):
        """receives the actual function to wrap"""
        @wraps(fun)
        def wrapper(instance):
            """implements obtaining the member"""
            try:
                rval = getattr(instance, name)
                if rval is None:
                    raise AttributeError
                return rval
            except AttributeError:
                cls = instance
                if not isinstance(instance, type):
                    cls = type(instance)
                #end obtain class instance
                raise AssertionError("Class %s has to set the %s member" % (cls.__name__, name))
            #end exception handling
        #end wrapper
        return wrapper
    #end function receiver
    return function_receiver

## -- End Decorators -- @}

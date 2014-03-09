#-*-coding:utf-8-*-
"""
@package tx.base
@brief Most fundamental base types

@copyright 2012 Sebastian Thiel
"""
__all__ = ['Error', 'InterfaceBase', 'MetaBase', 'abstractmethod']

import abc
from abc import abstractmethod

from itertools import chain

# NOTE: Place additional imports of items that should be available here
# Make sure you adjust the __all__ list accordingly

# ==============================================================================
## \name Exceptions
# ------------------------------------------------------------------------------
# Basic Exception Types
## \{

class Error(Exception):
    """Most foundational pipeline exception"""
    __slots__ = ()

# end class Error
## -- End Exceptions -- \}


# ==============================================================================
## \name Meta-Classes
# ------------------------------------------------------------------------------
# Our basic meta classes which allow us to manipulate all class level functions
# at will to automated otherwise tedious processes.
## \{

class MetaBase(abc.ABCMeta):
    """A base class for all other meta-classes used in the @ref tx package.
    
    It provides facilities to automatically wrap methods into decorators which 
    perform certain tasks, like additional logging for improved debugging.
    
    * All subclasses of InterfaceBase are put into tx as well, allowing their access
      through tx.InterfaceName.
    * Puts new types into tx if the type itself (not its subtype) has the 'place_into_root_package' set to True
    """
    
    place_into_root_package_attribute_name = 'place_into_root_package'
    
    @staticmethod
    def __new__(mcls, name, bases, clsdict):
        """Create a new type and return it"""
        for base in bases:
            if base.__name__ == 'InterfaceBase':
                clsdict[mcls.place_into_root_package_attribute_name] = True
                break
            # end name mateches
        # end put into tx
        new_cls = super(MetaBase, mcls).__new__(mcls, name, bases, clsdict)
        if clsdict.get(mcls.place_into_root_package_attribute_name, False):
            import bcore
            setattr(tx, name, new_cls)
        # end should put it into root package
        return new_cls

    # -------------------------
    ## @name Subclass Interface
    # Methods for use by subclasses
    # @{
    
    @classmethod
    def _class_attribute_value(cls, clsdict, bases, attribute):
        """@return value found at clsdict[attribute] or bases.mro().__dict__[attribute] in standard search
        order, or None if nothing was found.
        @note useful if you store information for digestion by your metaclasson on the  type itself, or 
        on base classes of that type. This method basically emulates inheritance.
        @param cls
        @param clsdict
        @param bases
        @param attribute string identifying the attribute in the class dicts to look at"""
        def iterate_clsdicts():
            for base in bases:
                for mro_cls in base.mro():
                    yield mro_cls.__dict__
            # end for each base
        # end for each 
        
        # iterate top down
        for cls_dict in reversed(list(chain(iterate_clsdicts(), (clsdict, )))):
            rval = cls_dict.get(attribute)
            if rval:
                return rval
        # end for each clsdict to iterate
        
        return None
        
    ## -- End Subclass Interface -- @}
    

# end class MetaBase

## -- End Meta-Classes -- \}


# ==============================================================================
## \name Basic Types
# ------------------------------------------------------------------------------
# Implementations for types suitable to serve as base for derived types 
## \{

class InterfaceBase(object):
    """base class for all interfaces"""
    
    ## Provides support for ABC decorators, like abstractmethod
    __metaclass__ = MetaBase
    
    ## Slots help to protect against typos when assigning variables, keep instances small, and document the
    ## types member variables
    __slots__ = tuple()
    
    def supports(self, interface_type):
        """@return True if this instance supports the interface of the given type
        @param interface_type type of the interface/class you require this instance to be derived from, or a 
        tuple of interfaces or classes
        @note useful if you only have a weak reference of your interface instance
        or proxy which is a case where the ordinary `isinstance(obj, iInterface)`
        will not work"""
        return isinstance(self, interface_type)

## -- End Basic Types -- \}



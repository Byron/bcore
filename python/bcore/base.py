#-*-coding:utf-8-*-
"""
@package bcore.base
@brief Most fundamental base types

@copyright 2012 Sebastian Thiel
"""
__all__ = ['Error', 'InterfaceBase', 'MetaBase', 'abstractmethod', 'Version']

import abc
from abc import abstractmethod
import re

from itertools import chain

# NOTE: Place additional imports of items that should be available here
# Make sure you adjust the __all__ list accordingly

# ==============================================================================
## \name Exceptions
# ------------------------------------------------------------------------------
# Basic Exception Types
## \{

class Error(Exception):
    """Most foundational framework exception"""
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
    """A base class for all other meta-classes used in the @ref bcore package.
    
    It provides facilities to automatically wrap methods into decorators which 
    perform certain tasks, like additional logging for improved debugging.
    
    * All subclasses of InterfaceBase are put into bcore as well, allowing their access
      through bcore.InterfaceName.
    * Puts new types into bcore if the type itself (not its subtype) has the 'place_into_root_package' set to True
    """
    
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


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
# 
## @{

class Version(object):
    """An RPM-like version implementation, which doesn't make assumptions, yet allows comparison of arbitraty 
    strings.
    This type will also allow to analyse version strings and could server as a base class for more constraint
    version types.
    
    Non-alphanumeric characters are used as separator between tokens, each token serving as sub-version
    
    Comparisons are implemented using the 
    [RPM comparison algorithm](http://fedoraproject.org/wiki/Archive:Tools/RPM/VersionComparison)
    
    ## Examples ####
    
    * 2012.2.0
    * 1.2.3-R1
    * 20
    * foo.bar
    """
    __slots__ = ('_version')

    _re_tokens = re.compile('[0-9]+|[a-zA-Z]+')
    
    # -------------------------
    ## @name Configuration
    # @{
    
    TOKEN_ANY = "any"
    TOKEN_STRING = "string"
    TOKEN_NUMBER = "number"
    
    ## Represents an unknown version, and default instance are intiialized with it
    UNKNOWN = 'unknown'
    
    ## -- End Configuration -- @}
    
    def __init__(self, version_string = UNKNOWN):
        """Intiialize this instance
        @param version_string a string of pretty much any format that resembles a version. Usually, it consists
        of digits and/or names"""
        assert isinstance(version_string, basestring), '%s was %s, require string' % (version_string, type(version_string))
        self._version = version_string
        
        
    def _tokens(self):
        """@return a list of all tokens, dot separated"""
        return self._re_tokens.findall(self._version)
        
    # -------------------------
    ## @name Protocols
    # @{
    
    def __hash__(self):
        """brief docs"""
        return hash(self._version)
    
    def __cmp__(self, rhs):
        """Compare ourselves with the other version or string using 
        [RPM comparison algorithm](http://fedoraproject.org/wiki/Archive:Tools/RPM/VersionComparison)"""
        if not isinstance(rhs, type(self)):
            rhs = type(self)(rhs)
        # assure type
        
        lts, rts = self._tokens(), rhs._tokens()
        for lt, rt in zip(lts, rts):
            if isinstance(lt, int):
                if isinstance(rt, int):
                    if lt == rt:
                        continue
                    else:
                        return cmp(lt, rt)
                    # handle int comparison
                else:
                    # strings are always older compared to ints
                    return 1
                # handle rt type
            else:
                if isinstance(rt, basestring):
                    if lt == rt:
                        continue
                    else:
                        return cmp(lt, rt)
                    # end string handle comparison
                else:
                    # ints are always newer
                    return -1
                # end handle rt type
            # end handle lt type
        # end for each token
        
        # still here ? compare the length - more tokens are better
        cmp_len = cmp(len(lts), len(rts))
        if cmp_len != 0:
            return cmp_len
        # end 
        
        # equality !
        return 0
        
    def __str__(self):
        return self._version
    
    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self._version)
        
    def __getitem__(self, index):
        """@return version token at the given index. Type can be integer or string"""
        return self.tokens()[index]
        
    ## -- End Protocols -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def tokens(self, token_type = TOKEN_ANY):
        """@return list of tokens of the given type that this version is comprised of
        @note any number will be returned, even if it is part of a string"""
        assert token_type in (self.TOKEN_ANY, self.TOKEN_STRING, self.TOKEN_NUMBER)
        tokens = self._tokens()
        
        res = list()
        for token in self._tokens():
            try:
                number = int(token)
                if token_type in (self.TOKEN_NUMBER, self.TOKEN_ANY):
                    res.append(number)
                # end handle number type
            except ValueError:
                if token_type in (self.TOKEN_STRING, self.TOKEN_ANY):
                    res.append(token)
                # end handle string type
            # end handle exception
        # end for each token
        return res
        
    ## -- End Interface -- @}
    
# end class Version

## -- End Utilities -- @}




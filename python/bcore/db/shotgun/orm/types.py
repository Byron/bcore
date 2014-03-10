#-*-coding:utf-8-*-
"""
@package bcore.db.shotgun.orm.types
@brief Custom types representing respective shotgun types

@copyright 2013 Sebastian Thiel
"""
__all__ = ['value_type_map', 'ShotgunEntityMarker', 'ShotgunMultiEntityMarker']

from datetime import (
                        datetime,
                        date
                     )
from time import (
                    strptime,
                    gmtime
                 )

from bcore import ILog
from bcore.utility import DictObject

log = service(ILog).new('bcore.db.shotgun.orm.types')


class ShotgunEntityMarker(object):
    """Indicates a shotgun entity type is to be used"""
    __slots__ = ()

# end class ShotgunEntityMarker


class ShotgunMultiEntityMarker(object):
    """Indicates this property is of type MultiEntity"""
    __slots__ = ()

# end class ShotgunMultiEntityMarker


class _ShotgunTypeMixin(object):
    """Always pass through incoming values, and provide utility methods.
    It assumes the actual target type is the class derived from first"""
    __slots__ = ()
    
    def __new__(cls, *args):
        """Pass through incoming args, or convert them if needed, but only to the actual type"""
        Type = cls.type()
        if not args:
            return Type()
            
        value = args[0]
        if not isinstance(value, Type):
            try:
                return Type(value)
            except Exception:
                raise TypeError("Failed to convert input type %s to target type %s" % (type(value), Type))
            # end try conversion
        # end handle incorrect type
        
        # just use the given value, no need to convert it
        return value
        
    # -------------------------
    ## @name Interface
    # @{
    
    @classmethod
    def type(cls):
        """@return actual type that we  are representing"""
        return cls.__bases__[1]
    
    @classmethod
    def isinstance(cls, value):
        """@return True if the given value's type is an instance of our actual Type"""
        return isinstance(value, cls.type())
        
    ## -- End Interface -- @}

# end class _ShotgunTypeMixin


class _ShotgunDateMixin(_ShotgunTypeMixin):
    """A wrapper which fixes a type if needed, but lets through types that don't need fixing"""
    __slots__ = ()
    
    # FIX DB TYPES
    ###############
    def __new__(cls, *args):
        """In our test database, we have been storing just strings, even though the API deals with 
        datetime objects. Just to be sure we are good, we check the type here and convert it back
        to what it was.
        @note this is code that shouldn't be here, but it's easier than pre-processing our input data every
        time we test
        """
        if not args:
            # default value an equivalent to null, but at least of correct type
            return datetime(*gmtime(0)[:6])
        else:
            val = args[0]
            if isinstance(val, basestring):
               if len(val) == 25:
                   # cut timezone (for now, its just for testing ... ) could bring it in too
                   return datetime(*strptime(val[:-6], "%Y-%m-%d %H:%M:%S")[:6])
               elif len(val) == 10:
                   # its a date
                   return date(*strptime(val, "%Y-%m-%d")[:3])
               # end handle format
            # end handle conversion
            # otherwise return the original instance
            return val
        # end handle type conversion
        

# end class ShotgunDate


class ShotgunDate(_ShotgunDateMixin, date):
    __slots__ = ()
    
    
# end class ShotgunDate


class ShotgunDateTime(_ShotgunDateMixin, datetime):
    __slots__ = ()
    
    
# end class ShotgunDateTime


class ShotgunPassword(_ShotgunTypeMixin, str):
    """A string like '*******'"""
    __slots__ = ()

# end class ShotgunPassword


class ShotgunCheckbox(_ShotgunTypeMixin, int):
    """Just a boolean value"""
    __slots__ = ()

# end class ShotgunCheckbox


class ShotgunUUID(_ShotgunTypeMixin, unicode):
    """Values like this: 4f65d7be-def9-11df-bae7-00304898dbee"""
    __slots__ = ()

# end class ShotgunUUID


class ShotgunText(_ShotgunTypeMixin, unicode):
    __slots__ = ()

# end class ShotgunText


class ShotgunFootage(_ShotgunTypeMixin, unicode):
    """Format matches Preference value for "Formatting > Display of footage fields". Example above is default.F=Feet f=Frames."""
    __slots__ = ()

# end class ShotgunFootage


class ShotgunEntityType(_ShotgunTypeMixin, unicode):
    __slots__ = ()

# end class ShotgunEntityType


class ShotgunURL(_ShotgunTypeMixin, DictObject):
    """A shotgun URL consists of a few fields that can be set directly"""
    __slots__ = ()

# end class ShotgunURL


class ShotgunPercent(_ShotgunTypeMixin, int):
    __slots__ = ()

# end class ShotgunPercent


class ShotgunImage(_ShotgunTypeMixin, unicode):
    __slots__ = ()

# end class ShotgunImage


class ShotgunSummary(_ShotgunTypeMixin, unicode):
    """This type is returned, but seems always empty"""
    __slots__ = ()
    

# end class ShotgunSummary


class ShotgunFloat(_ShotgunTypeMixin, float):
    __slots__ = ()

# end class ShotgunFloat


class ShotgunList(_ShotgunTypeMixin, unicode):
    """Similarly to StatusLists, we are talking about a single member of a custom enumeration.
    Custom means that a list can't have icons associated with it, a status list can"""
    __slots__ = ()

# end class ShotgunList


class ShotgunNumber(_ShotgunTypeMixin, int):
    __slots__ = ()

# end class ShotgunNumber


class ShotgunColor(_ShotgunTypeMixin, unicode):
    """Colors are just strings with individual channels separated by ',', and values normalized to 255.
    They can also be a symbolic color"""
    __slots__ = ()
    
    # -------------------------
    ## @name Interface
    # @{
    
    def __new__(cls, *args):
        """Makes sure we are becoming an actual copy of the input, and thus have some methods to operate on it"""
        return unicode.__new__(cls, *args)
    
    @classmethod
    def new(cls, channels, symbol=None):
        """@return a new instance of our type, either as color with 3 channels or as symbol
        @param cls
        @param channels a tuple of 3 integer values ranging from 0 to 255, associated with r, g, b 
        respectively.
        @param symbol if not None, the symbolic name of the color. Channels are ignored in that case
        @throws ValueError if integers are out of range
        """
        if symbol:
            return cls(symbol)
        for cid, c in enumerate(channels):
            if not (-1 < c < 256):
                raise ValueError("Channel %i is not within bounds 0-255" % cid)
        # end assert values
        return cls(','.join(str(c) for c in channels))
        
    def is_symbolic(self):
        """@return True if we are a symbolic color, which is just a name"""
        return ',' not in self
        
    def channels(self):
        """@return values for all our 3 channels, R, G, B, as integers from 0 to 255.
        Will be [0,0,0] if we are symbolic"""
        tokens = self.split(',')
        if len(tokens) == 1:
            return [0, 0, 0]
        
        assert len(tokens) == 3
        return [int(token) for token in tokens]
        
    def channel(self, index):
        """@return the channel at the given index
        @throws IndexError if index is larger than 2"""
        return self.channels()[index]
        
    @property
    def r(self):
        """@return red channel"""
        return self.channel(0)
        
    @property
    def g(self):
        """@return green channel"""
        return self.channel(1)
        
    @property
    def b(self):
        """@return blue channel"""
        return self.channel(2)
        
    ## -- End Interface -- @}

# end class ShotgunColor


class ShotgunPivotColumn(_ShotgunTypeMixin, unicode):
    __slots__ = ()
    

# end class ShotgunPivotColumn


class ShotgunDuration(_ShotgunTypeMixin, int):
    __slots__ = ()

# end class ShotgunDuration


class ShotgunTagList(_ShotgunTypeMixin, list):
    __slots__ = ()

# end class ShotgunTagList


class ShotgunSerializable(_ShotgunTypeMixin, dict):
    __slots__ = ()

# end class ShotgunSerializable


class ShotgunStatusList(_ShotgunTypeMixin, unicode):
    """Yes, it's a member of an enumeration (the status list) and therefore not an actual list"""
    __slots__ = ()

# end class ShotgunStatusList


value_type_map = {
         # Entity and multi-entity are treated specially
         'entity' : ShotgunEntityMarker,
         'multi_entity' : ShotgunMultiEntityMarker, 
         # The rest is just normal constructors, taking a value to wrap around their type
         # NOTE: only works if default encoding was adjusted to UTF-8
         'text' : ShotgunText,
         'date_time' : ShotgunDateTime, 
         'password' : ShotgunPassword, 
         'checkbox' : ShotgunCheckbox, 
         'uuid' : ShotgunUUID, 
         'footage' : ShotgunFootage, 
         'entity_type' : ShotgunEntityType,
         'url' : ShotgunURL, 
         'percent' : ShotgunPercent, 
         'image' : ShotgunImage, 
         'float' : ShotgunFloat, 
         'list' : ShotgunList, 
         'number' : ShotgunNumber, 
         'summary' : ShotgunSummary,
         'date' : ShotgunDate, 
         'color' : ShotgunColor, 
         'pivot_column' : ShotgunPivotColumn, 
         'duration' : ShotgunDuration, 
         'tag_list' : ShotgunTagList, 
         'serializable' : ShotgunSerializable, 
         'status_list' : ShotgunStatusList
    }

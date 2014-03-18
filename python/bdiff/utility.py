#-*-coding:utf-8-*-
"""
@package bdiff.utility
@brief Utiltiies for use when diffing and merging is required

@copyright 2013 Sebastian Thiel
"""
__all__ = ['merge_data', 'NonInstantiatable', 'DictObject', 'is_mutable', 'smart_deepcopy', 'OrderedDict']

from UserDict import DictMixin

import pprint
from copy import deepcopy

# ==============================================================================
## @name Routines
# ------------------------------------------------------------------------------
## @{

def is_mutable( value):
    """Recursively check if the given value is mutable.
    
    A value is considered mutable if at least one contained value is mutable
    @param value a possibly nested value of built-in types
    @return true if value is mutable"""
    if isinstance(value, (basestring, int, float, type(None))):
        return False
    #end check immutable
    if isinstance(value, (list, dict)):
        return True
    #end check mutable
    
    if isinstance(value, tuple):
        for item in value:
            if is_mutable(item):
                return True
            #end abort recursion if item is mutable
        #end for each item to check in tuple
    #end handle tuple value
    
    return False

def merge_data(source, destination, delegate_type = None, diff_type = None):
    """A quick-and-dirty helper to more easily perform a merge operation, with all the object types involved
    @param delegate_type if None, it will default to AutoResolveAdditiveMergeDelegate
    @param diff_type if None, it defaults to TwoWayDiff
    @return the delegate's result of the merge operation"""
    # have to use delayed imports here, to mask the dependency which utility shouldn't really have
    if delegate_type is None:
        from .delegates import AutoResolveAdditiveMergeDelegate as delegate_type
    if diff_type is None:
        from .algoithms import TwoWayDiff as diff_type
    delegate = delegate_type()
    diff_type().diff(delegate, destination, source)
    return delegate.result()
    
def smart_deepcopy(value):
    """Create a deep copy of value only if this is necessary as its value has mutable parts.
    @return a deep copy of value if value was mutable
    @note checking for its mutability will cost additional time - its a trade-off between memory and 
    CPU cycles"""
    if is_mutable(value):
        return deepcopy(value)
    return value

## -- End Routines -- @}



# ==============================================================================
## @name Types
# ------------------------------------------------------------------------------
## @{

class NonInstantiatable(object):
    """A mixin which will makes it impossible to instantiate derived types
    
    @throws TypeError if someone tries to create an instance"""
    __slots__ = ()

    # since this prevents the instantiation of the object,
    # the arguments to new aren't used
    # pylint: disable=W0613
    def __new__(cls, *args, **kwargs):
        """Prevents instantiation"""
        raise TypeError("This type cannot be instantiated")
    # pylint: enable=W0613
# end class NonInstantiatable


class DictObject(object):
    """An object which wraps a dictionary to allow object.key access.
    If the source dictionary doesn't contain any sub-dictionaries, the input 
    dict will be referenced. Otherwise it will be copied.
    
    An attribute error is raised if a value is not accessible.
    
    Please note that you cannot access dict keys which are not valid attribute names.
    """
    
    _default_dict = dict()
    _unpackable_types = (dict, tuple, list)
    
    def __init__(self, indict = _default_dict):
        """Initialize this instance from an input dictionary. If it contains other dictionaries, those will 
        trigger their parent dictionaries to be copied, as they will be used as DictObject themselves and 
        placed in the copy accordingly.
        NOTE: other DictObjects are used by reference. Generally, this type tries to perform the least
        amount of copying possible."""
        if indict is self._default_dict:
            return
        # end handle default instantiation, which makes us empty
        if isinstance(indict, DictObject):
            self.__dict__ = indict.__dict__
            return
        #END handle special case, be a reference
        dct = indict
        for key, val in dct.iteritems():
            if isinstance(val, self._unpackable_types):
                dct = None
                break
        #END for each key-value pair
        
        if dct is None:
            dct = dict(indict)
            def unpack(val):
                """unpack helper"""
                if isinstance(val, dict):
                    val = DictObject(val)
                elif isinstance(val, (tuple, list)):
                    val = type(val)(unpack(item) for item in val)
                return val
            #END unpack
            for key, val in dct.iteritems():
                dct[key] = unpack(val)
            #END for each k,v pair
        #END handle recursive copy
        self.__dict__ = dct
        
    def __str__(self):
        return pprint.pformat(self.__dict__)
        
    def __repr__(self):
        return str(self)
        
    def __getattr__(self, name):
        return object.__getattribute__(self, name)
        
    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError:
            raise KeyError(name)
        #end convert exception
        
    def __setitem__(self, name, value):
        setattr(self, name, value)
        
    def __contains__(self, name):
        return name in self.__dict__
    
    def __len__(self):
        return len(self.__dict__)
        
    def __iter__(self):
        return iter(self.__dict__)
        
    def __eq__(self, other):
        """Compares a possibly expensive comparison"""
        if isinstance(other, DictObject):
            # EXPENSIVE !
            return self.to_dict() == other.to_dict()
        elif isinstance(other, dict):
            return self.to_dict() == other
        # end handle type of other
        return self is other
        
    
    # R0912 Too many branches - yes, he is right, however, its how it is - don't want to put 
    # the utilty methods external
    # pylint: disable-msg=R0912
    def to_dict(self, recursive = False):
        """@return ourselves as normal dict
        @param recursive if True, a recursive copy will be returned if required."""
        if recursive:
            def obtain_needs_copy(value):
                """figure out if a copy is required"""
                if isinstance(value, DictObject):
                    return True
                if isinstance(value, (tuple, list, set)):
                    for item in value:
                        if obtain_needs_copy(item):
                            return True
                        #end check needs copy
                    #end for each item in value
                #end if instance is iterable
                return False
            #end check needs copy
            
            # W0631 Using possibly undefined loop variable , val, its defined ... 
            # R0912 Too many branches - yes, he is right, however, its how it is - don't want to put 
            # the utilty methods external
            # pylint: disable-msg=W0631
            def unpack(val):
                """unpack val recursively and copy it gently"""
                if isinstance(val, DictObject):
                    val = val.to_dict(recursive)
                elif isinstance(val, (tuple, list, set)):
                    val = type(val)(unpack(item) for item in val)
                #end handle type resolution
                return val
            #end unpack
            
            needs_copy = False
            for value in self.__dict__.itervalues():
                if obtain_needs_copy(value):
                    needs_copy = True
                    break
                #end check value
            #END for each value
            
            if needs_copy:
                new_dict = dict()
                for key, val in self.__dict__.iteritems():
                    new_dict[key] = unpack(val)
                #END for each key, value pair
                return new_dict
            # else:
            #   just fall through and return ourselves as dictionary
            
        #END handle recursion
        return self.__dict__
        
    def clone(self):
        """@return a deep copy of this dict. This onyl means that the key-sets are independent. However, the 
        values are still shared, which matters in case of lists for instance"""
        return type(self)(deepcopy(self.to_dict(recursive=True)))
        
    def inversed_dict(self):
        """@return new dictionary which uses this dicts keys as values, and values as keys
        @note duplicate values will result in just a single key, effectively drupping items.
        Use this only if you have unique key-value pairs"""
        return dict(zip(self.__dict__.values(), self.__dict__.keys()))
    
    def get(self, name, default=None):
        """as dict.get"""
        return self.__dict__.get(name, default)
        
    def keys(self):
        """as dict.keys"""
        return self.__dict__.keys()
        
    def values(self):
        """as dict.values"""
        return self.__dict__.values()
        
    def items(self):
        """as dict.items"""
        return self.__dict__.items()
        
    def iteritems(self):
        """as dict.iteritems"""
        return self.__dict__.iteritems()


class OrderedDict(dict, DictMixin):
    """@copyright (c) 2009 Raymond Hettinger

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation files
    (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge,
    publish, distribute, sublicense, and/or sell copies of the Software,
    and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:
    
    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
    
    @note: Unfortunately, there is no unit test for this available or I didn't
    find it. As its the default python implementation though, I believe it
    should be working pretty well.
    """
    __slots__ = ('_map', '_end')
    
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        self.clear() # reset
        self.update(*args, **kwds)

    def clear(self):
        end = list()
        object.__setattr__(self, '_end', end)
        object.__setattr__(self, '_map', dict()) # key --> [key, prev, next]
        end += [None, end, end]         # sentinel node for doubly linked list
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            end = self._end
            curr = end[1]
            curr[2] = end[1] = self._map[key] = [key, curr, end]
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        key, prev, next_item = self._map.pop(key)
        prev[2] = next_item
        next_item[1] = prev

    def __iter__(self):
        end = self._end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self._end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def popitem(self, last=True):
        """same as in dict"""
        if not self:
            raise KeyError('dictionary is empty')
        if last:
            key = reversed(self).next()
        else:
            key = iter(self).next()
        value = self.pop(key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        tmp = (self._map, self._end)
        del self._map, self._end
        inst_dict = vars(self).copy()
        self._map, self._end = tmp
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)
        
    def __getattr__(self, name):
        """provides read access"""
        try:
            return self[name]
        except KeyError:
            raise AttributeError("No attribute named '%s'" % name)
        #end handle getitem
        
    def __setattr__(self, name, value):
        """Set the given value into our dict"""
        if name in self.__slots__:
            return super(OrderedDict, self).__setattr__(name, value)
        self[name] = value

    def keys(self):
        """same as in dict"""
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems

    def __str__(self, indent=1):
        indent_str = '    '*indent
        ret_str = "Dict\n"
        for key, value in self.iteritems():
            if isinstance(value, OrderedDict):
                ret_str += "%s%s: %s" % (indent_str, key, value.__str__(indent=indent+1))
            else:
                ret_str += "%s%s: %s\n" % (indent_str, key, str(value))

        return ret_str

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, self.items())

    def copy(self):
        """same as in dict"""
        return self.__class__(self)
        
    def to_dict(self):
        """@return a recursive copy of this dict, except that the dict type is just dict.
        @note useful for pretty-printing"""
        out = dict()
        for key, value in self.iteritems():
            if isinstance(value, self.__class__):
                value = value.to_dict()
            out[key] = value
        #end for each key-value pair
        return out

    @classmethod
    def fromkeys(cls, iterable, value=None):
        """same as in dict"""
        new_dict = cls()
        for key in iterable:
            new_dict[key] = value
        return new_dict

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            if len(self) != len(other):
                return False
            for left, right in  zip(self.items(), other.items()):
                if left != right:
                    return False
            return True
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

## -- End Types -- @}





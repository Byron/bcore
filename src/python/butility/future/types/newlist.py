

import sys
import copy

from future.utils import with_metaclass
from future.types.newobject import newobject


_builtin_list = list
ver = sys.version_info[:2]


class BaseNewList(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, _builtin_list)

class newlist(with_metaclass(BaseNewList, _builtin_list, newobject)):
    
    def copy(self):
        
        return copy.copy(self)

    def clear(self):
        
        for i in range(len(self)):
            self.pop()

    def __new__(cls, *args, **kwargs):
        

        if len(args) == 0:
            return super(newlist, cls).__new__(cls)
        elif type(args[0]) == newlist:
            value = args[0]
        else:
            value = args[0]
        return super(newlist, cls).__new__(cls, value)

    def __add__(self, value):
        return newlist(super(newlist, self).__add__(value))

    def __radd__(self, left):
        " left + self "
        try:
            return newlist(left) + self
        except:
            return NotImplemented

    def __getitem__(self, y):
        
        if isinstance(y, slice):
            return newlist(super(newlist, self).__getitem__(y))
        else:
            return super(newlist, self).__getitem__(y)

    def __native__(self):
        
        return list(self)

    def __nonzero__(self):
        return len(self) > 0


__all__ = ['newlist']

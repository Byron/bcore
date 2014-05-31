

import sys

from future.utils import with_metaclass


_builtin_dict = dict
ver = sys.version_info[:2]


class BaseNewDict(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, _builtin_dict)

class newdict(with_metaclass(BaseNewDict, _builtin_dict)):
    
    def items(self):
        
        if ver == (2, 7):
            return self.viewitems()
        elif ver == (2, 6):
            return self.iteritems()
        elif ver >= (3, 0):
            return self.items()

    def keys(self):
        
        if ver == (2, 7):
            return self.viewkeys()
        elif ver == (2, 6):
            return self.iterkeys()
        elif ver >= (3, 0):
            return self.keys()

    def values(self):
        
        if ver == (2, 7):
            return self.viewvalues()
        elif ver == (2, 6):
            return self.itervalues()
        elif ver >= (3, 0):
            return self.values()

    def __new__(cls, *args, **kwargs):
        

        if len(args) == 0:
            return super(newdict, cls).__new__(cls)
        elif type(args[0]) == newdict:
            value = args[0]
        else:
            value = args[0]
        return super(newdict, cls).__new__(cls, value)
        
    def __native__(self):
        
        return dict(self)


__all__ = ['newdict']

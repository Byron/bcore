

import sys

from future.utils import with_metaclass


_builtin_object = object
ver = sys.version_info[:2]


# Dodgy: this messes up isinstance checks with subclasses of newobject
# class BaseNewObject(type):
#     def __instancecheck__(cls, instance):
#         return isinstance(instance, _builtin_object)

class newobject(_builtin_object):
    
    def next(self):
        if hasattr(self, '__next__'):
            return type(self).__next__(self)
        raise TypeError('newobject is not an iterator')
    
    def __unicode__(self):
        # All subclasses of the builtin object should have __str__ defined.
        # Note that old-style classes do not have __str__ defined.
        if hasattr(self, '__str__'):
            s = type(self).__str__(self)
        else:
            s = str(self)
        if isinstance(s, unicode):
            return s
        else:
            return s.decode('utf-8')

    def __nonzero__(self):
        if hasattr(self, '__bool__'):
            return type(self).__bool__(self)
        # object has no __nonzero__ method
        return True

    # Are these ever needed?
    # def __div__(self):
    #     return self.__truediv__()

    # def __idiv__(self, other):
    #     return self.__itruediv__(other)

    def __long__(self):
        if not hasattr(self, '__int__'):
            return NotImplemented
        return self.__int__()  # not type(self).__int__(self)

    # def __new__(cls, *args, **kwargs):
    #     

    #     if len(args) == 0:
    #         return super(newdict, cls).__new__(cls)
    #     elif type(args[0]) == newdict:
    #         return args[0]
    #     else:
    #         value = args[0]
    #     return super(newdict, cls).__new__(cls, value)
        
    def __native__(self):
        
        return object(self)


__all__ = ['newobject']

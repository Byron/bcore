import types
import sys
import numbers
import functools

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
PY26 = sys.version_info[0:2] == (2, 6)
PYPY = hasattr(sys, 'pypy_translation_info')

def with_metaclass(meta, *bases):
    
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__
        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})


# Definitions from pandas.compat follow:
if PY3:
    def bchr(s):
        return bytes([s])
    def bstr(s):
        if isinstance(s, str):
            return bytes(s, 'latin-1')
        else:
            return bytes(s)
    def bord(s):
        return s
else:
    # Python 2
    def bchr(s):
        return chr(s)
    def bstr(s):
        return str(s)
    def bord(s):
        return ord(s)

###

if PY3:
    def tobytes(s):
        if isinstance(s, bytes):
            return s
        else:
            if isinstance(s, str):
                return s.encode('latin-1')
            else:
                return bytes(s)
else:
    # Python 2
    def tobytes(s):
        if isinstance(s, unicode):
            return s.encode('latin-1')
        else:
            return ''.join(s)


if PY3:
    def native_str_to_bytes(s, encoding='utf-8'):
        return s.encode(encoding)

    def bytes_to_native_str(b, encoding='utf-8'):
        return b.decode(encoding)

    def text_to_native_str(t, encoding=None):
        return t
else:
    # Python 2
    def native_str_to_bytes(s, encoding=None):
        from future.types import newbytes    # to avoid a circular import
        return newbytes(s)

    def bytes_to_native_str(b, encoding=None):
        return native(b)

    def text_to_native_str(t, encoding='ascii'):
        
        return unicode(t).encode(encoding)


if PY3:
    # list-producing versions of the major Python iterating functions
    def lrange(*args, **kwargs):
        return list(range(*args, **kwargs))

    def lzip(*args, **kwargs):
        return list(zip(*args, **kwargs))

    def lmap(*args, **kwargs):
        return list(map(*args, **kwargs))

    def lfilter(*args, **kwargs):
        return list(filter(*args, **kwargs))
else:
    import __builtin__
    # Python 2-builtin ranges produce lists
    lrange = __builtin__.range
    lzip = __builtin__.zip
    lmap = __builtin__.map
    lfilter = __builtin__.filter


def isidentifier(s, dotted=False):
    
    if dotted:
        return all(isidentifier(a) for a in s.split('.'))
    if PY3:
        return s.isidentifier()
    else:
        import re
        _name_re = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")
        return bool(_name_re.match(s))


def viewitems(obj, **kwargs):
    
    func = getattr(obj, "viewitems", None)
    if not func:
        func = obj.items
    return func(**kwargs)


def viewkeys(obj, **kwargs):
    
    func = getattr(obj, "viewkeys", None)
    if not func:
        func = obj.keys
    return func(**kwargs)


def viewvalues(obj, **kwargs):
    
    func = getattr(obj, "viewvalues", None)
    if not func:
        func = obj.values
    return func(**kwargs)


def iteritems(obj, **kwargs):
    
    func = getattr(obj, "iteritems", None)
    if not func:
        func = obj.items
    return func(**kwargs)


def iterkeys(obj, **kwargs):
    
    func = getattr(obj, "iterkeys", None)
    if not func:
        func = obj.keys
    return func(**kwargs)


def itervalues(obj, **kwargs):
    
    func = getattr(obj, "itervalues", None)
    if not func:
        func = obj.values
    return func(**kwargs)


def bind_method(cls, name, func):
    
    # only python 2 has an issue with bound/unbound methods
    if not PY3:
        setattr(cls, name, types.MethodType(func, None, cls))
    else:
        setattr(cls, name, func)


def getexception():
    return sys.exc_info()[1]




def implements_iterator(cls):
    
    if PY3:
        return cls
    else:
        cls.next = cls.__next__
        del cls.__next__
        return cls

if PY3:
    get_next = lambda x: x.next
else:
    get_next = lambda x: x.__next__


def encode_filename(filename):
    if PY3:
        return filename
    else:
        if isinstance(filename, unicode):
            return filename.encode('utf-8')
        return filename


def is_new_style(cls):
    
    return hasattr(cls, '__class__') and ('__dict__' in dir(cls) 
                                          or hasattr(cls, '__slots__'))

# The native platform string and bytes types. Useful because ``str`` and
# ``bytes`` are redefined on Py2 by ``from future.builtins import *``.
native_str = str
native_bytes = bytes


if PY3:
    def istext(obj):
        
        return isinstance(obj, native_str)
else:
    def istext(obj):
        return isinstance(obj, unicode)
# end 


def isbytes(obj):
    
    return isinstance(obj, type(b''))


def isnewbytes(obj):
    
    # TODO: generalize this so that it works with subclasses of newbytes
    # Import is here to avoid circular imports:
    from future.types.newbytes import newbytes
    return type(obj) == newbytes


def isint(obj):
    

    return isinstance(obj, numbers.Integral)


def native(obj):
    
    if hasattr(obj, '__native__'):
        return obj.__native__()
    else:
        return obj


# Implementation of exec_ is from ``six``:

def old_div(a, b):
    
    if isinstance(a, numbers.Integral) and isinstance(b, numbers.Integral):
        return a // b
    else:
        return a / b


def as_native_str(encoding='utf-8'):
    
    if PY3:
        return lambda f: f
    else:
        def encoder(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs).encode(encoding=encoding)
            return wrapper
        return encoder

# listvalues and listitems definitions from Nick Coghlan's (withdrawn)
# PEP 496:
try:
    dict.iteritems
except AttributeError:
    # Python 3
    def listvalues(d):
        return list(d.values())
    def listitems(d):
        return list(d.items())
else:
    # Python 2
    def listvalues(d):
        return d.values()
    def listitems(d):
        return d.items()

if PY3:
    def ensure_new_type(obj):
        return obj
else:
    def ensure_new_type(obj):
        from future.types.newbytes import newbytes
        from future.types.newstr import newstr
        from future.types.newint import newint
        from future.types.newdict import newdict

        native_type = type(native(obj))

        # Upcast only if the type is already a native (non-future) type
        if issubclass(native_type, type(obj)):
            # Upcast
            if native_type == str:  # i.e. Py2 8-bit str
                return newbytes(obj)
            elif native_type == unicode:
                return newstr(obj)
            elif native_type == int:
                return newint(obj)
            elif native_type == dict:
                return newdict(obj)
            else:
                return NotImplementedError('type %s not supported' % type(obj))
        else:
            # Already a new type
            assert type(obj) in [newbytes, newstr]
            return obj


__all__ = ['PY3', 'PY2', 'PYPY', 'python_2_unicode_compatible',
           'as_native_str',
           'with_metaclass', 'bchr', 'bstr', 'bord',
           'tobytes', 'str_to_native_bytes', 'bytes_to_native_str', 
           'lrange', 'lmap', 'lzip', 'lfilter',
           'isidentifier', 'iteritems', 'iterkeys', 'itervalues',
           'viewitems', 'viewkeys', 'viewvalues',
           'bind_method', 'getexception',
           'reraise', 'implements_iterator', 'get_next', 'encode_filename',
           'is_new_style', 'native_str', 'old_div', 'as_native_str',
           'listvalues', 'listitems'
          ]


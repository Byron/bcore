"""minimized future compilation with just the code bcore needs"""
from __future__ import division, absolute_import, print_function


###########
# UTILS ##
#########
# future.utils.__init__.py

import sys
from numbers import Integral
from numbers import Number
from types import FunctionType
from collections import Iterable
import functools

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
PY26 = sys.version_info[0:2] == (2, 6)

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
    return type(obj) == newbytes


def isint(obj):
    

    return isinstance(obj, Integral)


def native(obj):
    
    if hasattr(obj, '__native__'):
        return obj.__native__()
    else:
        return obj


# Implementation of exec_ is from ``six``:

def old_div(a, b):
    
    if isinstance(a, Integral) and isinstance(b, Integral):
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


##############
# BUILTINS ##
############




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


from math import ceil
from collections import Sequence, Iterator


class newrange(Sequence):
    

    def __init__(self, *args):
        if len(args) == 1:
            start, stop, step = 0, args[0], 1
        elif len(args) == 2:
            start, stop, step = args[0], args[1], 1
        elif len(args) == 3:
            start, stop, step = args
        else:
            raise TypeError('range() requires 1-3 int arguments')

        try:
            start, stop, step = int(start), int(stop), int(step)
        except ValueError:
            raise TypeError('an integer is required')

        if step == 0:
            raise ValueError('range() arg 3 must not be zero')
        elif step < 0:
            stop = min(stop, start)
        else:
            stop = max(stop, start)

        self._start = start
        self._stop = stop
        self._step = step
        self._len = (stop - start) // step + bool((stop - start) % step)

    def __repr__(self):
        if self._start == 0 and self._step == 1:
            return 'range(%d)' % self._stop
        elif self._step == 1:
            return 'range(%d, %d)' % (self._start, self._stop)
        return 'range(%d, %d, %d)' % (self._start, self._stop, self._step)

    def __eq__(self, other):
        return isinstance(other, newrange) and \
               self._start == other._start and \
               self._stop == other._stop and \
               self._step == other._step

    def __len__(self):
        return self._len

    def index(self, value):
        
        diff = value - self._start
        quotient, remainder = divmod(diff, self._step)
        if remainder == 0 and 0 <= quotient < self._len:
            return abs(quotient)
        raise ValueError('%r is not in range' % value)

    def count(self, value):
        
        # a value can occur exactly zero or one times
        return int(value in self)

    def __contains__(self, value):
        
        try:
            self.index(value)
            return True
        except ValueError:
            return False

    def __reversed__(self):
        
        sign = self._step / abs(self._step)
        last = self._start + ((self._len - 1) * self._step)
        return newrange(last, self._start - sign, -1 * self._step)

    def __getitem__(self, index):
        
        if isinstance(index, slice):
            return self.__getitem_slice(index)
        if index < 0:
            # negative indexes access from the end
            index = self._len + index
        if index < 0 or index >= self._len:
            raise IndexError('range object index out of range')
        return self._start + index * self._step

    def __getitem_slice(self, slce):
        
        start, stop, step = slce.start, slce.stop, slce.step
        if step == 0:
            raise ValueError('slice step cannot be 0')

        start = start or self._start
        stop = stop or self._stop
        if start < 0:
            start = max(0, start + self._len)
        if stop < 0:
            stop = max(start, stop + self._len)

        if step is None or step > 0:
            return newrange(start, stop, step or 1)
        else:
            rv = reversed(self)
            rv._step = step
            return rv

    def __iter__(self):
        
        return rangeiterator(self)


class rangeiterator(Iterator):
    

    def __init__(self, rangeobj):
        self._range = rangeobj

        # Intialize the "last outputted value" to the value
        # just before the first value; this simplifies next()
        self._last = self._range._start - self._range._step
        self._count = 0

    def __iter__(self):
        
        return self

    def next(self):
        
        self._last += self._range._step
        self._count += 1
        if self._count > self._range._len:
            raise StopIteration()
        return self._last



# Some utility functions to enforce strict type-separation of unicode str and
# bytes:
def disallow_types(argnums, disallowed_types):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):

            errmsg = "argument can't be {0}"
            for (argnum, mytype) in zip(argnums, disallowed_types):
                # Handle the case where the type is passed as a string like 'newbytes'.
                if isinstance(mytype, str) or isinstance(mytype, bytes):
                    mytype = globals()[mytype]

                # Only restrict kw args only if they are passed:
                if len(args) <= argnum:
                    break

                # Here we use type() rather than isinstance() because
                # __instancecheck__ is being overridden. E.g.
                # isinstance(b'abc', newbytes) is True on Py2.
                if type(args[argnum]) == mytype:
                    raise TypeError(errmsg.format(mytype))

            return function(*args, **kwargs)
        return wrapper
    return decorator


def no(mytype, argnums=(1,)):
    
    if isinstance(argnums, Integral):
        argnums = (argnums,)
    disallowed_types = [mytype] * len(argnums)
    return disallow_types(argnums, disallowed_types)


def issubset(list1, list2):
    
    n = len(list1)
    for startpos in range(len(list2) - n + 1):
        if list2[startpos:startpos+n] == list1:
            return True
    return False




_builtin_bytes = bytes

if PY3:
    # We'll probably never use newstr on Py3 anyway...
    unicode = str


class BaseNewBytes(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, _builtin_bytes)


class newbytes(with_metaclass(BaseNewBytes, _builtin_bytes)):
    
    def __new__(cls, *args, **kwargs):
        
        
        encoding = None
        errors = None

        if len(args) == 0:
            return super(newbytes, cls).__new__(cls)
        elif len(args) >= 2:
            args = list(args)
            if len(args) == 3:
                errors = args.pop()
            encoding=args.pop()
        # Was: elif isinstance(args[0], newbytes):
        # We use type() instead of the above because we're redefining
        # this to be True for all unicode string subclasses. Warning:
        # This may render newstr un-subclassable.
        if type(args[0]) == newbytes:
            # Special-case: for consistency with Py3.3, we return the same object
            # (with the same id) if a newbytes object is passed into the
            # newbytes constructor.
            return args[0]
        elif isinstance(args[0], _builtin_bytes):
            value = args[0]
        elif isinstance(args[0], unicode):
            try:
                if 'encoding' in kwargs:
                    assert encoding is None
                    encoding = kwargs['encoding']
                if 'errors' in kwargs:
                    assert errors is None
                    errors = kwargs['errors']
            except AssertionError:
                raise TypeError('Argument given by name and position')
            if encoding is None:
                raise TypeError('unicode string argument without an encoding')
            ###
            # Was:   value = args[0].encode(**kwargs)
            # Python 2.6 string encode() method doesn't take kwargs:
            # Use this instead:
            newargs = [encoding]
            if errors is not None:
                newargs.append(errors)
            value = args[0].encode(*newargs)
            ### 
        elif isinstance(args[0], Iterable):
            if len(args[0]) == 0:
                # This could be an empty list or tuple. Return b'' as on Py3.
                value = b''
            else:
                # Was: elif len(args[0])>0 and isinstance(args[0][0], Integral):
                #      # It's a list of integers
                # But then we can't index into e.g. frozensets. Try to proceed
                # anyway.
                try:
                    values = [chr(x) for x in args[0]]
                    value = b''.join(values)
                except:
                    raise ValueError('bytes must be in range(0, 256)')
        elif isinstance(args[0], Integral):
            if args[0] < 0:
                raise ValueError('negative count')
            value = b'\x00' * args[0]
        else:
            value = args[0]
        return super(newbytes, cls).__new__(cls, value)
        
    def __repr__(self):
        return 'b' + super(newbytes, self).__repr__()

    def __str__(self):
        return 'b' + "'{0}'".format(super(newbytes, self).__str__())

    def __getitem__(self, y):
        value = super(newbytes, self).__getitem__(y)
        if isinstance(y, Integral):
            return ord(value)
        else:
            return newbytes(value)

    def __getslice__(self, *args):
        return self.__getitem__(slice(*args))

    def __contains__(self, key):
        if isinstance(key, int):
            newbyteskey = newbytes([key])
        # Don't use isinstance() here because we only want to catch
        # newbytes, not Python 2 str:
        elif type(key) == newbytes:
            newbyteskey = key
        else:
            newbyteskey = newbytes(key)
        return issubset(list(newbyteskey), list(self))
    
    @no(unicode)
    def __add__(self, other):
        return newbytes(super(newbytes, self).__add__(other))

    @no(unicode)
    def __radd__(self, left):
        return newbytes(left) + self
            
    @no(unicode)
    def __mul__(self, other):
        return newbytes(super(newbytes, self).__mul__(other))

    @no(unicode)
    def __rmul__(self, other):
        return newbytes(super(newbytes, self).__rmul__(other))

    def join(self, iterable_of_bytes):
        errmsg = 'sequence item {0}: expected bytes, {1} found'
        if isbytes(iterable_of_bytes) or istext(iterable_of_bytes):
            raise TypeError(errmsg.format(0, type(iterable_of_bytes)))
        for i, item in enumerate(iterable_of_bytes):
            if istext(item):
                raise TypeError(errmsg.format(i, type(item)))
        return newbytes(super(newbytes, self).join(iterable_of_bytes))

    @classmethod
    def fromhex(cls, string):
        # Only on Py2:
        return cls(string.replace(' ', '').decode('hex'))

    @no(unicode)
    def find(self, sub, *args):
        return super(newbytes, self).find(sub, *args)

    @no(unicode)
    def rfind(self, sub, *args):
        return super(newbytes, self).rfind(sub, *args)

    @no(unicode, (1, 2))
    def replace(self, old, new, *args):
        return newbytes(super(newbytes, self).replace(old, new, *args))

    def encode(self, *args):
        raise AttributeError("encode method has been disabled in newbytes")

    def decode(self, encoding='utf-8', errors='strict'):
        
        # Py2 str.encode() takes encoding and errors as optional parameter,
        # not keyword arguments as in Python 3 str.

        return newstr(super(newbytes, self).decode(encoding, errors))

        # This is currently broken:
        # # We implement surrogateescape error handling here in addition rather
        # # than relying on the custom error handler from
        # # future.utils.surrogateescape to be registered globally, even though
        # # that is fine in the case of decoding. (But not encoding: see the
        # # comments in newstr.encode()``.)
        #
        # if errors == 'surrogateescape':
        #     # Decode char by char
        #     mybytes = []
        #     for code in self:
        #         # Code is an int
        #         if 0x80 <= code <= 0xFF:
        #             b = 0xDC00 + code
        #         elif code <= 0x7F:
        #             b = _unichr(c).decode(encoding=encoding)
        #         else:
        #             # # It may be a bad byte
        #             # FIXME: What to do in this case? See the Py3 docs / tests.
        #             # # Try swallowing it.
        #             # continue
        #             # print("RAISE!")
        #             raise NotASurrogateError
        #         mybytes.append(b)
        #     return newbytes(mybytes)
        # return newbytes(super(newstr, self).decode(encoding, errors))

    @no(unicode)
    def startswith(self, prefix, *args):
        return super(newbytes, self).startswith(prefix, *args)

    @no(unicode)
    def endswith(self, prefix, *args):
        return super(newbytes, self).endswith(prefix, *args)

    @no(unicode)
    def split(self, sep=None, maxsplit=-1):
        # Py2 str.split() takes maxsplit as an optional parameter, not as a
        # keyword argument as in Python 3 bytes.
        parts = super(newbytes, self).split(sep, maxsplit)
        return [newbytes(part) for part in parts]

    def splitlines(self, keepends=False):
        
        # Py2 str.splitlines() takes keepends as an optional parameter,
        # not as a keyword argument as in Python 3 bytes.
        parts = super(newbytes, self).splitlines(keepends)
        return [newbytes(part) for part in parts]

    @no(unicode)
    def rsplit(self, sep=None, maxsplit=-1):
        # Py2 str.rsplit() takes maxsplit as an optional parameter, not as a
        # keyword argument as in Python 3 bytes.
        parts = super(newbytes, self).rsplit(sep, maxsplit)
        return [newbytes(part) for part in parts]

    @no(unicode)
    def partition(self, sep):
        parts = super(newbytes, self).partition(sep)
        return tuple(newbytes(part) for part in parts)

    @no(unicode)
    def rpartition(self, sep):
        parts = super(newbytes, self).rpartition(sep)
        return tuple(newbytes(part) for part in parts)

    @no(unicode, (1,))
    def rindex(self, sub, *args):
        
        pos = self.rfind(sub, *args)
        if pos == -1:
            raise ValueError('substring not found')

    @no(unicode)
    def index(self, sub, *args):
        
        if isinstance(sub, int):
            if len(args) == 0:
                start, end = 0, len(self)
            elif len(args) == 1:
                start = args[0]
            elif len(args) == 2:
                start, end = args
            else:
                raise TypeError('takes at most 3 arguments')
            return list(self)[start:end].index(sub)
        if not isinstance(sub, bytes):
            try:
                sub = self.__class__(sub)
            except (TypeError, ValueError):
                raise TypeError("can't convert sub to bytes")
        try:
            return super(newbytes, self).index(sub, *args)
        except ValueError:
            raise ValueError('substring not found')

    def __eq__(self, other):
        if isinstance(other, (_builtin_bytes, bytearray)):
            return super(newbytes, self).__eq__(other)
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, _builtin_bytes):
            return super(newbytes, self).__ne__(other)
        else:
            return True

    unorderable_err = 'unorderable types: bytes() and {0}'

    def __lt__(self, other):
        if not isbytes(other):
            raise TypeError(self.unorderable_err.format(type(other)))
        return super(newbytes, self).__lt__(other)

    def __le__(self, other):
        if not isbytes(other):
            raise TypeError(self.unorderable_err.format(type(other)))
        return super(newbytes, self).__le__(other)

    def __gt__(self, other):
        if not isbytes(other):
            raise TypeError(self.unorderable_err.format(type(other)))
        return super(newbytes, self).__gt__(other)

    def __ge__(self, other):
        if not isbytes(other):
            raise TypeError(self.unorderable_err.format(type(other)))
        return super(newbytes, self).__ge__(other)

    def __native__(self):
        # We can't just feed a newbytes object into str(), because
        # newbytes.__str__() returns e.g. "b'blah'", consistent with Py3 bytes.
        return super(newbytes, self).__str__()

    @no(unicode)
    def rstrip(self, bytes_to_strip=None):
                
        return newbytes(super(newbytes, self).rstrip(bytes_to_strip))

    @no(unicode)
    def strip(self, bytes_to_strip=None):
                
        return newbytes(super(newbytes, self).strip(bytes_to_strip))

    def lower(self):
                
        return newbytes(super(newbytes, self).lower())

    @no(unicode)
    def upper(self):
                
        return newbytes(super(newbytes, self).upper())

    @classmethod
    @no(unicode)
    def maketrans(cls, frm, to):
        
        return newbytes(string.maketrans(frm, to))




if PY3:
    long = int


class BaseNewInt(type):
    def __instancecheck__(cls, instance):
        # Special case for Py2 short or long int
        return isinstance(instance, (int, long))


class newint(with_metaclass(BaseNewInt, long)):
    
    def __new__(cls, x=0, base=10):
        
        try:
            val = x.__int__()
        except AttributeError:
            val = x
        else:
            if not isint(val):
                raise TypeError('__int__ returned non-int ({0})'.format(type(val)))

        if base != 10:
            # Explicit base
            if not (istext(val) or isbytes(val) or isinstance(val, bytearray)):
                raise TypeError("int() can't convert non-string with explicit base")
            try:
                return super(newint, cls).__new__(cls, val, base)
            except TypeError:
                return super(newint, cls).__new__(cls, newbytes(val), base)
        # After here, base is 10
        try:
            return super(newint, cls).__new__(cls, val)
        except TypeError:
            # Py2 long doesn't handle bytearray input with an explicit base, so
            # handle this here.
            # Py3: int(bytearray(b'10'), 2) == 2
            # Py2: int(bytearray(b'10'), 2) == 2 raises TypeError
            # Py2: long(bytearray(b'10'), 2) == 2 raises TypeError
            try:
                return super(newint, cls).__new__(cls, newbytes(val))
            except:
                raise TypeError("newint argument must be a string or a number, not '{0}'".format(
                                    type(val)))
            
        
    def __repr__(self):
        
        value = super(newint, self).__repr__()
        assert value[-1] == 'L'
        return value[:-1]

    def __add__(self, other):
        value = super(newint, self).__add__(other)
        if value is NotImplemented:
            # e.g. a float
            return long(self) + other
        return newint(value)

    def __radd__(self, other):
        value = super(newint, self).__radd__(other)
        return newint(value)

    def __sub__(self, other):
        value = super(newint, self).__sub__(other)
        return newint(value)

    def __rsub__(self, other):
        value = super(newint, self).__rsub__(other)
        return newint(value)

    def __mul__(self, other):
        value = super(newint, self).__mul__(other)
        if isint(value):
            return newint(value)
        if value is NotImplemented:
            return long(self) * other
        return value

    def __rmul__(self, other):
        value = super(newint, self).__rmul__(other)
        if isint(value):
            return newint(value)
        return value

    def __div__(self, other):
        # We override this rather than e.g. relying on object.__div__ or
        # long.__div__ because we want to wrap the value in a newint()
        # call if other is another int
        value = long(self) / other
        if isinstance(other, (int, long)):
            return newint(value)
        else:
            return value

    def __rdiv__(self, other):
        value = other / long(self)
        if isinstance(other, (int, long)):
            return newint(value)
        else:
            return value

    def __idiv__(self, other):
        # long has no __idiv__ method. Use __itruediv__ and cast back to newint:
        value = self.__itruediv__(other)
        if isinstance(other, (int, long)):
            return newint(value)
        else:
            return value

    def __truediv__(self, other):
        value = super(newint, self).__truediv__(other)
        if value is NotImplemented:
            value = long(self) / other
        return value

    def __rtruediv__(self, other):
        return super(newint, self).__rtruediv__(other)

    def __itruediv__(self, other):
        # long has no __itruediv__ method
        mylong = long(self)
        mylong /= other
        return mylong

    def __floordiv__(self, other):
        return newint(super(newint, self).__floordiv__(other))

    def __rfloordiv__(self, other):
        return newint(super(newint, self).__rfloordiv__(other))

    def __ifloordiv__(self, other):
        # long has no __ifloordiv__ method
        mylong = long(self)
        mylong //= other
        return newint(mylong)

    def __mod__(self, other):
        return newint(super(newint, self).__mod__(other))

    def __rmod__(self, other):
        return newint(super(newint, self).__rmod__(other))

    def __divmod__(self, other):
        value = super(newint, self).__divmod__(other)
        return (newint(value[0]), newint(value[1]))

    def __rdivmod__(self, other):
        value = super(newint, self).__rdivmod__(other)
        return (newint(value[0]), newint(value[1]))

    def __pow__(self, other):
        return newint(super(newint, self).__pow__(other))

    def __rpow__(self, other):
        return newint(super(newint, self).__rpow__(other))

    def __lshift__(self, other):
        return newint(super(newint, self).__lshift__(other))

    def __rlshift__(self, other):
        return newint(super(newint, self).__lshift__(other))

    def __rshift__(self, other):
        return newint(super(newint, self).__rshift__(other))

    def __rrshift__(self, other):
        return newint(super(newint, self).__rshift__(other))

    def __and__(self, other):
        return newint(super(newint, self).__and__(other))

    def __rand__(self, other):
        return newint(super(newint, self).__rand__(other))

    def __or__(self, other):
        return newint(super(newint, self).__or__(other))

    def __ror__(self, other):
        return newint(super(newint, self).__ror__(other))

    def __xor__(self, other):
        return newint(super(newint, self).__xor__(other))

    def __rxor__(self, other):
        return newint(super(newint, self).__rxor__(other))

    # __radd__(self, other) __rsub__(self, other) __rmul__(self, other) __rdiv__(self, other) __rtruediv__(self, other) __rfloordiv__(self, other) __rmod__(self, other) __rdivmod__(self, other) __rpow__(self, other) __rlshift__(self, other) __rrshift__(self, other) __rand__(self, other) __rxor__(self, other) __ror__(self, other) 

    # __iadd__(self, other) __isub__(self, other) __imul__(self, other) __idiv__(self, other) __itruediv__(self, other) __ifloordiv__(self, other) __imod__(self, other) __ipow__(self, other, [modulo]) __ilshift__(self, other) __irshift__(self, other) __iand__(self, other) __ixor__(self, other) __ior__(self, other)

    def __neg__(self):
        return newint(super(newint, self).__neg__())
        
    def __pos__(self):
        return newint(super(newint, self).__pos__())
    
    def __abs__(self):
        return newint(super(newint, self).__abs__())
    
    def __invert__(self):
        return newint(super(newint, self).__invert__())

    def __int__(self):
        return self

    def __nonzero__(self):
        return self.__bool__()

    def __bool__(self):
        
        return super(newint, self).__nonzero__()

    def __native__(self):
        return long(self)


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


    def __long__(self):
        if not hasattr(self, '__int__'):
            return NotImplemented
        return self.__int__()  # not type(self).__int__(self)

    def __native__(self):
        
        return object(self)



if PY3:
    # We'll probably never use newstr on Py3 anyway...
    unicode = str


class BaseNewStr(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, unicode)


class newstr(with_metaclass(BaseNewStr, unicode)):
    """We only really want it to be derived from unicode - everything else we can settle ourselves.
    No expensive runtime checks, I say"""
    pass  
  

# future.builtins.iterators.py
import itertools

if not PY3:
    filter = itertools.ifilter
    map = itertools.imap
    range= newrange
    zip = itertools.izip
else:
    import builtins
    filter = builtins.filter
    map = builtins.map
    range = builtins.range
    zip = builtins.zip


if PY3:
    import builtins
    bytes = builtins.bytes
    dict = builtins.dict
    int = builtins.int
    list = builtins.list
    object = builtins.object
    range = builtins.range
    str = builtins.str
else:
    bytes = newbytes
    int = newint
    object = newobject
    str = newstr
    dict = newdict


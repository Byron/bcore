

from __future__ import absolute_import, division, print_function

import functools
from numbers import Integral

from future import utils


# Some utility functions to enforce strict type-separation of unicode str and
# bytes:
def disallow_types(argnums, disallowed_types):
    

    def decorator(function):

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            # These imports are just for this decorator, and are defined here
            # to prevent circular imports:
            from .newbytes import newbytes
            from .newint import newint
            from .newstr import newstr

            errmsg = "argument can't be {0}"
            for (argnum, mytype) in zip(argnums, disallowed_types):
                # Handle the case where the type is passed as a string like 'newbytes'.
                if isinstance(mytype, str) or isinstance(mytype, bytes):
                    mytype = locals()[mytype]

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


if utils.PY3:
    import builtins
    bytes = builtins.bytes
    dict = builtins.dict
    int = builtins.int
    list = builtins.list
    object = builtins.object
    range = builtins.range
    str = builtins.str

    # The identity mapping
    newtypes = {bytes: bytes,
                dict: dict,
                int: int,
                list: list,
                object: object,
                range: range,
                str: str}

    __all__ = ['newtypes']

else:

    from .newbytes import newbytes
    from .newdict import newdict
    from .newint import newint
    from .newlist import newlist
    from .newrange import newrange
    from .newobject import newobject
    from .newstr import newstr

    newtypes = {bytes: newbytes,
                dict: newdict,
                int: newint,
                long: newint,
                list: newlist,
                object: newobject,
                range: newrange,
                str: newbytes,
                unicode: newstr}

    __all__ = ['newbytes', 'newdict', 'newint', 'newlist', 'newrange', 'newstr', 'newtypes']


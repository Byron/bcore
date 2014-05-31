"""minimized future compilation with just the code bcore needs"""
from __future__ import division, absolute_import, print_function


###########
# UTILS ##
#########
import sys

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

if PY3:
    # We'll probably never use newstr on Py3 anyway...
    unicode = str

if PY3:
    import builtins
    str = builtins.str
else:
    str = unicode


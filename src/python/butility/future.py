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
        def __new__(cls, name, nbases, d):
            if nbases is None:
                return type.__new__(cls, name, (), d)
            # There may be clients who rely on this attribute to be set to a reasonable value, which is why 
            # we set the __metaclass__ attribute explicitly
            if PY2 and '___metaclass__' not in d:
                d['__metaclass__'] = meta
            # end 
            return meta(name, bases, d)
        # end
    # end metaclass
    return metaclass(meta.__name__ + 'Helper', None, {})
    # end handle py2

if PY3:
    # We'll probably never use newstr on Py3 anyway...
    unicode = str

if PY3:
    import builtins
    str = builtins.str
    string_types = str
else:
    str = unicode
    string_types = (str, __builtins__['str'])


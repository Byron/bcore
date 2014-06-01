#-*-coding:utf-8-*-
"""
@package butility.compat
@brief A module to encapsulate differences between python versions

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str
__all__ = ['pickle', 'StringIO']

import sys

if sys.version_info[0] < 3:
    # for Py2
    import cPickle as pickle

    if sys.version_info[1] < 7:
        # wow ! in py 2.6, cStringIO is broken and can't handle unicode - something we can easily throw at it
        # ARGH !
        from StringIO import StringIO
        PyStringIO = StringIO
    else:
        from cStringIO import StringIO
        # for unicode support 
        from StringIO import StringIO as PyStringIO
    # end string io special handling
    import cProfile as profile
else:
    # for Py3
    import pickle
    from io import StringIO
    PyStringIO = StringIO
    import profile
# end 

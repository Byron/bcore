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

try:
    # for Py2
    import cPickle as pickle

    if sys.version_info < (2,7):
        # wow ! in py 2.6, cStringIO is broken and can't handle unicode - something we can easily throw at it
        # ARGH !
        from StringIO import StringIO
    else:
        from cStringIO import StringIO
except ImportError:
    # for Py3
    import pickle
    from io import StringIO
# end 


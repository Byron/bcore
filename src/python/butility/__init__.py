#-*-coding:utf-8-*-
"""
@package butility
@brief A package with useful utilities that have no dependency to any other non-platform code

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
# Allow better imports !
from __future__ import absolute_import

def _initialize():
    """Make sure our absolute requirements are met - namely future"""
    try:
        import future
    except ImportError:
        # try to use our builtin version
        import os
        import sys
        pdir = os.path.join(os.path.dirname(__file__), 'future-builtin')
        sys.path.append(pdir)

        import future
    # end try future import
# end 

_initialize()

from .base import *
from .path import *
from .system import *
from .types import *

__version__ = Version('0.1.0')


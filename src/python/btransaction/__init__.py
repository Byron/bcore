#-*-coding:utf-8-*-
"""
@package btransaction
@brief Toplevel package for transaction implementation and operations using that framework

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
# Allow better imports !
from __future__ import absolute_import

from butility import Version
__version__ = Version("0.1.0")

from .base import *

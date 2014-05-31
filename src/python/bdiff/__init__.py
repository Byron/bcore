#-*-coding:utf-8-*-
"""
@package bdiff
@brief Package with facilities to diff any data structure

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
# Allow better imports !
from __future__ import absolute_import

from butility import Version
__version__ = Version("0.1.0")

from .base import *
from .delegates import *
from .algorithms import *
from .utility import *

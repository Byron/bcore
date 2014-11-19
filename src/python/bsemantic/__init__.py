#-*-coding:utf-8-*-
"""
@package bsemantic
@brief A package containing a flexible templating engine used to generate paths.

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""  # Allow better imports !
from __future__ import absolute_import
from __future__ import unicode_literals

from butility import Version
__version__ = Version("0.1.0")

from .base import *
from .exceptions import *
from .generators import *
from .inference import *

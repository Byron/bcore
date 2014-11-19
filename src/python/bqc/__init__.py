#-*-coding:utf-8-*-
"""
@package bqc
@brief A framework to implement quality assurance on a very basic level.

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import absolute_import

from butility import Version
__version__ = Version("0.1.0")

from .interfaces import *
from .base import *

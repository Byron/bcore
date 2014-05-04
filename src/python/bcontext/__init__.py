#-*-coding:utf-8-*-
"""
@package bcontext
@brief A framework to manage an application context, made of implementation and configuration

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import absolute_import

from butility import Version
__version__ = Version("0.1.0")

# make sure people can get the most fundamental implementation in this package
from .base import *
from .hierarchy import *
from .utility import *

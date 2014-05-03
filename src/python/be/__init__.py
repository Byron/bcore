#-*-coding:utf-8-*-
"""
@package be
@brief A configurable command framework

As opposed to bcmd, which provides foundations only, this is far more flexibly due to various
configuration options.
@note this package can be started
@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
# Allow better imports !
from __future__ import absolute_import
from .cmd import *

__version__ = BeCommand.version


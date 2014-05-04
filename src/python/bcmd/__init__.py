#-*-coding:utf-8-*-
"""
@package bcmd
@brief A package to provide an extensible framework for handling commandline tools

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import absolute_import

from butility import Version
__version__ = Version("0.1.0")

from .interfaces import *
from .base import *
from .utility import *
from .argparse import *

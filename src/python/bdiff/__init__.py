#-*-coding:utf-8-*-
"""
@package bdiff
@brief Package with facilities to diff any data structure

@page diff Diff Framework

Example Usage
#############

Please see an excerpt from the test. First, we define some tree-ish data structures
@snippet bapp/tests/core/diff/test_algorithms.py data structures


Then we perform a two-way diff on them using the pre-defined DiffIndexDelegate
@snippet bapp/tests/core/diff/test_algorithms.py two way diff

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
# Allow better imports !
from __future__ import absolute_import

from butility import Version
__version__ = Version("0.1.0")

from .base import *
from .delegates import *
from .algorithms import *
from .utility import *

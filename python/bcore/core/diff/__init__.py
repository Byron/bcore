#-*-coding:utf-8-*-
"""
@package tx.core.diff
@brief Package with facilities to diff any data structure

@page diff Diff Framework

Example Usage
#############

Please see an excerpt from the test. First, we define some tree-ish data structures
@snippet bcore/tests/core/diff/test_algorithms.py data structures


Then we perform a two-way diff on them using the pre-defined DiffIndexDelegate
@snippet bcore/tests/core/diff/test_algorithms.py two way diff

@copyright 2012 Sebastian Thiel
"""
from .base import *
from .delegates import *
from .algorithms import *
from .utility import *

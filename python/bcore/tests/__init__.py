#-*-coding:utf-8-*-
"""
@package tx.tests
Main test package for all bcore code.

Provides core functionality which will be used by all test cases in one way or another.

Imports tx.tests.core

@copyright 2012 Sebastian Thiel
"""

# Import all core features into the main package
import sys
from bcore.tests.core import *
import logging
from bcore.utility import init_ipython_terminal


def _initialize():
    """Add some utilities"""
    # be sure we can easily start ipython from an interpreter
    import __builtin__
    setattr(__builtin__, 'ipy', init_ipython_terminal)
    
    # Set debug logging for test cases
    logging.root.setLevel(logging.DEBUG)
    
#end _initialize


_initialize()
    


#-*-coding:utf-8-*-
"""
@package bapp.tests.base
@brief most fundamental types

@copyright 2012 Sebastian Thiel
"""

import logging

import bapp
from butility.tests import TestCaseBase
from butility import (Path,
                      wraps)

log = logging.getLogger('bapp.tests')


# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
## @{

def preserve_application(fun):
    """A wrapper which preserves whichever value was in bapp.Application.main during
    the test-case"""
    @wraps(fun)
    def wrapper(*args, **kwargs):
        prev = bapp.Application.main        
        try:
            return fun(*args, **kwargs)
        finally:
            bapp.Application.main = prev
        # end reset Application
    # end wrapper
    return wrapper

def with_application(fun):
    """similar to preserve_application(), but will create a new application object that will 
    be discarded once the decorated function completes.
    It's useful if there is ApplictionSettingsClient code that tries to access the central information database"""
    @wraps(fun)
    def wrapper(*args, **kwargs):
        assert bapp.Application.main is None, "Should have no application yet"
        bapp.Application.new()
        return fun(*args, **kwargs)
    # end wrapper
    return preserve_application(wrapper)        
    

## -- End Decorators -- @}


# ==============================================================================
## @name Types
# ------------------------------------------------------------------------------
## @{

class TestCoreCaseBase(TestCaseBase):
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

# end class TestCaseBase

## -- End Types -- @}






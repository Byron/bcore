#-*-coding:utf-8-*-
"""
@package bcore.tests.base
@brief most fundamental types

@copyright 2012 Sebastian Thiel
"""

import logging

import bcore
from butility.tests import TestCaseBase
from butility import (Path,
                      wraps)

log = logging.getLogger('bcore.tests')


# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
## @{

def preserve_application(fun):
    """A wrapper which preserves whichever value was in bcore.Application.main during
    the test-case"""
    @wraps(fun)
    def wrapper(*args, **kwargs):
        prev = bcore.Application.main        
        try:
            return fun(*args, **kwargs)
        finally:
            bcore.Application.main = prev
        # end reset Application
    # end wrapper
    return wrapper

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






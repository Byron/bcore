#-*-coding:utf-8-*-
"""
@package bcore.tests.processing.tractor.base
@brief Base classes and utilities for tractor tests

@copyright 2013 Sebastian Thiel
"""
__all__ = ['TractorTestCaseBase']


from bcore.tests import TestCaseBase



# ==============================================================================
## @name Classes
# ------------------------------------------------------------------------------
## @{

class TractorTestCaseBase(TestCaseBase):
    """A test case with some maya utilities"""
    __slots__ = ()

    ## Subdirectory to the ./fixtures root
    fixture_subdir = 'processing/tractor'

# end class TractorTestCaseBase

## -- End Classes -- @}




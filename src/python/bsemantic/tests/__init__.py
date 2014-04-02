#-*-coding:utf-8-*-
"""
@package bsemantic.tests
@brief tests for bsemantic

@copyright 2012 Sebastian Thiel
"""
__all__ = []

from nose import SkipTest

try:
    import parse
except ImportError:
    raise SkipTest("If we are launched without the wrapper, tests can't work as dependencies are not met")
# end handle dependencies

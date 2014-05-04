#-*-coding:utf-8-*-
"""
@package be.tests.base
@brief utilities for use in be test suite

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['BeTestCase']

from butility.tests import TestCaseBase
from butility import Path


class BeTestCase(TestCaseBase):
    """Base for all be test cases"""
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

# end class BeTestCase

